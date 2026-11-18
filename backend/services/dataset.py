import json
import re

from core.database import get_db_connection
from core.config import get_dataset_path
from typing import Any, List
from fastapi import HTTPException
from models.payload import Filter, Payload


def is_empty(v) -> bool:
    if v is None:
        return True

    if isinstance(v, list) and len(v) == 0:
        return True
    return False


def fetch_config(dataset_id):
    """
    Generates a dataset config payload based on a provided dataset
    """
    # find dataset by id
    db_path = get_dataset_path(dataset_id)

    if db_path is None:
        return "Todo DB path error"

    conn = get_db_connection(db_path)

    result = conn.sql("SELECT json_config FROM dataset_config")

    payload = json.loads(result.fetchone()[0])

    for grp in payload["filter_groups"]:
        for x in range(len(grp["filters"])):
            grp["filters"][x] = {
                k: v for k, v in grp["filters"][x].items() if not is_empty(v)
            }

    return payload


def generate_records_query(
    cols: list[int],
    page: int = 1,
    page_size: int = 100,
    sort_by: int | None = None,
    asc: bool = True,
    *,
    filter_ctes: str
):
    quote = "'{}'"

    if len(cols):
        col_str = f"[{','.join(quote.format(c) for c in cols)}]"
        column_call = f"column_mapper({col_str})"
    else:
        column_call = "default_columns()"

    sort_var = ""
    sort_stmt = "ORDER BY __internal_row_id"
    if sort_by:
        sort_var = f"SET VARIABLE sort_by = list_first(column_mapper([{sort_by}]));"
        sort_stmt = f"ORDER BY COLUMNS(getvariable('sort_by')) {'ASC' if asc else 'DESC'} NULLS LAST, __internal_row_id"

    page = max(page, 1)
    page_size = max(page_size, 1)
    offset = (page - 1) * page_size

    cte_prefix = f"{filter_ctes},\n" if filter_ctes else ""

    sql = f"""
    SET VARIABLE selected_cols = {column_call};
    {sort_var}

    WITH {cte_prefix}
    matched_rows AS (
        SELECT __internal_row_id
        FROM query_table(?)
    )
    SELECT {{
        "columns": ARRAY(
            SELECT details
            FROM column_details
            WHERE name IN getvariable('selected_cols')
        ),
        "rows": ARRAY(
            SELECT struct_pack(*COLUMNS(getvariable('selected_cols')))
            FROM dataset_view
            WHERE __internal_row_id IN (
                SELECT __internal_row_id
                FROM matched_rows
            )
            {sort_stmt}
            LIMIT {page_size}
            OFFSET {offset}
        ),
        "meta": {{
            'total_hits': (
                SELECT COUNT(*) FROM matched_rows
            ),
            'page': {page},
            'per_page': {page_size}
        }}
    }}::JSON;
    """

    return sql


def validate_dataset_filters(conn, filters: List[Filter]) -> dict[str, dict[str, Any]]:
    """Resolve metadata once and validate request values against ETL-checked definitions."""
    if not filters:
        return {}

    rows = conn.execute(
        "SELECT id, filter_type, target_column, regex, extras FROM filter WHERE id IN ?",
        [[f.filter_id for f in filters]],
    ).fetchall()
    definitions = {
        filter_id: {"type": filter_type, "target_column": target_column,
                    "regex": pattern, "extras": extras}
        for filter_id, filter_type, target_column, pattern, extras in rows
    }
    for f in filters:
        definition = definitions.get(f.filter_id)
        if definition is None:
            raise HTTPException(status_code=422, detail=f"Unknown filter_id: {f.filter_id}")

        filter_type = definition["type"]
        if filter_type in ("fixed_list", "user_list"):
            if not isinstance(f.filter_value, list):
                raise HTTPException(status_code=422, detail=f"Filter '{f.filter_id}' requires a list of values")
        elif filter_type in ("match", "prefix", "regex"):
            if not isinstance(f.filter_value, str):
                raise HTTPException(status_code=422, detail=f"Filter '{f.filter_id}' requires a single string value")
            if filter_type == "regex":
                definition["arguments"] = get_regex_filter_arguments(f, definition)
        else:
            raise HTTPException(status_code=422, detail=f"Filter '{f.filter_id}' has unsupported type '{filter_type}'")
    return definitions


def generate_filter_ctes(source_table: str, filters: List[Filter], definitions: dict[str, dict[str, Any]]) -> tuple[str, List[object], str]:
    """
    Generate Common Table Expressions (CTEs) for the given filters.

    Args:
        source_table (str): The name of the source table to filter.
        filters (List[Filter]): A list of Filter objects to apply.
        definitions (dict[str, dict[str, Any]]): A dictionary containing filter definitions.

    Returns:
        tuple[str, List[object], str]: A tuple containing the CTE string, the list of parameters, and the name of the final table.
    """
    ctes = []
    parameters: List[object] = []
    previous_table = source_table

    for index, f in enumerate(filters, start=1):
        definition = definitions[f.filter_id]
        filter_type = definition["type"]
        target_column = definition["target_column"]

        if filter_type in ("fixed_list", "user_list"):
            macro = "select_list_filter"
            arguments = [
                previous_table,
                [target_column],
                f.filter_value,
            ]
        elif filter_type == "match":
            macro = "select_exact_filter"
            arguments = [
                previous_table,
                [target_column],
                f.filter_value,
            ]
        elif filter_type == "prefix":
            macro = "select_prefix_filter"
            arguments = [
                previous_table,
                [target_column],
                f.filter_value,
            ]
        elif filter_type == "regex":
            macro_name = f"regex_{f.filter_id}_filter"
            macro = '"' + macro_name.replace('"', '""') + '"'
            arguments = [
                previous_table,
                *definition["arguments"],
            ]
        else:
            raise HTTPException(status_code=422, detail=f"Filtering with type '{filter_type}' is not supported yet")

        placeholders = ", ".join("?" for _ in arguments)
        cte_name = f"filtered_step_{index}"
        ctes.append(f"{cte_name} AS (SELECT * FROM {macro} ({placeholders}))")

        parameters.extend(arguments)
        previous_table = cte_name

    return ",\n".join(ctes), parameters, previous_table


def get_regex_filter_arguments(f: Filter, definition: dict[str, Any]) -> List[object]:
    """Parse user input once; regex syntax and field configuration are checked by ETL."""
    fields = json.loads(definition["extras"])["fields"]
    match = re.fullmatch(definition["regex"], f.filter_value)
    if match is None:
        raise HTTPException(status_code=422, detail=f"Filter '{f.filter_id}' does not match the required format")

    arguments: List[object] = []
    parsed_values: dict[str, str | int] = {}

    for field in fields:
        # Extract the value for the current field from the regex match
        value = match.group(field["regex_name"])
        if value is None:
            raise HTTPException(status_code=422, detail=f"Missing value for '{field['regex_name']}' in filter '{f.filter_id}'")

        # Convert the value to an integer if the match operator is not '='
        if field["match"] != "=":
            try:
                value = int(value)
            except ValueError:
                raise HTTPException(status_code=422, detail=f"'{field['regex_name']}' must be an integer")

            if not -(2**31) <= value <= 2**31 - 1:
                raise HTTPException(status_code=422, detail=f"'{field['regex_name']}' exceeds the supported integer range")

        parsed_values[field["regex_name"]] = value
        arguments.append(value)

    # Validate start and end range if both are present
    start = parsed_values.get("start")
    end = parsed_values.get("end")
    if isinstance(start, int) and isinstance(end, int):
        if start > end:
            raise HTTPException(status_code=422, detail=f"Filter '{f.filter_id}' requires start to be less than or equal to end")

    return arguments


def records(dataset_id: str, payload: Payload | None = None):
    # Get dataset
    db_path = get_dataset_path(dataset_id)

    if db_path is None:
        return "Todo DB path error"

    conn = get_db_connection(db_path)

    # TODO
    # - Add input model --
    #   - WIP
    # - Convert column ids into column names - done
    #   - SELECT column_mapper([1,3,10]) - done
    #   - Get default uses default_columns - done
    # - Build up where filter list ---
    # - Add pagination - done
    # - Sorting - done

    try:
        filters = (payload.filters or []) if payload else []
        filter_definitions = validate_dataset_filters(conn, filters)

        source_row = conn.execute("SELECT source FROM dataset").fetchone()
        if source_row is None:
            raise RuntimeError("Dataset source metadata is missing")
        source_table = source_row[0]

        filter_ctes, parameters, final_table = generate_filter_ctes(source_table, filters, filter_definitions)

        cols = []
        page = 1
        page_size = 100
        order_by = None
        asc = True

        if payload:
            cols = payload.columns or []
            page = payload.page if payload.page is not None else 1
            page_size = payload.per_page if payload.per_page is not None else 100

            if payload.order_by:
                order_by = payload.order_by.column_id
                asc = payload.order_by.order == "ASC"

        sql = generate_records_query(
            cols, page, page_size, order_by, asc,
            filter_ctes=filter_ctes
        )
        result = conn.execute(
            sql,
            [*parameters, final_table]
        )
        response = json.loads(result.fetchone()[0])
        return response
    finally:
        conn.close()

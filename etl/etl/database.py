import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Self

import duckdb

from etl.models import (
    DatasetInfo,
    Column,
    Filter,
    FilterGroup,
    RegexExtras,
    FIXED_LIST_FILTER_TYPE,
)

logger = logging.getLogger(__name__)

schema_version = "v2"

REGEX_MACRO_TEMPLATE = """
CREATE OR REPLACE MACRO regex_{}_filter(table_name, {}) AS TABLE(
    SELECT *
    FROM query_table(table_name)
    WHERE {}
)
"""

MACRO_COLUMN_MAP_TEMPLATE = """
create macro column_map(id) AS
  CASE id
    {}
  END;

CREATE MACRO column_mapper(ids) AS
(SELECT list_transform(ids, lambda c : column_map(c)));
"""

MACRO_COLUMN_MAP_ELEMENT = "WHEN {} THEN '{}'"

MACRO_DEFAULT_COLUMNS = """
CREATE MACRO default_columns() AS [{}];
"""

VIEW_COLUMN_LINK_COL = """
ALTER TABLE column_link
ADD {} struct(label VARCHAR, type VARCHAR, sortable BOOL, url VARCHAR, delimiter VARCHAR);
"""

VIEW_DATASET = """
CREATE OR REPLACE VIEW dataset_view AS
SELECT
{{"style":struct_extract(COLUMNS(*),'style') , 'value':struct_extract(COLUMNS(*),'value')}}
FROM dataset_{};
"""


def _process_value(val: str, type: str, url: str | None, delimiter: str | None):
    # Literal["link", "array-link", "labelled-link", "string"]

    if not url:
        url = "{}"

    match type:
        case "string":
            return f'"{val}"'
        case "link":
            return {"label": val, "url": url.format(val)}
        case "array-link":
            return {
                "values": [
                    {"label": v, "url": url.format(v)} for v in val.split(delimiter)
                ]
            }
        case "labelled-link":
            if "|" in val:
                bits = val.split("|")
                return {"label": bits[0], "url": url.format(bits[1])}
            return f'"{val}"'
        case _:
            f'"{val}"'


class BaseDatabase:
    def __init__(self, release_path: Path, release: str) -> None:
        self.release_path = release_path
        self.release = release
        self.conn: duckdb.DuckDBPyConnection

    def __enter__(self) -> Self:
        path = self.release_path / f"{self.release}.duckdb"
        self.conn = duckdb.connect(str(path))
        return self

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()


class DatabaseConfig(BaseDatabase):
    def __init__(
        self,
        release_path: Path,
        release: str,
        dataset: DatasetInfo,
        columns: list[Column],
        filters: list[Filter],
        filter_groups: list[FilterGroup],
        schema_version: str = schema_version,
    ):
        BaseDatabase.__init__(self, release_path, release)
        self.dataset = dataset
        self.columns = columns
        self.filters = filters
        self.filter_groups = filter_groups
        self.schema_version = schema_version
        self.ids: dict[str, int] = {}

    def create_dataset(self, view: DatasetInfo) -> None:
        """
        Method that creates a dataset version of the data table.
        The dataset version switches out a varchar value for a struct that includes
        the column type, a raw version of the value, and a processed version that includes
        everything needed to display the value on the client (see _process_value for details)
        """
        conn = self.conn
        # get dataset table
        # select visible columns
        # get column details
        cols = [c for c in self.columns if not c.hidden]
        col_lookup = {c.name: c for c in cols}
        col_names = [c.name for c in cols]
        col_args = ", ".join(["?" for x in range(len(col_names))])
        col_structs = [
            f"{n} STRUCT(style VARCHAR, raw VARCHAR, value JSON)" for n in col_names
        ]
        # create table
        create_table = f"CREATE TABLE dataset_{view.source} ({', '.join(col_structs)});"
        conn.execute(create_table)

        # insert statement
        insert_data = f"INSERT INTO dataset_{view.source} ({', '.join(col_names)}) VALUES({col_args})"

        # get values to insert
        select_data = f"SELECT {', '.join(col_names)} FROM {view.source}"
        query = conn.sql(select_data)
        rows = query.fetchall()
        for r in rows:
            row_args = [
                {
                    "style": col_lookup[col_names[x]].type,
                    "raw": r[x],
                    "value": _process_value(
                        r[x],
                        col_lookup[col_names[x]].type,
                        col_lookup[col_names[x]].url,
                        col_lookup[col_names[x]].delimiter,
                    ),
                }
                for x in range(len(col_names))
            ]

            # insert value
            conn.execute(insert_data, row_args)

        # create view
        print(VIEW_DATASET.format(view.source))
        conn.execute(VIEW_DATASET.format(view.source))

    def run(self) -> None:
        self.load_schema()

        logging.info(f"Processing {self.dataset.name}, filters and columns")
        self.write_dataset()
        logging.info("Finished")
        self.generate_release()

    def write_regex_macro(self, filter_id: str, extras: RegexExtras) -> bool:
        conn = self.conn
        inputs: list[str] = []
        matches: list[str] = []

        for field in extras.fields:
            modifier = ""
            if field.match != "=":  # force column to be a int when comparing size
                modifier = "::int"

            inputs.append(f"in_{field.regex_name}")
            matches.append(
                f"{field.column}{modifier} {field.match} in_{field.regex_name}"
            )

        macro = REGEX_MACRO_TEMPLATE.format(
            filter_id, ",".join(inputs), " AND ".join(matches)
        )
        print("Creating REGEX macro -------------------")
        print(macro)
        print("------------------------------")
        conn.execute(macro)

        return True

    def write_dataset(self) -> None:
        conn = self.conn

        # Define the view with source instead of dataset_id
        conn.execute(
            "INSERT INTO dataset (id, name, url_name, source) VALUES (?,?,?,?)",  # noqa: E501
            (
                self.dataset.id,
                self.dataset.name,
                self.dataset.url_name,
                self.dataset.source,
            ),
        )

        # Write filter groups and their filters
        # After view processing, view.filters is a list[ViewFilterGroup]
        for group in self.filter_groups:
            assert isinstance(group, FilterGroup)
            group_db_id = self.next_id("filter_group")
            group_sql = "INSERT INTO filter_group (filter_group_id, id, label, rank) VALUES (?,?,?,?)"  # noqa: E501
            conn.execute(
                group_sql,
                (
                    group_db_id,
                    group.group_id,
                    group.group_label,
                    group.rank,
                ),
            )

            selected_filters = [f.id for f in group.filters]

            for f in list(filter(lambda f: f.id in selected_filters, self.filters)):
                filter_db_id = self.next_id("filter")
                filter_sql = "INSERT INTO filter (filter_id, filter_group_id, id, label, title, example, filter_type, rank, min, max, extras, regex) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"  # noqa: E501
                # Generate a unique DB id by prefixing with the view id
                db_filter_id = f"{f.id}"

                extras = f.extras
                if f.type == "regex" and f.extras:
                    e: RegexExtras = f.extras
                    self.write_regex_macro(db_filter_id, e)

                if extras:
                    extras_dump = extras.model_dump(exclude_none=True)
                else:
                    extras_dump = "{}"

                filter_params = (
                    filter_db_id,
                    group_db_id,
                    db_filter_id,
                    f.label,
                    f.title,
                    f.example,
                    f.type,
                    f.rank,
                    f.min,
                    f.max,
                    extras_dump,
                    f.regex,
                )
                conn.execute(filter_sql, filter_params)
                if f.type == FIXED_LIST_FILTER_TYPE and f.filter_values is not None:
                    for value in f.filter_values:
                        value_sql = "INSERT INTO filter_value (filter_id, value, label) VALUES (?,?,?)"  # noqa: E501
                        value_params = (
                            filter_db_id,
                            value["value"],
                            value["label"],
                        )
                        conn.execute(value_sql, value_params)

        # Write merged columns (column metadata + view association)
        col_index = 0
        col_mapping = []
        default_columns = []
        for column in self.columns:
            col_db_id = self.next_id("column_info")
            col_sql = "INSERT INTO column_info (column_id, name, label, type, sortable, url, delimiter, hidden, rank, enable_by_default) VALUES (?,?,?,?,?,?,?,?,?,?)"  # noqa: E501
            col_params = (
                col_db_id,
                column.name,
                column.label,
                column.type,
                column.sortable,
                column.url,
                column.delimiter,
                column.hidden,
                column.rank,
                column.enabled,
            )
            col_mapping.append(MACRO_COLUMN_MAP_ELEMENT.format(col_db_id, column.name))
            if column.enabled and not column.hidden:
                default_columns.append(f"'{column.name}'")
            col_index += 1
            conn.execute(col_sql, col_params)

        ## create column map macro
        print(MACRO_COLUMN_MAP_TEMPLATE.format("\n".join(col_mapping)))
        conn.execute(MACRO_COLUMN_MAP_TEMPLATE.format("\n".join(col_mapping)))

        ## create default column macro
        print(MACRO_DEFAULT_COLUMNS.format(",".join(default_columns)))
        conn.execute(MACRO_DEFAULT_COLUMNS.format(",".join(default_columns)))

        self.create_dataset(self.dataset)

    def generate_release(self) -> None:
        sql = "INSERT INTO release (release_label, schema_version) VALUES (strftime(current_date(),'%Y-%m'), ?)"  # noqa: E501
        self.conn.execute(sql, (self.schema_version,))

    def load_schema(self) -> None:
        conn = self.conn
        path = (
            Path(__file__).parent.parent / "sql" / f"schema.{self.schema_version}.sql"
        )
        with open(path, "rt") as fh:
            content = fh.read()
            conn.execute(content)
        logging.info(f"Database schema loaded from {path!r}")

    def get_files(self, prefix: str) -> list[str]:
        """Take a prefix, find all files in the release_path directory
        and load JSON content for further processing"""
        loaded = []
        for file in self.release_path.iterdir():
            if (
                file.is_file()
                and file.name.startswith(f"{prefix}-")
                and file.name.endswith(".json")
            ):
                with open(file, "rt") as fh:
                    content = fh.read()
                    loaded.append(content)
        return loaded

    def next_id(self, table: str) -> int:
        current_id = self.ids.get(table, 1)
        self.ids[table] = current_id + 1
        return current_id


class Database(BaseDatabase):
    """Copies the parquet files present in the release directory into the DuckDB
    database. Looks for all .parquet files in the release_path and creates a table
    for each file named after the file stem.
    """

    def run(self) -> None:
        for path in self.get_parquet_paths():
            self.load_parquet(path)

    def load_parquet(self, path: Path) -> None:
        table_name = path.stem
        logging.info(f"Loading parquet {path!r} into table {table_name!r}")
        self.conn.execute(
            f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{path}')"
        )

    def get_parquet_paths(self) -> Iterator[Path]:
        for file in self.release_path.iterdir():
            if file.is_file() and file.name.endswith(".parquet"):
                yield file

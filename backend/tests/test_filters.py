"""Focused regression coverage for the supported backend filters."""

import json
import re
from pathlib import Path

import duckdb
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from models.payload import Filter, Payload
from services import dataset as dataset_service

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def conn(monkeypatch):
    monkeypatch.syspath_prepend(str(PROJECT_ROOT / "etl"))
    from etl.database import (
        DatabaseConfig,
        MACRO_COLUMN_MAP_TEMPLATE,
        MACRO_DEFAULT_COLUMNS,
    )
    from etl.models import RegexExtras

    connection = duckdb.connect()
    try:
        connection.execute("""
            CREATE TABLE filter (
                filter_id INTEGER, id VARCHAR, filter_type VARCHAR,
                target_column VARCHAR, regex VARCHAR, extras VARCHAR
            );
            INSERT INTO filter (filter_id, id, filter_type, target_column) VALUES
                (1, 'gene_type', 'fixed_list', 'so_term'),
                (2, 'gene_symbol', 'match', 'symbol'),
                (3, 'symbol_prefix', 'prefix', 'symbol'),
                (4, 'symbols', 'user_list', 'symbol'),
                (5, 'genome', 'fixed_list', 'genome_uuid');
            CREATE TABLE filter_value (filter_id INTEGER, value VARCHAR);
            INSERT INTO filter_value VALUES
                (1, 'protein_coding'), (1, 'lncRNA'),
                (5, 'g1'), (5, 'g2'), (5, 'g3');

            CREATE TABLE genes (
                __internal_row_id INTEGER, symbol VARCHAR, so_term VARCHAR,
                genome_uuid VARCHAR, slice_region_name VARCHAR,
                slice_location_start VARCHAR, slice_location_end VARCHAR
            );
            INSERT INTO genes VALUES
                (1, 'BRCA1', 'protein_coding', 'g1', '1', '100', '200'),
                (2, 'BRCA2', 'protein_coding', 'g1', '1', '300', '400'),
                (3, 'BRCA1', 'lncRNA',         'g2', '1', '100', '200'),
                (4, 'OTHER', 'pseudogene',     'g2', 'X', '100', '200'),
                (5, NULL,   'protein_coding', 'g3', '1', '100', '200');

            CREATE TABLE dataset (source VARCHAR);
            INSERT INTO dataset VALUES ('genes');
            CREATE VIEW dataset_view AS
            SELECT __internal_row_id, symbol,
                   {'style': 'string', 'value': so_term} AS so_term,
                   __internal_row_id AS row_id
            FROM genes;
            CREATE VIEW column_details AS
            SELECT name, {'id': id, 'name': name} AS details
            FROM (VALUES (1, 'symbol'), (2, 'so_term'), (3, 'row_id'))
                AS columns(id, name);
        """)

        # Use production macros, including ETL-generated location/column macros.
        schema = (PROJECT_ROOT / "etl/sql/schema.v2.sql").read_text()
        for name in ("select_list_filter", "select_exact_filter", "select_prefix_filter"):
            statement = re.search(
                rf"CREATE (?:OR REPLACE )?MACRO {name}\b.*?;", schema, re.DOTALL
            )
            assert statement is not None, f"Missing macro: {name}"
            connection.execute(statement.group())

        config = json.loads(
            (PROJECT_ROOT / "datasets/genes/config/config.json").read_text()
        )
        location = next(f for f in config["filters"] if f["id"] == "location")
        connection.execute(
            "INSERT INTO filter VALUES (6, ?, ?, ?, ?, ?)",
            [location["id"], location["type"], location["target_column"],
             location["regex"], json.dumps(location["extras"])],
        )
        writer = DatabaseConfig.__new__(DatabaseConfig)
        writer.conn = connection
        writer.write_regex_macro(
            "location", RegexExtras.model_validate(location["extras"])
        )
        connection.execute(MACRO_COLUMN_MAP_TEMPLATE.format(
            "WHEN 1 THEN 'symbol' WHEN 2 THEN 'so_term' WHEN 3 THEN 'row_id'"
        ))
        connection.execute(MACRO_DEFAULT_COLUMNS.format("'symbol', 'so_term'"))
        yield connection
    finally:
        connection.close()


@pytest.fixture
def fetch_records(conn, monkeypatch):
    """Run the real service with a fresh connection to the shared test database."""
    monkeypatch.setattr(dataset_service, "get_dataset_path", lambda _: "test")

    def fetch(specs=(), **options):
        options.setdefault("columns", [3])
        payload = Payload(
            filters=[Filter(filter_id=key, filter_value=value) for key, value in specs],
            **options,
        )
        request_conn = conn.cursor()
        monkeypatch.setattr(
            dataset_service, "get_db_connection", lambda _: request_conn
        )
        try:
            return dataset_service.records("genes", payload)
        finally:
            # Every request must release its connection, including failed ones.
            with pytest.raises(duckdb.ConnectionException):
                request_conn.execute("SELECT 1")

    return fetch


@pytest.mark.parametrize(
    "spec,expected",
    [
        (("gene_symbol", "BRCA1"), [1, 3]),
        (("gene_type", ["protein_coding", "lncRNA"]), [1, 2, 3, 5]),
        (("symbols", ["BRCA1", "BRCA1", "BRCA2", "absent"]), [1, 2, 3]),
        (("symbol_prefix", "BR"), [1, 2, 3]),
        # Inclusive overlap at both ends; the X-region row must not match.
        (("location", "1:200-300"), [1, 2, 3, 5]),
    ],
    ids=["match", "fixed-list-or", "user-list", "prefix", "location-overlap"],
)
def test_supported_filter_types(fetch_records, spec, expected):
    result = fetch_records([spec])
    assert result["rows"] == [{"row_id": row_id} for row_id in expected]
    assert result["meta"]["total_hits"] == len(expected)


def test_prefix_treats_wildcards_literally(conn, fetch_records):
    conn.executemany(
        "INSERT INTO genes (__internal_row_id, symbol) VALUES (?, ?)",
        [(6, "BR_%literal"), (7, "BRAXliteral")],
    )
    assert fetch_records([("symbol_prefix", "BR_%")])["rows"] == [{"row_id": 6}]


@pytest.mark.parametrize("value", ["BRCA", "brca1", "' OR TRUE --"])
def test_match_is_exact_case_sensitive_and_parameterised(fetch_records, value):
    result = fetch_records([("gene_symbol", value)])
    assert result["rows"] == []
    assert result["meta"]["total_hits"] == 0


def test_combined_filters_use_and_regardless_of_order(fetch_records):
    specs = [
        ("symbols", ["BRCA1", "BRCA2"]), ("symbol_prefix", "BR"),
        ("gene_symbol", "BRCA1"), ("gene_type", ["protein_coding"]),
        ("genome", ["g1", "g2"]), ("location", "1:100-200"),
    ]
    result = fetch_records(specs)
    assert result["rows"] == [{"row_id": 1}]
    assert result["meta"]["total_hits"] == 1
    assert fetch_records(specs[::-1]) == result


def test_removing_filters_restores_matches_across_genomes(fetch_records):
    assert fetch_records([
        ("genome", ["g2"]), ("gene_symbol", "BRCA1")
    ])["rows"] == [{"row_id": 3}]
    assert fetch_records([("gene_symbol", "BRCA1")])["rows"] == [
        {"row_id": 1}, {"row_id": 3}
    ]
    unfiltered = fetch_records()
    assert unfiltered["rows"] == [{"row_id": i} for i in range(1, 6)]
    assert unfiltered["meta"]["total_hits"] == 5


@pytest.mark.parametrize(
    "spec",
    [
        ("unknown_filter", "BRCA1"),
        ("gene_type", "protein_coding"),
        ("gene_symbol", ["BRCA1"]),
        ("genome", ["protein_coding"]),
        ("location", "1:100-200junk"),
        ("location", "1:200-100"),
        ("location", "1:1-2147483648"),
    ],
    ids=["unknown-id", "list-required", "string-required", "invalid-option",
         "location-format", "reversed-location", "coordinate-overflow"],
)
def test_invalid_filters_return_422(fetch_records, spec):
    with pytest.raises(HTTPException) as error:
        fetch_records([spec])
    assert error.value.status_code == 422


@pytest.mark.parametrize("value", [" ", [], ["BRCA1", ""]])
def test_blank_or_empty_values_are_rejected(value):
    with pytest.raises(ValidationError):
        Filter(filter_id="gene_symbol", filter_value=value)


def test_duplicate_filter_ids_are_rejected():
    with pytest.raises(ValidationError, match="Duplicate filter_id"):
        Payload(filters=[
            Filter(filter_id="gene_symbol", filter_value="BRCA1"),
            Filter(filter_id="gene_symbol", filter_value="BRCA2"),
        ])


@pytest.mark.parametrize(
    "page,expected",
    [(1, [1, 2]), (2, [5]), (3, [])],
)
def test_pagination_keeps_full_filtered_count(fetch_records, page, expected):
    result = fetch_records(
        [("gene_type", ["protein_coding"])], page=page, per_page=2
    )
    assert result["rows"] == [{"row_id": i} for i in expected]
    assert result["meta"] == {"total_hits": 3, "page": page, "per_page": 2}


@pytest.mark.parametrize(
    "order,expected",
    [("ASC", [1, 3, 2, 4, 5]), ("DESC", [4, 2, 1, 3, 5])],
)
def test_sorting_uses_row_id_for_ties_and_puts_nulls_last(fetch_records, order, expected):
    # Sort on symbol while returning only row_id.
    result = fetch_records(order_by={"column_id": 1, "order": order})
    assert result["rows"] == [{"row_id": i} for i in expected]


@pytest.mark.parametrize("columns", [[2], []], ids=["selected", "defaults"])
def test_column_selection_preserves_display_cells(fetch_records, columns):
    result = fetch_records(
        [("genome", ["g2"]), ("gene_symbol", "BRCA1")], columns=columns
    )
    expected = {"so_term": {"style": "string", "value": "lncRNA"}}
    if not columns:
        expected["symbol"] = "BRCA1"
    assert result["rows"] == [expected]
    assert {column["name"] for column in result["columns"]} == set(expected)
    assert result["meta"]["total_hits"] == 1


def test_invalid_regex_configuration_is_a_server_error(conn, fetch_records):
    conn.execute("UPDATE filter SET regex = '[' WHERE id = 'location'")
    with pytest.raises(RuntimeError, match="Invalid regex pattern"):
        fetch_records([("location", "1:100-200")])


def test_query_failure_still_closes_connection(conn, fetch_records):
    conn.execute("DROP VIEW dataset_view")
    with pytest.raises(duckdb.Error):
        fetch_records()
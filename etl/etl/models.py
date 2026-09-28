"""Pydantic models for config.json and data.json, aligned with schema v2."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Union, Any

from pydantic import BaseModel, model_validator

# ── Filter models ──

SUPPORTED_FILTERS = Literal[
    "fixed_list", "match", "prefix", "user_list", "range", "regex"
]

FIXED_LIST_FILTER_TYPE = "fixed_list"

SUPPORTED_COLUMNS = Literal["link", "array-link", "labelled-link", "string"]


class RegexField(BaseModel):
    column: str
    regex_name: str
    match: Literal[">", "<", ">=", "<=", "="]


class RegexExtras(BaseModel):
    fields: list[RegexField]


# ── View models ──


class Filter(BaseModel):
    id: str
    target_column: str
    label: str | None = None
    title: str
    example: str | None = None
    type: SUPPORTED_FILTERS | None = None
    min: float | None = None
    max: float | None = None
    rank: int | None = None
    filter_values: list[dict[str, str]] | None = None
    extras: RegexExtras | None = None
    regex: str | None = None


class FilterGroup(BaseModel):
    group_id: str
    group_label: str
    rank: int | None = None
    filters: list[Filter]


class Column(BaseModel):
    name: str
    enabled: bool = True
    rank: int | None = None
    # Populated during processing from dataset introspection + config overrides
    label: str | None = None
    sortable: bool = True
    hidden: bool = False
    type: SUPPORTED_COLUMNS = "string"
    url: str | None = None
    delimiter: str | None = None


class DatasetInfo(BaseModel):
    url_name: str
    id: str
    name: str
    source: str
    include_remaining_columns: bool = False
    filter_groups: list[FilterGroup]
    columns: list[Column]


# ── Top-level config ──


class Config(BaseModel):
    filters: list[Filter]
    dataset: DatasetInfo
    columns: dict[str, dict[str, Column]] = {}  # keyed by view id


def validate_config(config_data: dict[str, Any]) -> bool:
    Config.model_validate(config_data)

    # check required fields for filters
    # - regex - regex has groups. group names match extras
    # - range has min max
    #

    return True


# ── Dataset models (data.json) ──


class CreateColumn(BaseModel):
    name: str
    command: str


class DataSource(BaseModel):
    name: str
    path: str
    parquet_path: str | Path | None = None
    filter: str | None = None
    filter_column: str | None = None
    create_columns: list[CreateColumn] = []
    column_metadata_path: str | Path | None = None
    columns: list[Column] | None = None

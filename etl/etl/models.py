"""Pydantic models for config.json and data.json, aligned with schema v2."""

from __future__ import annotations

import re
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


class FilterId(BaseModel):
    id: str


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

    @model_validator(mode="after")
    def validate_definition(self):
        if not self.id.strip() or not self.target_column.strip():
            raise ValueError("Filter ID and target_column must not be blank")
        if self.type is None:
            raise ValueError(f"Filter '{self.id}' requires a type")
        if self.type == "regex":
            if not self.regex or not self.extras or not self.extras.fields:
                raise ValueError(f"Filter '{self.id}' requires a regex and nonempty extras.fields")
            try:
                pattern = re.compile(self.regex)
            except re.error as exc:
                raise ValueError(f"Invalid regex pattern for filter '{self.id}': {exc}") from exc
            names = [field.regex_name for field in self.extras.fields]
            if len(names) != len(set(names)) or set(names) != set(pattern.groupindex):
                raise ValueError(f"Filter '{self.id}' fields must match its named regex groups exactly")
            if any(not field.column.strip() for field in self.extras.fields):
                raise ValueError(f"Filter '{self.id}' regex columns must not be blank")
        elif self.extras is not None or self.regex is not None:
            raise ValueError(f"Filter '{self.id}' only supports regex/extras with type regex")
        return self


class FilterGroup(BaseModel):
    group_id: str
    group_label: str
    rank: int | None = None
    filters: list[FilterId]


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


# ── Top-level config ──


class Config(BaseModel):
    filters: list[Filter]
    filter_groups: list[FilterGroup]
    info: DatasetInfo
    columns: list[Column]


def validate_config(config_data: dict[str, Any]) -> bool:
    print("-----------------------------------")
    print(config_data)
    print("-----------------------------------")
    config = Config.model_validate(config_data)
    filter_names = [f.id for f in config.filters]
    if len(filter_names) != len(set(filter_names)):
        raise ValueError("Filter IDs must be unique")

    for g in config.filter_groups:
        for gf in g.filters:
            if gf.id not in filter_names:
                raise ValueError(
                    f"Unknown filter {gf.id} found in filter group {g.group_id}"
                )

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

"""Pydantic models for config.json and data.json, aligned with schema v2."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Union

from pydantic import BaseModel, model_validator

# ── Filter models ──

class RegexField(BaseModel):
    column: str
    regex_capture_group: str
    match: Literal[">", "<", ">=", "<=", "="]

class RegexQueryConfig(BaseModel):
    fields: list[RegexField]

class Filter(BaseModel):
    id: str
    target_column: str
    label: str
    label: str | None = None
    title: str
    type: Literal[
        "select_list", "select", "select_in", "list_contains", "range", "regex"
    ]
    match: Literal["exact", "prefix"] | None = None
    filter_labels: str | None = None
    min: float | None = None
    max: float | None = None
    config: RegexQueryConfig | None = None
    regex: str | None = None
    


# ── View models ──


class ViewFilter(BaseModel):
    filter_id: str

    # Attributes we copy across from the Filter object definition above
    # which is why we're not very tight on the defs
    label: str | None = None
    title: str
    example: str | None = None
    type: (
        Literal[
            "select_list", "select", "select_in", "list_contains", "range", "location"
        ]
        | None
    ) = None
    match: Literal["exact", "prefix"] | None = None
    min: float | None = None
    max: float | None = None
    rank: int | None = None
    filter_values: list[dict[str, str]] | None = None
    config:  RegexQueryConfig | None = None
    regex: str | None = None

    def copy_from_filter(self, filter: Filter) -> None:
        for key, value in filter.model_dump(exclude_none=True).items():
            if hasattr(self, key):
                setattr(self, key, value)


class ViewFilterGroup(BaseModel):
    group_id: str
    group_label: str
    rank: int | None = None
    filters: list[ViewFilter]


class ViewColumn(BaseModel):
    name: str
    enabled: bool = True
    rank: int | None = None
    # Populated during processing from dataset introspection + config overrides
    label: str | None = None
    sortable: bool = True
    hidden: bool = False
    type: Literal["link", "array-link", "labelled-link", "string"] = "string"
    url: str | None = None
    delimiter: str | None = None


class View(BaseModel):
    url_name: str
    id: str
    name: str
    source: str
    include_remaining_columns: bool = False
    filter_groups: list[ViewFilterGroup]
    columns: list[ViewColumn]
    

# ── Columns ──


class Column(BaseModel):
    name: str | None = None
    label: str | None = None
    sortable: bool = True
    hidden: bool | None = False
    type: Literal["link", "array-link", "labelled-link", "string"] = "string"
    url: str | None = None
    delimiter: str | None = None


# ── Top-level config ──


class Config(BaseModel):
    filters: list[Filter]
    views: list[View]
    columns: dict[str, dict[str, Column]] = {}  # keyed by view id

    @model_validator(mode='before')
    @classmethod
    def copy_filters_to_filter_groups(cls, data: Any) -> Any:
        filter_dict = {d["id"]:d for d in data["filters"]}
        
        for v in data["views"]:
            for g in v["filter_groups"]:
                for f in g["filters"]:
                    if f["id"] in filter_dict.keys():
                        f = filter_dict[f["id"]]
                    else:
                        raise ValueError(f"{f['id']} not found in filters!")

def validate_config(config_data:dict[str, Any]) -> bool:
    Config.model_validate(config_data)
    return True

# ── Dataset models (data.json) ──

class CreateColumn(BaseModel):
    name: str
    command: str


class Dataset(BaseModel):
    name: str
    path: str
    parquet_path: str | Path | None = None
    filter: str | None = None
    filter_column: str | None = None
    create_columns: list[CreateColumn] = []
    column_metadata_path: str | Path | None = None
    columns: list[Column] | None = None

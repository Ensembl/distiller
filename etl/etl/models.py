"""Pydantic models for config.json and data.json, aligned with schema v2."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Union

from pydantic import BaseModel, model_validator

# ── Filter models ──

SUPPORTED_FILTERS = Literal[
        "fixed_list", "match", "prefix", "user_list", "range", "regex"
    ]

SUPPORTED_COLUMNS = Literal["link", "array-link", "labelled-link", "string"] 

class RegexField(BaseModel):
    column: str
    regex_name: str
    match: Literal[">", "<", ">=", "<=", "="]


class RegexExtras(BaseModel):
    fields: list[RegexField]


class Filter(BaseModel):
    id: str
    target_column: str
    label: str
    label: str | None = None
    title: str
    type: SUPPORTED_FILTERS
    filter_labels: str | None = None
    min: float | None = None
    max: float | None = None
    extras: RegexExtras | None = None
    regex: str | None = None
    


# ── View models ──


class ViewFilter(BaseModel):
    id: str

    # Attributes we copy across from the Filter object definition above
    # which is why we're not very tight on the defs
    label: str | None = None
    title: str
    example: str | None = None
    type: (
        SUPPORTED_FILTERS
        | None
    ) = None
    match: Literal["exact", "prefix"] | None = None
    min: float | None = None
    max: float | None = None
    rank: int | None = None
    filter_values: list[dict[str, str]] | None = None
    extras:  RegexExtras | None = None
    regex: str | None = None

    def copy_from_filter(self, filter: Filter) -> None:
        for key, value in filter.model_dump(exclude_none=True).items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.extras = filter.extras


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
    type: SUPPORTED_COLUMNS = "string"
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
    type: SUPPORTED_COLUMNS = "string"
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
                for i in range(len(g["filters"])):
                    f_id = g["filters"][i]["id"]
                    if f_id in filter_dict.keys():
                        g["filters"][i] = filter_dict[f_id]
                    else:
                        raise ValueError(f"{f['id']} not found in filters!")
        print(data["views"][0]["filter_groups"][0]["filters"])
        return data

def validate_config(config_data:dict[str, Any]) -> bool:
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


class Dataset(BaseModel):
    name: str
    path: str
    parquet_path: str | Path | None = None
    filter: str | None = None
    filter_column: str | None = None
    create_columns: list[CreateColumn] = []
    column_metadata_path: str | Path | None = None
    columns: list[Column] | None = None

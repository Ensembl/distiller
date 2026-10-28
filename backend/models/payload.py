from typing import List, Literal, Optional
from pydantic import BaseModel, StrictStr, field_validator

class OrderBy(BaseModel):
    column_id: int
    order: Literal["ASC","DESC"]

class Filter(BaseModel):
    filter_id: StrictStr
    filter_value: StrictStr | List[StrictStr]

    @field_validator("filter_id")
    @classmethod
    def validate_filter_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("filter_id must not be blank")
        return value

    @field_validator("filter_value")
    @classmethod
    def validate_filter_value(cls, value: str | List[str]) -> str | List[str]:
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("filter_value must not be blank")
            return value

        if not value:
            raise ValueError("filter_value must not be an empty list")

        if any(not item.strip() for item in value):
            raise ValueError("filter_value must not contain blank values")

        return list(dict.fromkeys(value)) # Remove duplicates while preserving order


class Payload(BaseModel):
    columns: Optional[List[int]] = [1]
    page: Optional[int] = 1
    per_page: Optional[int] = 100
    filters: Optional[List[Filter]] = []
    order_by: Optional[OrderBy] = None

    # To do: Add validation for columns (and maybe other fields)

    @field_validator("filters")
    @classmethod
    def validate_unique_filter_ids(cls, filters: Optional[List[Filter]]) -> Optional[List[Filter]]:
        if filters is None:
            return filters

        seen = set()
        for item in filters:
            if item.filter_id in seen:
                raise ValueError(f"Duplicate filter_id: {item.filter_id}")
            seen.add(item.filter_id)

        return filters
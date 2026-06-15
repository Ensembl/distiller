from typing import List, Literal, Optional
from pydantic import BaseModel

class OrderBy(BaseModel):
    column_id: int
    order: Literal["ASC","DESC"]

class Filter(BaseModel):
    filter_id: string
    filter_value: string

class Payload(BaseModel):
    columns: Optional[List[int]] = [1]
    page: Optional[int] = 1
    per_page: Optional[int] = 100
    #filters: Optional[List[Filter]] = []
    order_by: Optional[OrderBy] = None
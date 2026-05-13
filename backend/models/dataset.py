from pydantic import BaseModel, ValidationError

class Column(BaseModel):
    name:str
    label:str
    style:str
    is_sortable:bool
    enabled_by_default:bool
    mask:int

class FilterOption(BaseModel):
    label:str
    value:str 

class FilterCore(BaseModel):
    id:str
    tite:str
    label:str
    example:str
    filter_type:str
    rank:int

class FilterRegex(FilterCore):
    regex:str

class FilterSelect(FilterCore):
    options:list[FilterOption]
    
class RangeFilter(FilterCore):
    min:int
    max:int

class FilterGroup(BaseModel):
    id:str
    label:str
    view_id:int
    rank:int
    filters:list[Filter]
    
class DatasetConfig(BaseModel):
    id:str
    label:str
    columns:list[Columns]
    filter_groups:list[FilterGroup]
    
from pydantic import BaseModel, ValidationError

class Columns(BaseModel):
    name:str
    label:str
    style:str
    is_sortable:bool
    enabled_by_default:bool
    mask:int
    
class Filter(BaseModel):
    id:str
    label:str
    filter_type:str
    match_type:str
    regex:str
    min:int
    max:int
    rank:int

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
    
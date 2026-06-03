import json

from core.database import get_db_connection
from core.config import get_dataset_path

def is_empty(v) -> bool:
    if v is None:
        return True
    
    if isinstance(v, list) and len(v) == 0:
        return True
    return False

def fetch_config(dataset_id):
    """
    Generates a dataset config payload based on a provided dataset
    """
    # find dataset by id
    db_path = get_dataset_path(dataset_id)
    
    if db_path is None:
        return "Todo DB path error"
    
    conn = get_db_connection(db_path)
    
    result = conn.sql("SELECT json_config FROM dataset_config WHERE view_id = 1")
    
    payload = json.loads(result.fetchone()[0])
    
    for grp in payload["filter_groups"]:
        for x in range(len(grp["filters"])):
            grp["filters"][x] = {
                k:v for k,v in grp["filters"][x].items() if not is_empty(v)
            }

    return payload


def records(dataset:str):
    # Get dataset
    # build column list
    # build filters 
    # build sort
    return "WIP"
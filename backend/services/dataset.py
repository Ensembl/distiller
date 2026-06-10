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


def generate_records_query(cols:list[str]):
    quote = "'{}'"
    col_str = f"[{','.join(quote.format(c) for c in cols)}]"
    sql = f"""
    with col_select as (
    SELECT COLUMNS({col_str}) FROM dataset_view
    )
    SELECT {{
    "columns":ARRAY(SELECT details FROM column_details where name in {col_str}),
    "rows":ARRAY(SELECT struct_pack(*COLUMNS(*)) FROM col_select limit 4)
    }}::JSON;   
    """
    
    return sql



def records(dataset_id:str):
    # Get dataset
    db_path = get_dataset_path(dataset_id)
    
    if db_path is None:
        return "Todo DB path error"
    
    conn = get_db_connection(db_path)
    
    # TODO
    # - Add input model
    # - Convert column ids into column names
    # - Build up where filter list
    # - Add pagination 
    
    sql = generate_records_query(['gen_alt_symbols','metadata_name_url', 'so_term', 'type'])
    
    result = conn.sql(sql)
    
    payload = json.loads(result.fetchone()[0])

    return payload
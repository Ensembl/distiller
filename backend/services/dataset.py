import json

from core.database import get_db_connection
from core.config import get_dataset_path
from models.payload import Payload


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


def generate_records_query(cols:list[number], page:int = 1, page_size:int = 100, sort_by:int = None, asc:bool = True):
    quote = "'{}'"
    
    if len(cols): 
        col_str = f"[{','.join(quote.format(c) for c in cols)}]"
        column_call = f"column_mapper({col_str})"
    else:
        column_call = "default_columns()"
    sort_var = ""
    sort_stmt = ""
    if sort_by:
        sort_var = f"set variable sort_by = list_first(column_mapper([{sort_by}]));"
        sort_stmt = f"ORDER BY COLUMNS(getvariable('sort_by')) {'ASC' if asc else 'DESC'} NULLS LAST"
    
    sql = f"""
    SET VARIABLE selected_cols = {column_call};
    {sort_var}

    with col_select as (
    SELECT COLUMNS(getvariable('selected_cols')) FROM dataset_view {sort_stmt}
    )
    SELECT {{
    "columns":ARRAY(SELECT details FROM column_details where name in getvariable('selected_cols')),
    "rows":ARRAY(SELECT struct_pack(*COLUMNS(*)) FROM col_select LIMIT {page_size} OFFSET {page}),
    "meta":{{
        'total_hits':list_first(ARRAY(SELECT COUNT(*) FROM dataset_view)),
        'page':{page},
        'per_page':{page_size}
    }}
    }}::JSON;   
    """
    
    return sql


def records(dataset_id:str, payload: Payload |  None = None):
    # Get dataset
    db_path = get_dataset_path(dataset_id)
    
    if db_path is None:
        return "Todo DB path error"
    
    conn = get_db_connection(db_path)
    
    # TODO
    # - Add input model --
    #   - WIP
    # - Convert column ids into column names - done
    #   - SELECT column_mapper([1,3,10]) - done
    #   - Get default uses default_columns - done
    # - Build up where filter list ---
    # - Add pagination - done
    # - Sorting - done
    
    if payload:
        order_by = None
        order = None
        if payload.order_by:
            order_by = payload.order_by.column_id
            order = payload.order_by.order == "ASC"
            
        sql = generate_records_query(
            payload.columns,
            payload.page,
            payload.per_page,
            order_by,
            order
        )
    else:
        sql = generate_records_query([],1,100)

    result = conn.sql(sql)
    
    payload = json.loads(result.fetchone()[0])

    return payload
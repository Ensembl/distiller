import duckdb

def get_macro_from_filter(filter_id:str, filter_type:str) -> str:
    """
        maps filter type to macro
    """
    match filter_type:
        case "select_list":
            return "select_list_filter"
        case "select_exact": 
            return "select_exact_filter"
        case "select_prefix":
            return "select_prefix_filter"
        case "select_in":
            return "???"
        case "list_contains":
            return "???"
        case "range":
            return "range_filter"
        case "regex":
            return f"regex_{filter_id}_filter"


def get_db_connection(path:str):
    """
    FastAPI dependency for database connections.
    Creates a new connection for each request.
    """
    conn = duckdb.connect(path, read_only=True)
    conn.execute("PRAGMA threads = 4")
    conn.execute("PRAGMA memory_limit = '2GB'")
    return conn
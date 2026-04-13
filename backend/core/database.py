import duckdb

def get_db_connection(path:str):
    """
    FastAPI dependency for database connections.
    Creates a new connection for each request.
    """
    conn = duckdb.connect(settings.duckdb_path, read_only=True)
    conn.execute("PRAGMA threads = 4")
    conn.execute("PRAGMA memory_limit = '2GB'")
    try:
        yield conn
    finally:
        conn.close()
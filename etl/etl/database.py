import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Self

import duckdb

from etl.models import View, ViewFilterGroup, RegexExtras, FIXED_LIST_FILTER_TYPE

logger = logging.getLogger(__name__)

schema_version = "v2"

REGEX_MACRO_TEMPLATE = """
CREATE OR REPLACE MACRO regex_{}_filter(table_name, {}) AS TABLE(
    SELECT *
    FROM query_table(table_name)
    WHERE {}
)
"""

VIEW_COLUMN_LINK_COL = """
ALTER TABLE view_column_link ADD {} struct(label VARCHAR, type VARCHAR, sortable BOOL, url VARCHAR, delimiter VARCHAR);"""

VIEW_DATASET = """
CREATE OR REPLACE VIEW dataset_view AS
SELECT 
{{"style":struct_extract(COLUMNS(*),'style') , 'value':struct_extract(COLUMNS(*),'value')}}
FROM dataset_{};
"""

def _process_value(val:str, type:str, url:str|None, delimiter:str|None):
    # Literal["link", "array-link", "labelled-link", "string"] 
    match type:
        case "string":
            return f"\"{val}\""
        case "link":
            return {'label':val, 'url': url.format(val)}
        case "array-link":
             {'values':[
                 {'label':v, 'url': url.format(v)}
                 for v in val.split(delimiter)
                 ]
            }
        case _:
             f"\"{val}\""

class BaseDatabase:
    def __init__(self, release_path: Path, release: str) -> None:
        self.release_path = release_path
        self.release = release
        self.conn: duckdb.DuckDBPyConnection

    def __enter__(self) -> Self:
        path = self.release_path / f"{self.release}.duckdb"
        self.conn = duckdb.connect(str(path))
        return self

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()


class DatabaseConfig(BaseDatabase):

    def __init__(
        self,
        release_path: Path,
        release: str,
        views: list[View],
        schema_version: str = schema_version,
    ):
        BaseDatabase.__init__(self, release_path, release)
        self.views = views
        self.schema_version = schema_version
        self.ids: dict[str, int] = {}
    
    def create_dataset(self, view:View) -> None:
        """
        Method that creates a dataset version of the data table.
        The dataset version switches out a varchar value for a struct that includes
        the column type, a raw version of the value, and a processed version that includes
        everything needed to display the value on the client (see _process_value for details)
        """
        conn = self.conn
        # get dataset table
        # select visible columns
        # get column details
        cols = [c for c in view.columns if c.hidden == False]
        col_lookup = {c.name:c for c in cols}
        col_names = [c.name for c in cols]
        col_args = ", ".join(['?' for x in range(len(col_names))])
        col_structs = [
            f"{n} STRUCT(style VARCHAR, raw VARCHAR, value JSON)"
            for n in col_names
        ]
        # create table
        create_table = f"CREATE TABLE dataset_{view.source} ({', '.join(col_structs)});"
        conn.execute(create_table)
        
        # insert statement
        insert_data = f"INSERT INTO dataset_{view.source} ({', '.join(col_names)}) VALUES({col_args})"
        
        # get values to insert
        select_data = f"SELECT {', '.join(col_names)} FROM {view.source}"
        query = conn.sql(select_data)
        rows = query.fetchall()
        for r in rows:
            row_args = [
                {
                    'style':col_lookup[col_names[x]].type,
                    'raw':r[x],
                    'value':_process_value(
                        r[x],
                        col_lookup[col_names[x]].type,
                        col_lookup[col_names[x]].url,
                        col_lookup[col_names[x]].delimiter
                        )
                }
                for x in range(len(col_names))
            ]
            
            # insert value
            conn.execute(insert_data, row_args)
        
        # create view
        print(VIEW_DATASET.format(view.source))
        conn.execute(VIEW_DATASET.format(view.source))


    def run(self) -> None:
        self.load_schema()
        for view in self.views:
            logging.info(f"Processing {view.name}, filters and columns")
            self.write_view(view)
            logging.info("Finished")
        self.generate_release()

    def write_regex_macro(self, filter_id:str , extras: RegexExtras) -> bool:
        conn = self.conn
        inputs:[str] = []
        matches:[str] = []
        
        for field in extras.fields:
            modifier = ""
            if field.match != "=": #force column to be a int when comparing size
                modifier = "::int"

            inputs.append(f"in_{field.regex_name}")
            matches.append(f"{field.column}{modifier} {field.match} in_{field.regex_name}")
        
        macro = REGEX_MACRO_TEMPLATE.format(filter_id, ",".join(inputs), " AND ".join(matches))
        print("Creating REGEX macro -------------------")
        print(macro)
        print("------------------------------")
        conn.execute(macro)
            
        return True
    
    def write_view_column_link(self,view_id:int, view: View) -> None:
        """
        Create a version of view_column_link that can be joined with the dataset table
        """
        
        conn = self.conn
        
        # extend table to add columns
        args = [view_id]
        for col in view.columns:
            query = VIEW_COLUMN_LINK_COL.format(f"col_{col.name}")
            print(query)
            conn.execute(query)
            args.append(
                f"{{'label':'{col.label}', 'type':'{col.type}', 'sortable':'{col.sortable}', 'url':'{col.url}', 'delimiter':'{col.delimiter}'}}"
            )
        
        # insert
        cols = [f"col_{c.name}" for c in view.columns]
        params = ["?"]
        params.extend(["?" for c in view.columns])
        insert = f"INSERT INTO view_column_link (view_id, { ', '.join(cols)}) VALUES ({', '.join(params)})"
        
        print(insert)
        print("------")
        print(args[1])
        
        conn.execute(insert, args)
        
        

    def write_view(self, view: View) -> None:
        conn = self.conn
        view_db_id = self.next_id("view")

        # Define the view with source instead of dataset_id
        conn.execute(
            'INSERT INTO "view" (view_id, id, name, url_name, source) VALUES (?,?,?,?,?)',  # noqa: E501
            (view_db_id, view.id, view.name, view.url_name, view.source),
        )

        # Write filter groups and their filters
        # After view processing, view.filters is a list[ViewFilterGroup]
        for group in view.filter_groups:
            assert isinstance(group, ViewFilterGroup)
            group_db_id = self.next_id("view_filter_group")
            group_sql = "INSERT INTO view_filter_group (view_filter_group_id, view_id, id, label, rank) VALUES (?,?,?,?,?)"  # noqa: E501
            conn.execute(
                group_sql,
                (group_db_id, view_db_id, group.group_id, group.group_label, group.rank),
            )

            for view_filter in group.filters:
                view_filter_db_id = self.next_id("view_filter")
                filter_sql = "INSERT INTO view_filter (view_filter_id, view_filter_group_id, id, label, title, example, filter_type, rank, min, max, extras, regex) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"  # noqa: E501
                # Generate a unique DB id by prefixing with the view id
                db_filter_id = f"{view.id}_{view_filter.id}"

                extras = view_filter.extras
                if view_filter.type == "regex":
                    self.write_regex_macro(db_filter_id, extras)
                
                if extras:
                    extras_dump = extras.model_dump(exclude_none=True)
                else:
                    extras_dump = "{}"

                filter_params = (
                    view_filter_db_id,
                    group_db_id,
                    db_filter_id,
                    view_filter.label,
                    view_filter.title,
                    view_filter.example,
                    view_filter.type,
                    view_filter.rank,
                    view_filter.min,
                    view_filter.max,
                    extras_dump,
                    view_filter.regex,
                )
                conn.execute(filter_sql, filter_params)
                if (
                    view_filter.type == FIXED_LIST_FILTER_TYPE
                    and view_filter.filter_values is not None
                ):
                    for value in view_filter.filter_values:
                        value_sql = "INSERT INTO view_filter_value (view_filter_id, value, label) VALUES (?,?,?)"  # noqa: E501
                        value_params = (
                            view_filter_db_id,
                            value["value"],
                            value["label"],
                        )
                        conn.execute(value_sql, value_params)
     
        # Write merged columns (column metadata + view association)
        col_index = 0
        for column in view.columns:
            col_db_id = self.next_id("view_column")
            col_sql = "INSERT INTO view_column (view_column_id, view_id, name, label, type, sortable, url, delimiter, hidden, rank, enable_by_default, mask) VALUES (?,?,?,?,?,?,?,?,?,?,?, col_mask(?))"  # noqa: E501
            col_params = (
                col_db_id,
                view_db_id,
                column.name,
                column.label,
                column.type,
                column.sortable,
                column.url,
                column.delimiter,
                column.hidden,
                column.rank,
                column.enabled,
                col_index
            )
            col_index += 1
            conn.execute(col_sql, col_params)
            
        #self.write_view_column_link(view_db_id, view)
        self.create_dataset(view)

    def generate_release(self) -> None:
        sql = "INSERT INTO release (release_label, schema_version) VALUES (strftime(current_date(),'%Y-%m'), ?)"  # noqa: E501
        self.conn.execute(sql, (self.schema_version,))

    def load_schema(self) -> None:
        conn = self.conn
        path = (
            Path(__file__).parent.parent / "sql" / f"schema.{self.schema_version}.sql"
        )
        with open(path, "rt") as fh:
            content = fh.read()
            conn.execute(content)
        logging.info(f"Database schema loaded from {path!r}")

    def get_files(self, prefix: str) -> list[str]:
        """Take a prefix, find all files in the release_path directory
        and load JSON content for further processing"""
        loaded = []
        for file in self.release_path.iterdir():
            if (
                file.is_file()
                and file.name.startswith(f"{prefix}-")
                and file.name.endswith(".json")
            ):
                with open(file, "rt") as fh:
                    content = fh.read()
                    loaded.append(content)
        return loaded

    def next_id(self, table: str) -> int:
        current_id = self.ids.get(table, 1)
        self.ids[table] = current_id + 1
        return current_id


class Database(BaseDatabase):
    """Copies the parquet files present in the release directory into the DuckDB
    database. Looks for all .parquet files in the release_path and creates a table
    for each file named after the file stem.
    """

    def run(self) -> None:
        for path in self.get_parquet_paths():
            self.load_parquet(path)

    def load_parquet(self, path: Path) -> None:
        table_name = path.stem
        logging.info(f"Loading parquet {path!r} into table {table_name!r}")
        self.conn.execute(
            f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{path}')"
        )

    def get_parquet_paths(self) -> Iterator[Path]:
        for file in self.release_path.iterdir():
            if file.is_file() and file.name.endswith(".parquet"):
                yield file

import logging
from pathlib import Path

import duckdb

from etl.models import DataSource

logger = logging.getLogger(__name__)


class Transform:
    """Performs first pass transformation. Takes an input parquet
    or CSV file and any additional columns wanted. Will then
    write the final files to the output path. Paths to parquet
    files are added to the given data source variable.

    Key used is 'parquet'.

    Attributes:
        data_source (list[DatSource]): List of data source definitions
        release_path (Path): Path to output release directory
        target (str): Name of the view to be created in DuckDB
    """

    def __init__(
        self, datasets: list[DataSource], release_path: Path, target: str = "datasource"
    ):
        self.datasets = datasets
        self.release_path = release_path
        self.target = target

    def run(self) -> None:
        for dataset in self.datasets:
            parquet_path = self.transform_dataset(dataset)
            dataset.parquet_path = parquet_path

    def transform_dataset(self, data_source: DataSource) -> Path:
        with duckdb.connect() as conn:
            # Set columns to all first
            dataset_cols = ["*"]
            # add additional columns as needed
            for column_definition in data_source.create_columns:
                logger.debug(
                    f"Creating new column from '{column_definition.command}' as '{column_definition.name}'"  # noqa: E501
                )
                dataset_cols.append(
                    f"{column_definition.command} AS {column_definition.name}"
                )

            if ".parquet" in data_source.path:
                sql_view = f"""
    CREATE VIEW {self.target} AS
    SELECT {", ".join(dataset_cols)}
    FROM read_parquet('{data_source.path}')
            """
            elif ".csv" in data_source.path:
                sql_view = f"""
    CREATE VIEW {self.target} AS
    SELECT {", ".join(dataset_cols)}
    FROM read_csv('{data_source.path}', header=true, all_varchar=true, delim =',', quote='"', sample_size = -1)
    """  # noqa: E501
            else:
                raise ValueError(
                    "Unsupported file format. Use .parquet or .csv (compressed csv should work)"  # noqa: E501
                )
            logger.debug(sql_view)
            print("-----------")
            print(sql_view)
            print("-----------")
            conn.execute(sql_view)
            return self.write_output(data_source, conn)

    def write_output(self, data_source: DataSource, conn) -> Path:
        # output as parquet
        name = f"{data_source.name}.parquet"
        save_path = self.release_path / name
        output_sql = (
            f"COPY {self.target} TO '{save_path}' (FORMAT parquet, COMPRESSION zstd)"
        )
        conn.execute(output_sql)
        return save_path

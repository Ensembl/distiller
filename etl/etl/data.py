import json
from pathlib import Path

import duckdb

from etl.models import Column, DataSource, DatasetInfo


class DatasetsProcessorError(Exception):
    pass


class DataProcessor:
    """Create configuration for data for later use. To do this it

    - Introspects parquet files for column names per dataset
    - Creates a config for all columns including reformatting column names
    - Column overrides (keyed by view id) are applied later by ViewsProcessor
    - Saving to JSON in the release_path

    Attributes:
      - datasets: list[Dataset] of datasets to process
      - views: list[View] of views referencing datasets
      - columns: dict[str,dict[str,Column]] of configs to apply, keyed by view id
      - release_path: where to write data to
    """  # noqa: E501

    def __init__(
        self,
        data_sources: list[DataSource],
        dataset_info: DatasetInfo,
        columns: list[Column],
        release_path: Path,
    ):
        self.sources = data_sources
        self.dataset_info = dataset_info
        self.columns = columns
        self.release_path = release_path

    def run(self) -> None:
        with duckdb.connect() as conn:
            for data_source in self.sources:
                name = data_source.name
                parquet_path = data_source.parquet_path
                if parquet_path is None:
                    raise DatasetsProcessorError(
                        f"Dataset '{name}' has no parquet_path"
                    )
                parquet_path = Path(parquet_path)
                conn.read_parquet(str(parquet_path))
                raw_columns = self.get_columns(parquet_path, conn)

                # Build base column metadata (no view-specific overrides)
                base_columns = self._build_base_columns(raw_columns)
                data_source.columns = base_columns

                # Validate that per-view column overrides reference real columns
                real_names = {c[0] for c in raw_columns}

                if self.dataset_info.source != name:
                    continue
                dataset_overrides = {c.name: c for c in self.columns}
                for col_name in dataset_overrides:
                    if col_name not in real_names:
                        raise DatasetsProcessorError(
                            f"Column '{col_name}' specified in columns config "
                            f"for view '{self.dataset_info.id}' is not found in "
                            f"source '{name}'"
                        )

                # Write data_source metadata JSON
                data_source.parquet_path = None
                metadata_path = self._write_data_source(data_source)
                data_source.column_metadata_path = metadata_path
                data_source.parquet_path = parquet_path

    def _build_base_columns(self, raw_columns: list[tuple[str, str]]) -> list[Column]:
        """Build Column objects from parquet introspection with default labels."""
        column_output = []
        for column_name, _ in raw_columns:
            column_config = Column(name=column_name)
            label = column_name.replace("_", " ")
            label = label[0].upper() + label[1:]
            column_config.label = label
            column_output.append(column_config)
        return column_output

    def _write_data_source(self, data_source: DataSource) -> Path:
        save_path = self.release_path / f"dataset-{data_source.name}.json"
        with open(save_path, "w") as fh:
            json.dump(data_source.model_dump(exclude_none=True), fh, indent=4)
        return save_path

    def get_columns(
        self, parquet_path: Path, conn: duckdb.DuckDBPyConnection
    ) -> list[tuple[str, str]]:
        sql = f"SELECT column_name, column_type FROM (describe'{str(parquet_path)}')"
        return conn.sql(sql).fetchall()

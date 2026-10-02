import json
import logging
import re
from pathlib import Path

import duckdb

from etl.models import (
    Column,
    DataSource,
    Filter,
    RegexExtras,
    DatasetInfo,
    Column,
    Filter,
    FilterGroup,
    FIXED_LIST_FILTER_TYPE,
)

logger = logging.getLogger(__name__)


class FilterError(Exception):
    pass


class DatasetProcessor:
    """Creates the filters available by querying distinct values from each dataset and
    parquet file. Saves to JSON files in the release_path.

    Filters are based on the filters defined in the config file. We also apply
    the filter_label text in the SQL select to get the label for each filter value. You can
    configure this to be different from the cell contents if needed e.g. lowercasing, trimming, adding prefixes etc.

    Attributes:
        - dataSource: list[DataSource] of datasets available to link to a view
        - dataset: DatasetInfo detailing dataset
        - filters: list[Filter] of all available filters
        - columns: dict[str,dict[str,Column]] of per-view column overrides, keyed by view id
        - release_path: Path where to write data to
        - warn_max: int, maximum number of distinct filter values before warning. Default 60
    """  # noqa: E501

    def __init__(
        self,
        dataset: DatasetInfo,
        filters: list[Filter],
        filter_groups: list[FilterGroup],
        data_sources: list[DataSource],
        columns: list[Column],
        release_path: Path,
        warn_max: int = 60,
    ):
        self.dataset = dataset
        self.filters = filters
        self.filter_groups = filter_groups
        self.data_sources = data_sources
        self.columns = columns
        self.release_path = release_path
        self.warn_max = warn_max

    def _get_filters_for_group(
        filters: dict[str, Filter], filter_group: FilterGroup
    ) -> list[Filter]:
        f_results: list[Filter] = []
        for f in filter_group.filters:
            f_results.append(filters[f.id])
        return f_results

    def run(self) -> None:
        filter_dict = {f.id: f for f in self.filters}
        with duckdb.connect() as conn:
            data_source = self.get_data_source(self.dataset.source)
            self.validate_query_columns(self.columns, self.filters)
            # normalised_groups = self.normalise_to_groups(view)
            group_rank = 1
            for group in self.filter_groups:
                group.rank = group_rank
                group_rank += 1
                filter_rank = 1
                for filter in DatasetProcessor._get_filters_for_group(
                    filter_dict, group
                ):
                    self.process_filter(
                        self.dataset, filter, data_source.parquet_path, conn
                    )
                    filter.rank = filter_rank
                    filter_rank += 1
            # Replace view.filters with the normalised groups
            self.populate_additional_columns(self.dataset, self.columns)
            self.write_view(self.dataset)

    def process_filter(
        self,
        dataset: DatasetInfo,
        filter: Filter,
        parquet: str | Path | None,
        conn: duckdb.DuckDBPyConnection,
    ) -> None:
        filter_definition = self.get_filter_definition(dataset, filter)
        if filter_definition.type == FIXED_LIST_FILTER_TYPE:
            filter_values = self.distinct_filter_values(
                filter_definition, parquet, conn
            )
            size = len(filter_values)
            if size == 0:
                logging.warning(
                    f"Problem. No values found for {filter_definition.id!r}"
                )
            elif size > self.warn_max:
                logging.warning(
                    f"{dataset.source} - {filter_definition.id!r} has over {self.warn_max} ({size}) values"  # noqa: E501
                )
            filter.filter_values = filter_values

    def get_filter_definition(self, dataset: DatasetInfo, filter: Filter) -> Filter:
        for filter in self.filters:
            if filter.id == filter.id:
                return filter
        raise FilterError(
            f"Cannot find the filter '{filter.id}' in the view '{dataset.name}'"  # noqa: E501
        )

    def get_data_source(self, source_name: str) -> DataSource:
        for source in self.data_sources:
            if source.name == source_name:
                return source
        raise FilterError(f"No dataset found for '{source_name}'")

    def distinct_filter_values(
        self,
        filter: Filter,
        parquet: str | Path | None,
        conn: duckdb.DuckDBPyConnection,
    ) -> list[dict[str, str]]:
        distinct_sql = f"""
SELECT DISTINCT "{filter.target_column}" AS value, {filter.label} AS label
from '{parquet}'
ORDER BY label ASC
"""
        logger.debug(distinct_sql)
        results = conn.sql(distinct_sql)
        columns = results.columns
        fetch_results = results.fetchall()
        filter_values = []
        for r in fetch_results:
            filter_values.append({columns[0]: str(r[0]), columns[1]: str(r[1])})
        return filter_values

    def validate_query_columns(
        self, columns: list[Column], filters: list[Filter]
    ) -> None:
        """Validate that all query_columns referenced in filters exist in the source."""
        if columns is None:
            return

        # available_columns = {c.name for c in dataset.columns if c.name is not None}
        for filter_def in filters:
            extra = filter_def.extras
            if extra is None:
                # config is only used for complex filter types such as regex
                continue
            elif isinstance(extra, dict):
                raise FilterError(f"Error with extras, not parsed to a model '{extra}'")
            elif isinstance(extra, RegexExtras):
                if filter_def.regex is None:
                    raise FilterError(
                        f"Error Regex not set when extras is set! '{extra}'"
                    )
                regex = re.compile(filter_def.regex)

                registered_regex_keys = [field.regex_name for field in extra.fields]
                regex_keys = regex.groupindex.keys()
                if len(registered_regex_keys) != len(regex_keys):
                    raise FilterError(
                        f"Filter '{filter_def.id}' regex role "
                        "Registered REGEX keys does not match found REGEX keys,"
                        f"registered: {len(registered_regex_keys)}, "
                        f"found: {len(regex_keys)}"
                    )

                for pattern_name in regex_keys:
                    if pattern_name not in registered_regex_keys:
                        raise FilterError(
                            f"Filter '{filter_def.id}' regex role "
                            f"'{pattern_name}' was not registered"
                        )

    def _get_column_override(
        self, columns: list[Column], column_name: str
    ) -> Column | None:
        """Look up a per-view column override."""
        for c in columns:
            if c.name == column_name:
                return c

    def _enrich_view_column(self, view_col: Column, ds_column: Column) -> None:
        """Enrich a ViewColumn with metadata from the dataset column + per-view override."""
        view_col.label = view_col.label if view_col.label else ds_column.label
        view_col.type = ds_column.type
        view_col.sortable = view_col.sortable if view_col else ds_column.sortable
        view_col.url = view_col.url if view_col.url else ds_column.url
        view_col.delimiter = (
            view_col.delimiter if view_col.delimiter else ds_column.delimiter
        )
        view_col.hidden = view_col.hidden if view_col.hidden else False

    def populate_additional_columns(
        self, dataset: DatasetInfo, columns: list[Column]
    ) -> None:
        dataset_columns = self.get_data_source(dataset.source).columns
        if dataset_columns is None:
            return

        # Build a lookup from column name to dataset Column
        ds_col_lookup: dict[str, Column] = {}
        for dc in dataset_columns:
            if dc.name is not None:
                ds_col_lookup[dc.name] = dc

        rank = 1
        seen: dict[str, bool] = {}
        # Rank existing columns, record seen, and enrich with metadata
        for column in columns:
            column.rank = rank
            rank = rank + 1
            seen[column.name] = True
            ds_col = ds_col_lookup.get(column.name)
            if ds_col:
                self._enrich_view_column(column, ds_col)

        # Add remaining columns (including hidden ones)
        if dataset.include_remaining_columns:
            for ds_column in dataset_columns:
                if ds_column.name is not None and ds_column.name not in seen:
                    new_col = Column(name=ds_column.name, rank=rank)
                    self._enrich_view_column(new_col, ds_column)
                    columns.append(new_col)
                    rank = rank + 1

    def write_view(self, dataset: DatasetInfo) -> Path:
        save_path = self.release_path / f"dataset-{dataset.id}.json"
        with open(save_path, "w") as fh:
            json.dump(dataset.model_dump(exclude_none=True), fh, indent=4)
        return save_path

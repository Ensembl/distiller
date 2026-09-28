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
        - datasets: list[Dataset] of datasets available to link to a view
        - views: list[View] of views to process
        - filters: list[Filter] of all available filters
        - columns: dict[str,dict[str,Column]] of per-view column overrides, keyed by view id
        - release_path: Path where to write data to
        - warn_max: int, maximum number of distinct filter values before warning. Default 60
    """  # noqa: E501

    def __init__(
        self,
        dataset: DatasetInfo,
        filters: list[Filter],
        data_sources: list[DataSource],
        columns: dict[str, dict[str, Column]],
        release_path: Path,
        warn_max: int = 60,
    ):
        self.dataset = dataset
        self.filters = filters
        self.data_sources = data_sources
        self.columns = columns
        self.release_path = release_path
        self.warn_max = warn_max

    def run(self) -> None:
        with duckdb.connect() as conn:
            data_source = self.get_data_source(self.dataset.source)
            self.validate_query_columns(self.dataset, data_source)
            # normalised_groups = self.normalise_to_groups(view)
            group_rank = 1
            for group in self.dataset.filter_groups:
                group.rank = group_rank
                group_rank += 1
                filter_rank = 1
                for view_filter in group.filters:
                    self.process_filter(
                        self.dataset, view_filter, data_source.parquet_path, conn
                    )
                    view_filter.rank = filter_rank
                    filter_rank += 1
                # For auto-wrapped groups (size 1), use the filter's
                # resolved label as the group label
                if len(group.filters) == 1 and group.filters[0].label:
                    group.group_label = group.filters[0].label
            # Replace view.filters with the normalised groups
            self.populate_additional_columns(self.dataset)
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
        self, dataset: DatasetInfo, data_source: DataSource
    ) -> None:
        """Validate that all query_columns referenced in filters exist in the source."""
        if dataset.columns is None:
            return

        available_columns = {c.name for c in dataset.columns if c.name is not None}

        for group in dataset.filter_groups:
            for vf in group.filters:
                filter_def = self.get_filter_definition(dataset, vf)
                extra = filter_def.extras
                if extra is None:
                    # config is only used for complex filter types such as regex
                    continue
                elif isinstance(extra, dict):
                    raise FilterError(
                        f"Error with extras, not parsed to a model '{extra}'"
                    )
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

    def _get_column_override(self, view_id: str, column_name: str) -> Column | None:
        """Look up a per-view column override."""
        view_overrides = self.columns.get(view_id, {})
        return view_overrides.get(column_name)

    def _enrich_view_column(
        self, view_col: Column, ds_column: Column, view_id: str
    ) -> None:
        """Enrich a ViewColumn with metadata from the dataset column + per-view override."""
        override = self._get_column_override(view_id, view_col.name)
        if override is not None:
            view_col.label = override.label if override.label else ds_column.label
            view_col.type = override.type
            view_col.sortable = override.sortable
            view_col.url = override.url
            view_col.delimiter = override.delimiter
            view_col.hidden = override.hidden or False
        else:
            view_col.label = ds_column.label
            view_col.type = ds_column.type
            view_col.sortable = ds_column.sortable
            view_col.url = ds_column.url
            view_col.delimiter = ds_column.delimiter
            view_col.hidden = ds_column.hidden or False

    def populate_additional_columns(self, dataset: DatasetInfo) -> None:
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
        for column in dataset.columns:
            column.rank = rank
            rank = rank + 1
            seen[column.name] = True
            ds_col = ds_col_lookup.get(column.name)
            if ds_col:
                self._enrich_view_column(column, ds_col, dataset.id)

        # Add remaining columns (including hidden ones)
        if dataset.include_remaining_columns:
            for ds_column in dataset_columns:
                if ds_column.name is not None and ds_column.name not in seen:
                    new_col = Column(name=ds_column.name, rank=rank)
                    self._enrich_view_column(new_col, ds_column, dataset.id)
                    dataset.columns.append(new_col)
                    rank = rank + 1

    def write_view(self, dataset: DatasetInfo) -> Path:
        save_path = self.release_path / f"dataset-{dataset.id}.json"
        with open(save_path, "w") as fh:
            json.dump(dataset.model_dump(exclude_none=True), fh, indent=4)
        return save_path

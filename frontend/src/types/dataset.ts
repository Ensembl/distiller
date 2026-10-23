import type { FilterGroup } from './filters';
import type { TableColumn } from './data-table';

export type Dataset = {
  id: string;
  label: string;
};

export type DatasetConfig = {
  columns: TableColumn[];
  filter_groups: FilterGroup[];
};

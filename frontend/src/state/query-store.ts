import { createStore } from './reactive-store';

import type { TableColumn } from "../types/data-table";

type SelectedFixedListFilter = {
  type: 'fixed_list';
  id: string;
  options: string[]; // list of selected options
};

type SelectedMatchStringFilter = {
  type: 'match',
  id: string;
  value: string;
};

type SelectedRegexFilter = {
  type: 'regex';
  id: string;
  value: string;
};

type SelectedRangeFilter = {
  type: 'range',
  id: string;
  min: number;
  max: number;
};

type SelectedFilter =
  | SelectedFixedListFilter
  | SelectedMatchStringFilter
  | SelectedRegexFilter
  | SelectedRangeFilter;


export type SelectedFilters = Record<string, SelectedFilter>;

type QueryState = {
  selectedFilters: SelectedFilters;
  selectedColumnIds: TableColumn['id'][];
  page: number;
  perPage: number;
  sortBy: string | null;
}

const initialState: QueryState = {
  selectedFilters: {},
  selectedColumnIds: [],
  page: 1,
  perPage: 100,
  sortBy: null
};


export const createQueryStore = () => {
  const stateClone = structuredClone(initialState);
  const store = createStore(stateClone);

  const actions = {
    setFilter(filter: SelectedFilter) {
      store.state.selectedFilters[filter.id] = filter;
      store.state.page = 1;
    },

    removeFilter(filterId: string) {
      delete store.state.selectedFilters[filterId];
      store.state.page = 1;
    },

    setSelectedColumnIds(columnIds: QueryState['selectedColumnIds']) {
      store.state.selectedColumnIds = columnIds;
    },

    setPage(page: number) {
      store.state.page = page;
    },

    setPerPage(perPage: number) {
      store.state.perPage = perPage;
      store.state.page = 1;
    },

    reset() {
      Object.assign(
        store.state,
        structuredClone(initialState)
      );
    }
  };

  return {
    ...store,
    actions,
  };
};

export type QueryStore = ReturnType<typeof createQueryStore>;
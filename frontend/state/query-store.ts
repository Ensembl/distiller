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
}

const initialState: QueryState = {
  selectedFilters: {},
  selectedColumnIds: [],
  page: 1,
  perPage: 100
};

export class QueryStore {
  state: QueryState;

  subscriptions: Set<(state: QueryState) => void>;

  #isNotificationQueued = false;

  constructor() {
    this.state = structuredClone(initialState);
    this.subscriptions = new Set();
  }

  getState() {
    return this.state;
  }

  subscribe(fn: (state: QueryState) => void) {
    fn(this.state);
    this.subscriptions.add(fn);
    const unsubscribe = () => this.subscriptions.delete(fn);
    return unsubscribe;
  }

  // batch all notifications into a single animation frame
  notify() {
    if (this.#isNotificationQueued) {
      return
    } {
      this.#isNotificationQueued = true;
      requestAnimationFrame(() => {
        this.subscriptions.forEach(fn => fn(this.state));
        this.#isNotificationQueued = false;
      });
    }
  }

  setFilter(filter: SelectedFilter) {
    this.state.selectedFilters[filter.id] = filter;
    this.state.page = 1;
    this.notify();
  }

  removeFilter(filterId: string) {
    delete this.state.selectedFilters[filterId];
    this.state.page = 1;
    this.notify();
  }

  setSelectedColumnIds(columnIds: QueryState['selectedColumnIds']) {
    this.state.selectedColumnIds = columnIds;
    this.notify();
  }

  setPage(page: number) {
    this.state.page = page;
    this.notify();
  }

  setPerPage(perPage: number) {
    this.state.perPage = perPage;
    this.state.page = 1;
    this.notify();
  }

  reset() {
    this.state = structuredClone(initialState);
    this.notify();
  }

};


export const createQueryStore = () => {
  return new QueryStore();
};
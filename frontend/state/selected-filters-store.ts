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


export type SelectedFiltersState = Record<string, SelectedFilter>;

const initialState: SelectedFiltersState = {};

export class SelectedFiltersStore {
  state: SelectedFiltersState;

  subscriptions: Set<(state: SelectedFiltersState) => void>;

  constructor() {
    this.state = structuredClone(initialState);
    this.subscriptions = new Set();
  }

  getState() {
    return this.state;
  }

  subscribe(fn: (state: SelectedFiltersState) => void) {
    fn(this.state);
    this.subscriptions.add(fn);
    const unsubscribe = () => this.subscriptions.delete(fn);
    return unsubscribe;
  }

  notify() {
    this.subscriptions.forEach(fn => fn(this.state));
  }

  setFilter(filter: SelectedFilter) {
    this.state[filter.id] = filter;
    this.notify();
  }

  removeFilter(filterId: string) {
    delete this.state[filterId];
    this.notify();
  }
};


export const createSelectedFiltersStore = () => {
  return new SelectedFiltersStore();
};
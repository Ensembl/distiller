import { createStore } from './reactive-store';

import type { Dataset } from '../types/dataset';
import type { FilterGroup } from '../types/filters';
import type { TableColumn } from '../types/data-table';
import type { LoadingStatus } from '../types/loading-status';

export type ConfigState = {
  loadingStatus: LoadingStatus;
  datasets: Dataset[];
  selectedDatasetId: string | null;
  filterGroups: FilterGroup[];
  selectedFilterGroupId: string | null;
  selectedFilterId: string | null;
  columns: TableColumn[];
};

const initialState: ConfigState = {
  loadingStatus: 'initial',
  datasets: [],
  selectedDatasetId: null,
  filterGroups: [],
  selectedFilterGroupId: null,
  selectedFilterId: null,
  columns: []
};


export const createConfigStore = () => {
  const stateClone = structuredClone(initialState);
  const store = createStore(stateClone);

  const actions = {
    setLoadingStatus(loadingStatus: LoadingStatus) {
      store.state.loadingStatus = loadingStatus;
    },

    setDatasets(datasets: Dataset[]) {
      store.state.datasets = datasets;

      // select the first dataset bu default
      const firstDataset = datasets[0];
      this.setSelectedDatasetId(firstDataset.id);
    },

    setSelectedDatasetId(datasetId: string) {
      const selectedDataset = store.state.datasets
        .find(dataset => dataset.id === datasetId);

      if (!selectedDataset) {
        return;
      }

      store.state.selectedDatasetId = datasetId;
    },

    setFilterGroups(filterGroups: FilterGroup[]) {
      // update filter groups
      store.state.filterGroups = filterGroups;

      // select the first filter group by default
      const firstFilterGroup = filterGroups[0];
      this.setSelectedFilterGroupId(firstFilterGroup.id);
    },

    setColumns(columns: TableColumn[]) {
      store.state.columns = columns;
    },

    setSelectedFilterGroupId(id: string) {
      // update selected filter group id
      const filterGroup = store.state.filterGroups
        .find(group => group.id === id);
      if (!filterGroup) {
        return;
      }
      store.state.selectedFilterGroupId = id;

      // select the first filter in the group by default
      const firstFilter = filterGroup.filters[0];
      this.setSelectedFilterId(firstFilter.id);
    },

    setSelectedFilterId(id: string) {
      const filterGroup = store.state.filterGroups
        .find(group => group.id === store.state.selectedFilterGroupId);
      const filter = filterGroup?.filters.find(filter => filter.id === id);
      if (!filter) {
        return;
      }
      store.state.selectedFilterId = id;
    },

    clear() {
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

export type ConfigStore = ReturnType<typeof createConfigStore>;

























/**



type Subscriber = (state: ConfigState) => void;

export class XConfigStore {
  state: ConfigState;

  subscriptions: Set<Subscriber>;

  #isNotificationQueued = false;

  constructor() {
    this.state = structuredClone(initialState);
    this.subscriptions = new Set();
  }

  getState() {
    return this.state;
  }

  subscribe(fn: Subscriber) {
    fn(this.state);
    this.subscriptions.add(fn);
    const unsubscribe = () => this.subscriptions.delete(fn);
    return { unsubscribe };
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

  setLoadingStatus(loadingStatus: LoadingStatus) {
    this.state.loadingStatus = loadingStatus;
  }

  setDatasets(datasets: Dataset[]) {
    this.state.datasets = datasets;

    // select the first dataset bu default
    const firstDataset = datasets[0];
    this.setSelectedDatasetId(firstDataset.id);

    this.notify();
  }

  setSelectedDatasetId(datasetId: string) {
    const selectedDataset = this.state.datasets.find(dataset => dataset.id === datasetId);
    if (!selectedDataset) {
      return;
    }

    this.state.selectedDatasetId = datasetId;
    this.notify();
  }

  setFilterGroups(filterGroups: FilterGroup[]) {
    // update filter groups
    this.state.filterGroups = filterGroups;

    // select the first filter group by default
    const firstFilterGroup = filterGroups[0];
    this.setSelectedFilterGroupId(firstFilterGroup.id);

    this.notify();
  }

  setColumns(columns: TableColumn[]) {
    this.state.columns = columns;
  }

  setSelectedFilterGroupId(id: string) {
    // update selected filter group id
    const filterGroup = this.state.filterGroups.find(group => group.id === id);
    if (!filterGroup) {
      return;
    }
    this.state.selectedFilterGroupId = id;

    // select the first filter in the group by default
    const firstFilter = filterGroup.filters[0];
    this.setSelectedFilterId(firstFilter.id);

    this.notify();
  }

  setSelectedFilterId(id: string) {
    const filterGroup = this.state.filterGroups
      .find(group => group.id === this.state.selectedFilterGroupId);
    const filter = filterGroup?.filters.find(filter => filter.id === id);
    if (!filter) {
      return;
    }
    this.state.selectedFilterId = id;

    this.notify();
  }

  clear() {
    this.state = structuredClone(initialState);

    this.notify();
  }
};


// export const createConfigStore = () => {
//   return new ConfigStore();
// };


 */
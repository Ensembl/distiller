import { html, css, LitElement } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import { fetchDatasets, fetchDatasetConfig } from './data-provider/data-provider';

import { createConfigStore, type ConfigStore, type ConfigState } from './state/config-store';
import { createQueryStore, type QueryStore } from './state/query-store';

import './components/header/header';
import './components/main/main';

import resetStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/resets.js';

@customElement('ens-data-distiller')
export class TopPanel extends LitElement {

  static styles = [
    resetStyles,
    css`
      :host {
        display: grid;
        grid-template-rows: auto 1fr;
        height: 100%; // this can be overwritten via the class attribute by parent
      }
    `
  ];

  configStore: ConfigStore = createConfigStore()
  queryStore: QueryStore = createQueryStore()

  configStoreSubscription: ReturnType<ConfigStore['subscribe']> | null = null;

  connectedCallback() {
    super.connectedCallback();
    this.#fetchDatasets();
    this.#setListeners();
  }

  disconnectedCallback() {
    this.#removeListeners();
    super.disconnectedCallback();
  }

  #setListeners() {
    this.configStoreSubscription = this.configStore.subscribe((stateChange) => {
      if (stateChange.key === 'selectedDatasetId') {
        this.#onDatasetChange({
          datasetId: this.configStore.state.selectedDatasetId
        });
      }
    });
  }

  #removeListeners() {
    this.configStoreSubscription?.unsubscribe();
  }

  async #fetchDatasets() {
    this.configStore.actions.setLoadingStatus('loading');
    const datasets = await fetchDatasets();
    const firstDataset = datasets[0];
    const firstDatasetId = firstDataset.id;
    this.configStore.actions.setDatasets(datasets);
    this.configStore.actions.setSelectedDatasetId(firstDatasetId);
  }

  async #onDatasetChange({
    datasetId
  }: {
    datasetId: ConfigState['selectedDatasetId'];
  }) {
    if (!datasetId) {
      return;
    }
    this.configStore.actions.setLoadingStatus('loading');
    const datasetConfig = await fetchDatasetConfig({ datasetId });

    // check against a race condition (e.g. use switching datasets before response arrives)
    if (datasetId !== this.configStore.state.selectedDatasetId) {
      return;
    }

    const { filter_groups, columns } = datasetConfig;

    this.configStore.actions.setFilterGroups(filter_groups);
    this.configStore.actions.setColumns(columns);

    // reset the query store
    this.queryStore.actions.reset();

    const defaultSelectedColumnIds = columns.map(column => column.id);
    this.queryStore.actions.setSelectedColumnIds(defaultSelectedColumnIds);

    this.configStore.actions.setLoadingStatus('success');
  }

  render() {
    return html`
      <ens-data-distiller-header
        .configStore=${this.configStore}
      ></ens-data-distiller-header>
      <ens-data-distiller-main
        .configStore=${this.configStore}
        .queryStore=${this.queryStore}
      ></ens-data-distiller-main>
    `;
  }
}
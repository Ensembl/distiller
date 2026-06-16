import { html, css, LitElement } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import { fetchDatasets, fetchDatasetConfig } from './data-provider/data-provider';

import { createConfigStore, type ConfigStore } from './state/config-store';
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
  currentDatasetId: string | null = null;

  connectedCallback(): void {
    super.connectedCallback();
    this.#fetchDatasets();
    this.#setListeners();
  }

  #setListeners() {
    this.configStoreSubscription = this.configStore.subscribe((state) => {
      if (state.selectedDatasetId !== this.currentDatasetId) {
        this.currentDatasetId = state.selectedDatasetId;
        this.#onDatasetChange();
      }
    });
  }

  async #fetchDatasets() {
    this.configStore.setLoadingStatus('loading');
    const datasets = await fetchDatasets();
    const firstDataset = datasets[0];
    const firstDatasetId = firstDataset.id;
    this.configStore.setDatasets(datasets);
    this.configStore.setSelectedDatasetId(firstDatasetId);
  }

  async #onDatasetChange() {
    const datasetId = this.currentDatasetId;
    if (!datasetId) {
      return;
    }
    this.configStore.setLoadingStatus('loading');
    const datasetConfig = await fetchDatasetConfig({ datasetId });

    const { filter_groups, columns } = datasetConfig;

    this.configStore.setFilterGroups(filter_groups);
    this.configStore.setColumns(columns);

    // reset the query store
    this.queryStore.reset();

    const defaultSelectedColumnIds = columns.map(column => column.id);
    this.queryStore.setSelectedColumnIds(defaultSelectedColumnIds);

    this.configStore.setLoadingStatus('success');
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
import { html, css, LitElement } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import { fetchDatasetsAndFirstDatasetConfig } from './data-provider/data-provider';

import { createConfigStore, type ConfigStore } from './state/config-store';
import { createSelectedFiltersStore, type SelectedFiltersStore } from './state/selected-filters-store';


import './components/header/header';
import './components/main/main';

@customElement('ens-data-distiller')
export class TopPanel extends LitElement {

  static styles = css`
    :host {
      display: grid;
      grid-template-rows: auto 1fr;
      height: 100%; // this can be overwritten via the class attribute by parent
    }
  `;

  configStore: ConfigStore = createConfigStore()
  selectedFiltersStore: SelectedFiltersStore = createSelectedFiltersStore()

  connectedCallback(): void {
    super.connectedCallback();
    this.fetchInitialConfig();
  }

  async fetchInitialConfig() {
    this.configStore.setLoadingStatus('loading');
    const { datasets, currentDatasetId, filterGroups } = await fetchDatasetsAndFirstDatasetConfig();
    this.configStore.setDatasets(datasets);
    this.configStore.setSelectedDatasetId(currentDatasetId);
    this.configStore.setFilterGroups(filterGroups);
    this.configStore.setLoadingStatus('success');
  }

  render() {
    const state = this.configStore.getState();

    return html`
      <ens-data-distiller-header
        .configStore=${this.configStore}
      ></ens-data-distiller-header>
      <ens-data-distiller-main
        .configStore=${this.configStore}
      ></ens-data-distiller-main>
    `;
  }
}
import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

import '@ensembl/ensembl-elements-common/components/button/button.js';
import '@ensembl/ensembl-elements-common/components/select/select.js';

import type { ConfigStore } from '../../state/config-store';

@customElement('ens-data-distiller-header')
export class TopPanel extends LitElement {
  static styles = css`
    :host {
      display: grid;
      grid-template-columns: [title] auto [datasets] auto [download] 1fr;
      column-gap: 50px;
      align-items: center;
      height: 72px;
      background-color: var(--color-light-grey);
      padding: 0 var(--double-standard-gutter) 0 var(--standard-gutter);
    }

    .title {
      font-weight: var(--font-weight-bold);
    }

    .datasets {
      display: flex;
      align-items: center;
      column-gap: 1rem;
    }

    .datasets-label {
      font-weight: var(--font-weight-light);
    }

    .download {
      justify-self: end;
    }
  `;

  @property({ type: Object })
  configStore!: ConfigStore;

  configStoreSubscription: ReturnType<ConfigStore['subscribe']> | null = null;

  connectedCallback() {
    super.connectedCallback();
    this.#subscribeToConfigStore();
  }

  disconnectedCallback() {
    this.configStoreSubscription?.unsubscribe();
    super.disconnectedCallback();
  }

  #subscribeToConfigStore() {
    this.configStoreSubscription = this.configStore.subscribe((stateChange) => {
      const trackedKeys = ['datasets', 'selectedDatasetId'];
      if (trackedKeys.includes(stateChange.key as string)) {
        this.requestUpdate();
      }
    });
  }

  #onDatasetIdChange(event: Event) {
    const selectElement = event.currentTarget as HTMLSelectElement;
    const datasetId = selectElement.value;
    this.configStore.actions.setSelectedDatasetId(datasetId);
  }

  render() {
    if (!this.configStore) {
      return null;
    }
    const selectedDatasetId = this.configStore.state.selectedDatasetId ?? '';
    const datasets = this.configStore.state.datasets;

    return html`
      <span class="title">
        Ensembl data distiller
      </span>
      <label class="datasets">
        <span class="datasets-label">
          Dataset
        </span>
        <ens-select>
          <select
            .value=${selectedDatasetId}
            @change=${this.#onDatasetIdChange}
          >
            ${datasets.map((dataset) => {
              return html`
                <option
                  value=${dataset.id}
                >
                  ${dataset.label}
                </option>  
              `
            })}
          </select>
        </ens-select>
      </label>
      <ens-button class="download">
        Download data
      </ens-button>
    `;
  }
}
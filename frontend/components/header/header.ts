import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

import '@ensembl/ensembl-elements-common/components/select/select.js';

import type { ConfigStore } from '../../state/config-store';
import type { Dataset } from '../../types/dataset';

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
      padding: 0 var(--standard-gutter);
    }

    .title {
      font-weight: var(--font-weight-bold);
    }

    .download {
      justify-self: end;
    }
  `;

  @property({ type: Object })
  configStore: ConfigStore | null = null;

  @state()
  selectedDatasetId: string | null = null;

  @state()
  datasets: Dataset[] = [];

  configStoreSubscription: ReturnType<ConfigStore['subscribe']> | null = null;

  disconnectedCallback(): void {
    this.configStoreSubscription?.unsubscribe();
  }

  updated(changedProperties: Map<string, unknown>) {
    if (changedProperties.has('configStore') && this.configStore) {
      this.configStoreSubscription = this.configStore.subscribe((state) => {
        if (state.datasets !== this.datasets) {
          this.datasets = state.datasets;
        }
        if (state.selectedDatasetId !== this.selectedDatasetId) {
          this.selectedDatasetId = state.selectedDatasetId;
        } 
      });
    }
  }

  render() {
    return html`
      <span class="title">
        Ensembl data distiller
      </span>
      <ens-select>
        <select
          .value=${this.selectedDatasetId ?? ''}
        >
          ${this.datasets.map((dataset) => {
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
      <span class="download">
        Download
      </span>
    `;
  }
}
import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

import { fetchRecords } from '../../data-provider/data-provider';

import resetStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/resets.js';
import tableStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/table.js';
import { panelStyles } from '../../styles/panel-styles';

import type { ConfigStore } from '../../state/config-store';
import type { QueryStore } from '../../state/query-store';
import type { TableCell, TableData } from '../../types/data-table';

@customElement('ens-data-distiller-panel-bottom')
export class BottomPanel extends LitElement {
  static styles = [
    resetStyles,
    tableStyles,
    panelStyles,
    css`
      :host {
        display: block;
        padding-top: 24px;
        padding-left: var(--standard-gutter);
        border-radius: 5px;
        overflow: auto;
        white-space: nowrap;
      }
    `
  ];

  @property({ type: Object })
  configStore!: ConfigStore;

  @property({ type: Object })
  queryStore!: QueryStore;

  @state()
  tableData: TableData | null = null;

  queryStoreSubscription: ReturnType<QueryStore['subscribe']> | null = null;

  connectedCallback() {
    super.connectedCallback();
    this.#subscribeToQueryStore();
  }

  disconnectedCallback() {
    this.queryStoreSubscription?.unsubscribe();
    super.disconnectedCallback();
  }

  #subscribeToQueryStore() {
    this.queryStoreSubscription = this.queryStore.subscribe((stateChange) => {
      const trackedKeys = ['selectedColumnIds', 'page', 'perPage'];
      if (trackedKeys.includes(stateChange.key as string)) {
        this.#fetchRecords();
      }
    });
  }

  async #fetchRecords() {
    const datasetId = this.configStore.state.selectedDatasetId;
    const { selectedColumnIds, page, perPage } = this.queryStore.state;

    if (!datasetId || !selectedColumnIds.length) {
      return;
    }

    this.tableData = await fetchRecords({
      datasetId,
      columnIds: selectedColumnIds,
      page,
      perPage
    });
  }

  render() {
    if (!this.tableData) {
      return null;
    }

    const { columns, rows } = this.tableData;

    return html`
      <table class="ens-table">
        <thead>
          <tr>
            ${columns.map(column => html`
              <th>${column.label}</th>
            `)}
          </tr>
        </thead>
        <tbody>
          ${rows.map(row => html`
            <tr>
              ${columns.map(column => html`
                <td>${this.renderCell(row[column.name])}</td>
              `)}
            </tr>
          `)}
        </tbody>
      </table>
    `;
  }

  renderCell(cell: TableCell) {
    if (cell.style === 'link') {
      return html`
        <a href=${cell.value.url} target="_blank" rel="noopener noreferrer">
          ${cell.value.label}
        </a>
      `;
    }

    return cell.value;
  }
}

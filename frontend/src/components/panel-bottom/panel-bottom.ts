import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

import { fetchRecords } from '../../data-provider/data-provider';

import '@ensembl/ensembl-elements-common/components/external-link/external-link.js';
import '@ensembl/ensembl-elements-common/components/select/select.js';
import '@ensembl/ensembl-elements-common/components/paginator/paginator.js';
import './action-buttons/action-buttons';

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
        position: relative;
        display: grid;
        grid-template-rows: auto 1fr;
        min-width: 0;
        min-height: 0;
        padding-top: 24px;
        padding-left: var(--standard-gutter);
        border-radius: 5px;
      }

      .table-controls-area {
        display: grid;
        grid-template-columns: 1fr auto auto;
        align-items: center;
        column-gap: 1.5rem;
        padding-bottom: 1rem;
      }

      .table-container {
        overflow: auto;
        white-space: nowrap;
      }

      .total-hits,
      .per-page-container {
        display: flex;
        align-items: center;
        column-gap: 1rem;
      }

      .total-hits-label,
      .per-page-label {
        font-weight: var(--font-weight-light);
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
      this.tableData = null;
      return;
    }

    const tableData = await fetchRecords({
      datasetId,
      columnIds: selectedColumnIds,
      page,
      perPage
    });
    const isCurrentPage = page === this.queryStore.state.page
      && perPage === this.queryStore.state.perPage;

    if (isCurrentPage) {
      this.tableData = tableData;
    }
  }

  #onPageChange(event: CustomEvent<number>) {
    const page = event.detail;
    this.queryStore.actions.setPage(page);
  }

  #onPerPageChange(event: Event) {
    const selectElement = event.currentTarget as HTMLSelectElement;
    const perPage = parseInt(selectElement.value);
    this.queryStore.actions.setPerPage(perPage);
  }

  render() {
    if (!this.tableData) {
      return null;
    }

    const { columns, rows, meta } = this.tableData;

    return html`
      ${this.renderTableControlsArea(meta)}
      <div class="table-container">
        <table class="ens-table">
          <thead class="sticky-table-head">
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
      </div>
      <ens-data-distiller-action-buttons></ens-data-distiller-action-buttons>
    `;
  }

  renderTableControlsArea(meta: TableData['meta']) {
    const perPageOptions = [100, 200, 500, 1000];
    const totalPages = Math.ceil(meta.total_hits / meta.per_page);

    return html`
      <div class="table-controls-area">
        <div class="total-hits">
          <span>${meta.total_hits.toLocaleString('en-GB')}</span>
          <span class="total-hits-label">
            results
          </span>
        </div>
        <div class="per-page-container">
          <ens-select>
            <select
              aria-label="Table rows per page"
              @change=${this.#onPerPageChange}
            >
              ${perPageOptions.map(perPageOption => html`
                <option
                  value=${perPageOption}
                  ?selected=${perPageOption === meta.per_page}
                >
                  ${perPageOption}
                </option>
              `)}
            </select>
          </ens-select>
          <span class="per-page-label">
            per page
          </span>
        </div>
        <ens-paginator
          current-page=${meta.page}
          total-pages=${totalPages}
          @ens-paginator-page-change=${this.#onPageChange}
        ></ens-paginator>
      </div>
    `;
  }

  renderCell(cell: TableCell) {
    if (cell.style === 'link') {
      if (!cell.value.label) {
        return null;
      }

      return html`
        <ens-external-link href=${cell.value.url}>
          ${cell.value.label}
        </ens-external-link>
      `;
    }

    return cell.value;
  }
}

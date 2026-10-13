import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';

import { fetchRecords } from '../../data-provider/data-provider';

import '@ensembl/ensembl-elements-common/components/external-link/external-link.js';
import '@ensembl/ensembl-elements-common/components/select/select.js';
import '@ensembl/ensembl-elements-common/components/paginator/paginator.js';
import '@ensembl/ensembl-elements-common/components/table/sortable-column-header.js';
import '@ensembl/ensembl-elements-common/components/icon-buttons/delete-button/delete-button.js';
import '@ensembl/ensembl-elements-common/components/icon-buttons/download-button/download-button.js';
import '@ensembl/ensembl-elements-common/components/icon-buttons/table-view-button/table-view-button.js';
import './action-buttons/action-buttons';

import resetStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/resets.js';
import tableStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/table.js';
import { panelStyles } from '../../styles/panel-styles';

import type { ConfigStore } from '../../state/config-store';
import type { QueryStore } from '../../state/query-store';
import type { TableCell, TableColumn, TableData } from '../../types/data-table';

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

      .initial-content {
        --icon-button-height: 20px;
        --icon-button-width: 20px;
        display: grid;
        grid-template-columns: auto 1fr;
        column-gap: 30px;
        row-gap: 30px;

        .strong {
          --icon-button-disabled-color: var(--color-black);
          font-weight: var(--font-weight-bold);
        }
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
      const trackedKeys = ['selectedColumnIds', 'page', 'perPage', 'orderBy'];
      if (trackedKeys.includes(stateChange.key as string)) {
        this.#fetchRecords();
      }
    });
  }

  async #fetchRecords() {
    const apiBaseUrl = this.configStore.state.apiBaseUrl;
    const datasetId = this.configStore.state.selectedDatasetId;
    const { selectedColumnIds, page, perPage, orderBy } = this.queryStore.state;

    if (!datasetId || !selectedColumnIds.length) {
      this.tableData = null;
      return;
    }

    const tableData = await fetchRecords({
      apiBaseUrl,
      datasetId,
      columnIds: selectedColumnIds,
      page,
      perPage,
      orderBy
    });

    const isCurrentQuery = page === this.queryStore.state.page
      && perPage === this.queryStore.state.perPage
      && orderBy === this.queryStore.state.orderBy;

    if (isCurrentQuery) {
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

  #onOrderChange(columnId: TableColumn['id']) {
    this.queryStore.actions.setOrder(columnId);
  }

  render() {
    if (!this.tableData) {
      return this.renderInitial();
    }

    const { columns, rows, meta } = this.tableData;

    return html`
      ${this.renderTableControlsArea(meta)}
      <div class="table-container">
        <table class="ens-table">
          <thead class="sticky-table-head">
            <tr>
              ${columns.map(column => this.renderColumnHead(column))}
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

  renderInitial() {
    const isLoaded = this.configStore.state.loadingStatus === 'success';
    const hasSelectedColumns = this.queryStore.state.selectedColumnIds.length > 0;

    if (!isLoaded || hasSelectedColumns) {
      return null;
    }

    return html`
      <div class="initial-content">
        <ens-table-view-button disabled class="strong"></ens-table-view-button>
        <span class="strong">Select data from the options above to start</span>

        <ens-delete-button disabled></ens-delete-button>
        <span>Select to clear</span>

        <ens-download-button disabled></ens-download-button>
        <span>Select to download</span>
      </div>
      <ens-data-distiller-action-buttons inert></ens-data-distiller-action-buttons>
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

  renderColumnHead(column: TableData['columns'][number]) {
    if (!column.sortable) {
      return html`
        <th>${column.label}</th>
      `;
    }

    const orderBy = this.queryStore.state.orderBy;
    const sortOrder = orderBy?.columnId === column.id ? orderBy.order : undefined;

    return html`
      <th>
        <ens-table-sortable-column-head
          sort-order=${ifDefined(sortOrder)}
          @click=${() => this.#onOrderChange(column.id)}
        >
          ${column.label}
        </ens-table-sortable-column-head>
      </th>
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

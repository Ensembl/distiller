import { html, css, nothing, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import '@ensembl/ensembl-elements-common/components/text-button/text-button.js'
import '@ensembl/ensembl-elements-common/components/checkbox/checkbox.js';
import '@ensembl/ensembl-elements-common/components/icon-buttons/expand-button/expand-button.js';
import '@ensembl/ensembl-elements-common/components/input/input.js';

import '../circle-counter/circle-counter';
import '../filters/fixed-list-filter';
import '../filters/match-string-filter';
import '../filters/regex-filter';
import '../filters/range-filter';

import resetStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/resets.js';
import { panelStyles } from '../../styles/panel-styles';

import type { ConfigStore } from '../../state/config-store';
import type { QueryStore } from '../../state/query-store';
import type { TableColumn } from '../../types/data-table';

@customElement('ens-data-distiller-panel-top')
export class TopPanel extends LitElement {
  static styles = [
    resetStyles,
    panelStyles,
    css`
      :host {
        --top-panel-padding-top: 24px;
        position: relative;
        display: grid;
        grid-template-columns: [sidebar] auto [main] 1fr;
        min-height: 200px;
        height: 30%;
        height: 200px;
        border-radius: 5px;      
      }

      :host([collapsed]) {
        display: flex;
        align-items: center;
        min-height: 60px;
        height: 60px;
      }

      .collapsed-content {
        display: flex;
        align-items: center;
        column-gap: 1rem;
        padding-left: var(--standard-gutter);
      }

      .toggle-container {
        position: absolute;
        right: 0;
        top: 0;
        transform: translateX(80%);
        background-color: var(--color-white);
        padding-top: 14px;
        padding-bottom: 14px;
        padding-right: 14px;
        border-radius: 5px;
      }

      .sidebar {
        height: 100%;
        width: 200px;
        padding-top: var(--top-panel-padding-top);
        padding-left: var(--standard-gutter);
        border-right: 1px solid var(--color-medium-light-grey);
      }

      .sidebar-title {
        margin-bottom: 1rem;
      }

      .sidebar-navigation {
        display: flex;
        flex-direction: column;
        row-gap: 1rem;
        padding-left: 2rem;
      }

      .sidebar-navigation ens-text-button {
        font-weight: var(--font-weight-bold);
      }

      .sidebar-navigation ens-text-button::part(button) {
        font-weight: var(--font-weight-bold);
      }

      .sidebar-navigation-item {
        display: flex;
        align-items: center;
        column-gap: 0.5rem;
      }

      .sidebar-navigation .active {
        --text-button-disabled-color: var(--color-black);
      }

      .main {
        display: grid;
        height: 100%;
        min-height: 0;
        grid-template-rows: auto 1fr;
        padding-left: var(--standard-gutter);
      }

      .filters {
        display: flex;
        align-items: center;
        column-gap: 1.4rem;
        min-height: calc(var(--top-panel-padding-top) + 30px);
        padding-top: var(--top-panel-padding-top);
      }

      .filters .active {
        --text-button-disabled-color: var(--color-black);
      }

      .selection-controls {
        display: flex;
        align-items: center;
        column-gap: 0.5rem;
        margin-left: auto;
        margin-right: var(--standard-gutter);
      }

      .selection-controls ens-input {
        --input-width: 24ch;
        margin-left: 1.4rem;
      }

      .light {
        font-weight: var(--font-weight-light);
      }

      .main-content {
        padding-top: 1rem;
        height: 100%;
        min-height: 0;
      }

      .columns-list {
        display: flex;
        flex-direction: column;
        align-content: flex-start;
        flex-wrap: wrap;
        row-gap: 0.5rem;
        column-gap: 2rem;
        height: 100%;
        min-height: 0;
        overflow-x: auto;
      }
    `
  ];

  @property({ type: Object })
  configStore!: ConfigStore;

  @property({ type: Object })
  queryStore!: QueryStore;

  @property({ type: Boolean, attribute: 'collapsed', reflect: true })
  isCollapsed = false;

  @state()
  isShowingColumnsList: boolean = false;

  @state()
  searchText = '';

  configStoreSubscription: ReturnType<ConfigStore['subscribe']> | null = null;
  queryStoreSubscription: ReturnType<QueryStore['subscribe']> | null = null;

  connectedCallback(): void {
    super.connectedCallback();
    this.#subscribeToConfigStore();
    this.#subscribeToQueryStore();
  }

  disconnectedCallback(): void {
    this.configStoreSubscription?.unsubscribe();
    this.queryStoreSubscription?.unsubscribe();
    super.disconnectedCallback();
  }

  #subscribeToConfigStore() {
    this.configStoreSubscription = this.configStore.subscribe((stateChange) => {
      const trackedKeys = [
        'loadingStatus',
        'filterGroups',
        'selectedFilterGroupId',
        'selectedFilterId',
        'columns'
      ];
      if (trackedKeys.includes(stateChange.key as string)) {
        this.requestUpdate();
      }
    });
  }

  #subscribeToQueryStore() {
    this.queryStoreSubscription = this.queryStore.subscribe((stateChange) => {
      const trackedKeys = [
        'selectedColumnIds',
        'selectedFilters'
      ];
      const isSelectedFilterChange = stateChange.target === this.queryStore.state.selectedFilters;

      if (isSelectedFilterChange || trackedKeys.includes(stateChange.key as string)) {
        this.requestUpdate();
      }
    });
  }

  #onFilterGroupChange(id: string) {
    this.configStore.actions.setSelectedFilterGroupId(id);
    this.isShowingColumnsList = false;
    this.searchText = '';
  }

  #togglePanelCollapsed() {
    this.isCollapsed = !this.isCollapsed;
  }

  #onColumnSelectionChange(columnId: TableColumn['id']) {
    const selectedColumnIds = this.queryStore.state.selectedColumnIds;
    const isSelected = selectedColumnIds.includes(columnId);
    const columnIds = isSelected
      ? selectedColumnIds.filter(id => id !== columnId)
      : [...selectedColumnIds, columnId];

    this.queryStore.actions.setSelectedColumnIds(columnIds);
  }

  #onFixedListFilterChange(filterId: string, options: string[]) {
    if (!options.length) {
      this.queryStore.actions.removeFilter(filterId);
      return;
    }

    this.queryStore.actions.setFilter({
      type: 'fixed_list',
      id: filterId,
      options
    });
  }

  #onSelectAll() {
    if (this.isShowingColumnsList) {
      const columnIds = this.configStore.state.columns.map(column => column.id);
      this.queryStore.actions.setSelectedColumnIds(columnIds);
      return;
    }

    const filter = this.#getSelectedFilter();

    if (filter?.type === 'fixed_list') {
      const options = filter.options.map(option => option.value);
      this.#onFixedListFilterChange(filter.id, options);
    }
  }

  #onDeselectAll() {
    if (this.isShowingColumnsList) {
      this.queryStore.actions.setSelectedColumnIds([]);
      return;
    }

    const filter = this.#getSelectedFilter();

    if (filter) {
      this.queryStore.actions.removeFilter(filter.id);
    }
  }

  #getSelectedFilter() {
    const filterGroups = this.configStore.state.filterGroups;
    const selectedFilterGroupId = this.configStore.state.selectedFilterGroupId;
    const selectedFilterId = this.configStore.state.selectedFilterId;

    const filterGroup = filterGroups.find(group => group.id === selectedFilterGroupId);

    return filterGroup?.filters.find(filter => filter.id === selectedFilterId);
  }

  #onSearchChange(event: Event) {
    const inputElement = event.currentTarget as HTMLInputElement;
    this.searchText = inputElement.value;
  }

  onShowColumnsList() {
    this.isShowingColumnsList = true;
    this.searchText = '';
  }

  onSelectedFilterChange(id: string) {
    this.configStore.actions.setSelectedFilterId(id);
    this.searchText = '';
  }

  render() {
    if (this.isCollapsed) {
      return html`${this.renderCollapsed()}${this.renderToggle()}`;
    }

    return html`${this.renderSidebar()}${this.renderMain()}${this.renderToggle()}`;
  }

  renderSidebar() {
    if (!this.configStore) {
      return null;
    }

    const filterGroups = this.configStore.state.filterGroups;
    const selectedFilterGroupId = this.configStore.state.selectedFilterGroupId;
    const selectedColumnsCount = this.queryStore.state.selectedColumnIds.length;

    return html`
      <div class="sidebar">
        <div class="sidebar-title">
          Data
        </div>
        <div class="sidebar-navigation">
          ${filterGroups.map(group => {
            const isSelected = !this.isShowingColumnsList && group.id === selectedFilterGroupId;
            return html `
              <ens-text-button
                @click=${() => this.#onFilterGroupChange(group.id)}
                class=${isSelected ? 'active' : nothing as unknown as string}
                ?disabled=${isSelected}
              >
                ${group.label}
              </ens-text-button>          
            `;
          })}
          <div class="sidebar-navigation-item">
            <ens-text-button
              @click=${this.onShowColumnsList}
              class=${this.isShowingColumnsList ? 'active' : nothing as unknown as string}
              ?disabled=${this.isShowingColumnsList}
            >
              Attributes
            </ens-text-button>
            <ens-data-distiller-circle-counter ?dimmed=${selectedColumnsCount === 0}>
              ${selectedColumnsCount}
            </ens-data-distiller-circle-counter>
          </div>
        </div>
      </div>    
    `;
  }

  renderMain() {
    const loadingStatus = this.configStore.state.loadingStatus;
    const filterGroups = this.configStore.state.filterGroups;

    if (!filterGroups.length && loadingStatus === 'loading') {
      return 'Loading...';
    }
    if (!filterGroups.length) {
      return null;
    }

    return html`
      <div class="main">
        <div class="filters">
          <span class="light">
            ${this.isShowingColumnsList ? 'Attributes' : 'Filters'}
          </span>
          ${this.isShowingColumnsList ? nothing : this.renderFiltersList()}
          ${this.renderSelectionControls()}
        </div>
        <div class="main-content">
          ${this.isShowingColumnsList
            ? this.renderColumnsList()
            : this.renderFilter()
          }
        </div>
      </div>
    `;
  }

  renderFiltersList() {
    const filterGroups = this.configStore.state.filterGroups;
    const selectedFilterGroupId = this.configStore.state.selectedFilterGroupId;
    const selectedFilterId = this.configStore.state.selectedFilterId;

    const filterGroup = filterGroups.find(group => group.id === selectedFilterGroupId);

    return filterGroup?.filters.map(filter => {
      const isSelected = filter.id === selectedFilterId;
      return html `
        <ens-text-button
          @click=${() => this.onSelectedFilterChange(filter.id)}
          class=${isSelected ? 'active' : nothing as unknown as string}
          ?disabled=${isSelected}
        >
          ${filter.title}
        </ens-text-button>          
      `;
    });
  }

  renderSelectionControls() {
    const hasCheckboxes = this.isShowingColumnsList
      || this.#getSelectedFilter()?.type === 'fixed_list';

    if (!hasCheckboxes) {
      return nothing;
    }

    return html`
      <div class="selection-controls">
        <ens-text-button @click=${this.#onSelectAll}>
          Select all
        </ens-text-button>
        <span>|</span>
        <ens-text-button @click=${this.#onDeselectAll}>
          Deselect all
        </ens-text-button>
        <ens-input
          appearance="shaded"
          placeholder="Find"
          data-aria-label="Find"
          .value=${this.searchText}
          @input=${this.#onSearchChange}
        ></ens-input>
      </div>
    `;
  }

  renderFilter() {
    const filterGroups = this.configStore.state.filterGroups;
    const selectedFilterGroupId = this.configStore.state.selectedFilterGroupId;
    const selectedFilterId = this.configStore.state.selectedFilterId;

    const filterGroup = filterGroups.find(group => group.id === selectedFilterGroupId);
    const filter = filterGroup?.filters.find(filter => filter.id === selectedFilterId);
    if (!filter) {
      return;
    }

    if (filter.type === 'fixed_list') {
      const selectedFilter = this.queryStore.state.selectedFilters[filter.id];
      const selectedValues = selectedFilter?.type === 'fixed_list'
        ? selectedFilter.options
        : [];

      return html`
        <ens-data-distiller-fixed-list-filter
          .filterData=${filter}
          .selectedValues=${selectedValues}
          .searchText=${this.searchText}
          @change=${(event: CustomEvent<string[]>) => this.#onFixedListFilterChange(filter.id, event.detail)}
        ></ens-data-distiller-fixed-list-filter>
      `;    
    } else if (filter.type === 'match') {
      return html`
        <ens-data-distiller-match-string-filter
          .filterData=${filter}
        ></ens-data-distiller-match-string-filter>
      `;
    } else if (filter.type === 'regex') {
      return html`
        <ens-data-distiller-regex-filter
          .filterData=${filter}
        ></ens-data-distiller-regex-filter>
      `;
    } else if (filter.type === 'range') {
      return html`
        <ens-data-distiller-range-filter
          .filterData=${filter}
        ></ens-data-distiller-range-filter>
      `;
    }
  }

  renderColumnsList() {
    const selectedColumnIds = this.queryStore.state.selectedColumnIds;
    const searchText = this.searchText.toLowerCase();
    const columns = this.configStore.state.columns
      .filter(column => column.label.toLowerCase().includes(searchText));

    const checkboxes = columns.map(column => {
      const isSelected = selectedColumnIds.includes(column.id);

      return html`
        <ens-checkbox
          ?checked=${isSelected}
          @change=${() => this.#onColumnSelectionChange(column.id)}
        >
          ${column.label}
        </ens-checkbox>

      `;
    });

    return html`
      <div class="columns-list">
        ${checkboxes}
      </div>
    `;
  }

  renderCollapsed() {
    const filterGroups = this.configStore.state.filterGroups;
    const selectedFilterGroupId = this.configStore.state.selectedFilterGroupId;
    const filterGroup = filterGroups.find(group => group.id === selectedFilterGroupId);
    const label = this.isShowingColumnsList ? 'Attributes' : filterGroup?.label;

    return html`
      <div class="collapsed-content">
        <span>
          Data
        </span>
        <ens-text-button @click=${this.#togglePanelCollapsed}>
          ${label}
        </ens-text-button>
      </div>
    `;
  }

  renderToggle() {
    const buttonLabel = this.isCollapsed
      ? 'Expand the panel'
      : 'Collapse the panel';

    return html`
      <div class="toggle-container">
        <ens-expand-button
          ?expanded=${!this.isCollapsed}
          @click=${this.#togglePanelCollapsed}
          label=${buttonLabel}
        ></ens-expand-button>
      </div>
    `;
  }
}
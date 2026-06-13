import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import '@ensembl/ensembl-elements-common/components/text-button/text-button.js'

import '../filters/fixed-list-filter';
import '../filters/match-string-filter';
import '../filters/regex-filter';

import resetStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/resets.js';
import { panelStyles } from '../../styles/panel-styles';

import type { FilterGroup } from '../../types/filters';
import type { ConfigStore } from '../../state/config-store';
import type { LoadingStatus } from '../../types/loading-status';

// --panel-border-radius: 5px;

@customElement('ens-data-distiller-panel-top')
export class TopPanel extends LitElement {
  static styles = [
    resetStyles,
    panelStyles,
    css`
      :host {
        --top-panel-padding-top: 24px;
        display: grid;
        grid-template-columns: [sidebar] auto [main] 1fr;
        min-height: 200px;
        max-height: 360px;
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

      .main {
        padding-left: var(--standard-gutter);
      }

      .filters {
        display: flex;
        align-items: center;
        column-gap: 1.4rem;
        padding-top: var(--top-panel-padding-top);
      }

      .light {
        font-weight: var(--font-weight-light);
      }

      .filter {
        padding-top: 24px;
      }
    `
  ];

  @property({ type: Object })
  configStore: ConfigStore | null = null;

  @state()
  loadingStatus: LoadingStatus = 'initial';

  @state()
  filterGroups: FilterGroup[] = [];

  @state()
  selectedFilterGroupId: string | null = null;

  @state()
  selectedFilterId: string | null = null;

  configStoreSubscription: ReturnType<ConfigStore['subscribe']> | null = null;

  disconnectedCallback(): void {
    this.configStoreSubscription?.unsubscribe();
  }

  updated(changedProperties: Map<string, unknown>) {
    if (changedProperties.has('configStore') && this.configStore) {
      this.configStoreSubscription = this.configStore.subscribe((state) => {
        if (state.loadingStatus !== this.loadingStatus) {
          this.loadingStatus = state.loadingStatus;
        }
        if (state.filterGroups !== this.filterGroups) {
          this.filterGroups = state.filterGroups;
        }
        if (state.selectedFilterGroupId !== this.selectedFilterGroupId) {
          this.selectedFilterGroupId = state.selectedFilterGroupId;
        }
        if (state.selectedFilterId !== this.selectedFilterId) {
          this.selectedFilterId = state.selectedFilterId;
        }
      });
    }
  }

  onFilterGroupChange(id: string) {
    this.configStore!.setSelectedFilterGroupId(id);
  }

  onFilterChange(id: string) {
    this.configStore!.setSelectedFilterId(id);
  }

  render() {
    return html`${this.renderSidebar()}${this.renderMain()}`;
  }

  renderSidebar() {
    return html`
      <div class="sidebar">
        <div class="sidebar-title">
          Data
        </div>
        <div class="sidebar-navigation">
          ${this.filterGroups.map(group => {
            return html `
              <ens-text-button
                @click=${() => this.onFilterGroupChange(group.id)}
              >
                ${group.label}
              </ens-text-button>          
            `;
          })}
          <ens-text-button>
            Attributes
          </ens-text-button>
        </div>
      </div>    
    `;
  }

  renderMain() {
    if (!this.filterGroups.length && this.loadingStatus === 'loading') {
      return 'Loading...';
    }
    if (!this.filterGroups.length) {
      return null;
    }

    const filterGroup = this.filterGroups.find(group => group.id === this.selectedFilterGroupId);

    return html`
      <div class="main">
        <div class="filters">
          <span class="light">
            Filters
          </span>
          ${filterGroup?.filters.map(filter => {
            return html `
              <ens-text-button
                @click=${() => this.onFilterChange(filter.id)}
              >
                ${filter.title}
              </ens-text-button>          
            `;
          })}
        </div>
        <div class="filter">
          ${this.renderFilter()}
        </div>
      </div>
    `;
  }

  renderFilter() {
    const filterGroup = this.filterGroups.find(group => group.id === this.selectedFilterGroupId);
    const filter = filterGroup?.filters.find(filter => filter.id === this.selectedFilterId);
    if (!filter) {
      return;
    }

    if (filter.type === 'fixed_list') {
      return html`
        <ens-data-distiller-fixed-list-filter
          .filterData=${filter}
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
      // TODO: implement the filter
    }
  }
}
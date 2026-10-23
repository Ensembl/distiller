import { html, css, LitElement } from 'lit';
import { property } from 'lit/decorators.js';
import { customElement } from 'lit/decorators.js';

import '@ensembl/ensembl-elements-common/components/checkbox/checkbox.js';

import type { FixedListFilter as FixedListFilterType } from '../../types/filters';

@customElement('ens-data-distiller-fixed-list-filter')
export class FixedListFilter extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      align-content: flex-start;
      row-gap: 0.5rem;
      column-gap: 2rem;
      flex-wrap: wrap;
      height: 100%;
      overflow-x: auto;
    }
  `;

  @property({ type: Object })
  filterData: FixedListFilterType | null = null;

  @property({ type: Array })
  selectedValues: string[] = [];

  @property({ type: String })
  searchText = '';

  onChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const value = target.dataset.value as string;
    const isChecked = target.checked;

    const selectedValues = isChecked
      ? [...this.selectedValues, value]
      : this.selectedValues.filter(selectedValue => value !== selectedValue);

    const outgoingEvent = new CustomEvent('change', {
      detail: selectedValues
    });
    this.dispatchEvent(outgoingEvent);
  }

  render() {
    if (!this.filterData) {
      return null;
    }

    const searchText = this.searchText.toLowerCase();
    const options = this.filterData.options
      .filter(option => option.label.toLowerCase().includes(searchText));

    const checkboxes = options.map((option) => {
      return html`
        <ens-checkbox
          data-value=${option.value}
          ?checked=${this.selectedValues.includes(option.value)}
          @change=${this.onChange}
        >
          ${option.label}
        </ens-checkbox>
      `
    })

    return html`
      ${checkboxes}
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'ens-data-distiller-fixed-list-filter': FixedListFilter;
  }
}
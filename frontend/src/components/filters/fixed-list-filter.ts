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
      column-gap: 1rem;
      flex-wrap: wrap;
      height: 100%;
    }
  `;

  @property({ type: Object })
  filterData: FixedListFilterType | null = null;

  // TODO: selected values

  #values: string[] = [];

  onChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const value = target.dataset.value as string;
    const isChecked = target.checked;

    if (isChecked) {
      // add to internal values list
      this.#values.push(value);
    } else {
      // remove from internal values list
      this.#values = this.#values.filter(storedValue => value !== storedValue);
    }

    const outgoingEvent = new CustomEvent('change', {
      detail: [...this.#values]
    });
    this.dispatchEvent(outgoingEvent);
  }

  render() {
    if (!this.filterData) {
      return null;
    }

    const checkboxes = this.filterData.options.map((option) => {
      return html`
        <ens-checkbox
          data-value=${option.value}
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
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

  render() {
    if (!this.filterData) {
      return null;
    }

    const checkboxes = this.filterData.options.map((option) => {
      return html`
        <ens-checkbox>
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
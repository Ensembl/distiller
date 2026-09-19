import { html, css, LitElement } from 'lit';
import { property } from 'lit/decorators.js';
import { customElement } from 'lit/decorators.js';

import '@ensembl/ensembl-elements-common/components/input/input.js';

import type { RangeFilter as RangeFilterType } from '../../types/filters';

@customElement('ens-data-distiller-range-filter')
export class RangeFilter extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      row-gap: 1rem;
    }

    .inputs-container {
      --input-width: 30ch;
      display: flex;
      flex-direction: column;
      row-gap: 1rem;
    }

    ens-input::part(wrapper) {
      grid-template-columns: 5ch 1fr;
    }

    ens-input::part(label) {
      justify-self: end;
    }

  `;

  @property({ type: Object })
  filterData: RangeFilterType | null = null;

  render() {
    if (!this.filterData) {
      return null;
    }

    return html`
      <div class="inputs-container">
        <ens-input
          appearance="shaded"
          label="From"
        ></ens-input>
        <ens-input
          appearance="shaded"
          label="To"
        ></ens-input>
      </div>

    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'ens-data-distiller-range-filter': RangeFilter;
  }
}
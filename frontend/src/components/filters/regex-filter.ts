import { html, css, LitElement } from 'lit';
import { property } from 'lit/decorators.js';
import { customElement } from 'lit/decorators.js';

import '@ensembl/ensembl-elements-common/components/input/input.js';

import type { RegexFilter as RegexFilterType } from '../../types/filters';

@customElement('ens-data-distiller-regex-filter')
export class RegexFilter extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    ens-input::part(input-wrapper) {
      width: 60ch;
    }
  `;

  @property({ type: Object })
  filterData: RegexFilterType | null = null;

  render() {
    if (!this.filterData) {
      return null;
    }

    return html`
      <ens-input
        appearance="shaded"
        placeholder=${this.filterData.example}
        .label=${this.filterData.label}
      ></ens-input>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'ens-data-distiller-regex-filter': RegexFilter;
  }
}
import { html, css, LitElement } from 'lit';
import { customElement } from 'lit/decorators.js';

import '@ensembl/ensembl-elements-common/components/select/select.js';


@customElement('ens-data-distiller-header')
export class TopPanel extends LitElement {
  static styles = css`
    :host {
      display: grid;
      grid-template-columns: [title] auto [datasets] auto [download] 1fr;
      column-gap: 50px;
      align-items: center;
      height: 72px;
      background-color: var(--color-light-grey);
      padding: 0 var(--standard-gutter);
    }

    .title {
      font-weight: var(--font-weight-bold);
    }

    .download {
      justify-self: end;
    }
  `;

  render() {
    return html`
      <span class="title">
        Ensembl data distiller
      </span>
      <ens-select>
        <select>
          <option value="one">One</option>
          <option value="two">Two</option>
          <option value="three">Three</option>
        </select>
      </ens-select>
      <span class="download">
        Download
      </span>
    `;
  }
}
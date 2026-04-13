import { html, css, LitElement } from 'lit';
import { customElement } from 'lit/decorators.js';

import '../panel-top/panel-top';
import '../panel-bottom/panel-bottom';

@customElement('ens-data-distiller-main')
export class TopPanel extends LitElement {
  static styles = css`
    :host {
      display: grid;
      grid-template-rows: auto 1fr;
      row-gap: 20px;
      padding: 10px 0 20px;
      background-color: var(--color-medium-light-grey);
    }
  `;

  render() {
    return html`
      <ens-data-distiller-panel-top></ens-data-distiller-panel-top>
      <ens-data-distiller-panel-bottom></ens-data-distiller-panel-bottom>
    `;
  }
}
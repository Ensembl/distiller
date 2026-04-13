import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

import './components/header/header';
import './components/main/main';

// import resetStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/resets.js';
// import { panelStyles } from '../panel/shared-panel-styles';


@customElement('ens-data-distiller')
export class TopPanel extends LitElement {

  static styles = css`
    :host {
      display: grid;
      grid-template-rows: auto 1fr;
      height: 100%; // this can be overwritten via the class attribute by parent
    }
  `;

  render() {
    return html`
      <ens-data-distiller-header></ens-data-distiller-header>
      <ens-data-distiller-main></ens-data-distiller-main>
    `;
  }
}
import { html, css, LitElement } from 'lit';
import { customElement } from 'lit/decorators.js';

import { panelStyles } from '../../styles/panel-styles';

// --panel-border-radius: 5px;

@customElement('ens-data-distiller-panel-bottom')
export class TopPanel extends LitElement {
  static styles = [
    panelStyles,
    css`
      :host {
        display: block;
        border-radius: 5px;      
      }
    `
  ];

  render() {
    return html`
      panel-bottom
    `;
  }
}
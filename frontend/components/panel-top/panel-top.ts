import { html, css, LitElement } from 'lit';
import { customElement } from 'lit/decorators.js';

import { panelStyles } from '../../styles/panel-styles';

// --panel-border-radius: 5px;

@customElement('ens-data-distiller-panel-top')
export class TopPanel extends LitElement {
  static styles = [
    panelStyles,
    css`
      :host {
        display: block;
        min-height: 200px;
        max-height: 360px;
        border-radius: 5px;      
      }
    `
  ];

  render() {
    return html`
      panel-top
    `;
  }
}
import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

import '../panel-top/panel-top';
import '../panel-bottom/panel-bottom';

import resetStyles from '@ensembl/ensembl-elements-common/styles/constructable-stylesheets/resets.js';

import type { ConfigStore } from '../../state/config-store';
import type { QueryStore } from '../../state/query-store';

@customElement('ens-data-distiller-main')
export class TopPanel extends LitElement {
  static styles = [
    resetStyles,
    css`
      :host {
        display: grid;
        height: 100%;
        grid-template-rows: auto 1fr;
        row-gap: 20px;
        padding: 10px 0 20px;
        background-color: var(--color-medium-light-grey);
      }
    `
  ];

  @property({ type: Object })
  configStore: ConfigStore | null = null;

  @property({ type: Object })
  queryStore: QueryStore | null = null;

  render() {
    return html`
      <ens-data-distiller-panel-top
        .configStore=${this.configStore}
        .queryStore=${this.queryStore}
      ></ens-data-distiller-panel-top>
      <ens-data-distiller-panel-bottom></ens-data-distiller-panel-bottom>
    `;
  }
}
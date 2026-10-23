import { html, css, nothing, LitElement } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import './popover';

import {
  styles as buttonsColumnStyles,
  renderButtonsColumn
} from './buttons-column';

import type { ActionView } from '../../../types/action-view';

@customElement('ens-data-distiller-action-buttons')
export class ActionButtons extends LitElement {
  static styles = [
    buttonsColumnStyles,
    css`
      :host {
        --buttons-column-color: var(--color-white);
        --icon-button-height: 20px;
        --icon-button-width: 20px;
        position: absolute;
        top: 0;
        right: 0;
        transform: translateX(calc(100% - 10px));
        z-index: 1;
      }

      :host([inert]) {
        --icon-button-color: var(--color-grey);
      }
    `
  ];

  @state()
  actionView: ActionView = null;

  #onActionViewChange = (actionView: ActionView) => {
    this.actionView = actionView;
  }

  render() {
    return html`
      ${renderButtonsColumn({
        actionView: this.actionView,
        onActionViewChange: this.#onActionViewChange
      })}
      ${this.actionView ? html`
        <ens-data-distiller-action-buttons-popover
          .actionView=${this.actionView}
          .onActionViewChange=${this.#onActionViewChange}
        ></ens-data-distiller-action-buttons-popover>
      ` : nothing}
    `;
  }
}

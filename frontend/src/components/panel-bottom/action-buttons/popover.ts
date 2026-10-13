import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

import { checkOutsideClick } from '../../../utils/check-outside-click';

import {
  styles as buttonsColumnStyles,
  renderButtonsColumn
} from './buttons-column';

import type { ActionView } from '../../../types/action-view';

@customElement('ens-data-distiller-action-buttons-popover')
export class ActionButtonsPopover extends LitElement {
  static styles = [
    buttonsColumnStyles,
    css`
      :host {
        --buttons-column-color: transparent;
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        background-color: var(--color-light-grey);
        border-radius: 5px;
        padding-left: 40px;
        padding-bottom: 30px;
        display: grid;
        grid-template-columns: 1fr auto;
        width: 600px;
      }

      .title {
        font-weight: var(--font-weight-bold);
        padding-top: 24px;
      }
    `
  ];

  @property({ attribute: false })
  actionView: ActionView = null;

  @property({ attribute: false })
  onActionViewChange!: (actionView: ActionView) => void;

  connectedCallback() {
    super.connectedCallback();
    document.addEventListener('keyup', this.#onKeyPress);
    document.addEventListener('mousedown', this.#checkOutsideClick);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.removeEventListener('keyup', this.#onKeyPress);
    document.removeEventListener('mousedown', this.#checkOutsideClick);
  }

  #checkOutsideClick = (event: MouseEvent) => {
    const { isClickOutside } = checkOutsideClick({
      event,
      element: this
    });

    if (isClickOutside) {
      this.onActionViewChange(null);
    }
  }

  #onKeyPress = (event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      this.onActionViewChange(null);
    }
  }

  render() {
    const title = this.actionView === 'clear'
      ? 'Clear all data'
      : 'Download data';

    return html`
      <div class="title">
        ${title}
      </div>
      ${renderButtonsColumn({
        actionView: this.actionView,
        onActionViewChange: this.onActionViewChange
      })}
    `;
  }
}

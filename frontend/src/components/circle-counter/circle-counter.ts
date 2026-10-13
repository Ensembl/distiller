import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('ens-data-distiller-circle-counter')
export class CircleCounter extends LitElement {
  static styles = css`
    :host {
      min-width: 18px;
      height: 18px;
      border-radius: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: var(--color-green);
      color: var(--color-white);
      font-weight: var(--font-weight-bold);
      padding: 2px;
    }

    :host([dimmed]) {
      background-color: var(--color-grey);
    }
  `;

  @property({ type: Boolean })
  dimmed = false;

  render() {
    return html`
      <slot></slot>
    `;
  }
}

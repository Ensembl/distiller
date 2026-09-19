import { css } from 'lit';

/**
 * Panel is offset by a single standard gutter's width from the left edge of the screen.
 * It is also offset from the right edge of the screen by the width of a standard gutter
 * plus a width of the buttons area (which, in itself, is same width as the standard gutter).
 */

export const panelStyles = css`
  :host {
    width: calc(100% - var(--standard-gutter) - var(--double-standard-gutter));
    margin-left: var(--standard-gutter);
    border-radius: var(--panel-border-radius);
    background-color: var(--color-white);
    padding-right: var(--standard-gutter);
  }
`;
import { html, css, nothing } from 'lit';

import '@ensembl/ensembl-elements-common/components/icon-buttons/delete-button/delete-button.js';
import '@ensembl/ensembl-elements-common/components/icon-buttons/download-button/download-button.js';
import '@ensembl/ensembl-elements-common/components/icon-buttons/table-view-button/table-view-button.js';

import type { ActionView } from '../../../types/action-view';

export const styles = css`
  .buttons-column {
    display: flex;
    flex-direction: column;
    row-gap: 30px;
    background-color: var(--buttons-column-color, transparent);
    padding: 24px 15px 30px 0;
    border-radius: 5px;

    .active {
      --icon-button-disabled-color: var(--color-black);
    }
  }
`;

export const renderButtonsColumn = ({
  actionView,
  onActionViewChange
}: {
  actionView: ActionView;
  onActionViewChange: (actionView: ActionView) => void;
}) => {
  return html`
    <div class="buttons-column">
      <ens-table-view-button
        @click=${() => onActionViewChange(null)}
        ?disabled=${actionView === null}
        class=${actionView === null ? 'active' : nothing}
      ></ens-table-view-button>
      <ens-delete-button
        @click=${() => onActionViewChange('clear')}
        ?disabled=${actionView === 'clear'}
        class=${actionView === 'clear' ? 'active' : nothing}
        label="Clear filters"
      ></ens-delete-button>
      <ens-download-button
        @click=${() => onActionViewChange('download')}
        ?disabled=${actionView === 'download'}
        class=${actionView === 'download' ? 'active' : nothing}
      ></ens-download-button>
    </div>
  `;
};

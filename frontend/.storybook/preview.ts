import type { Preview } from '@storybook/web-components-vite';

import '@ensembl/ensembl-elements-common/styles/resets.css';
import '@ensembl/ensembl-elements-common/styles/fonts.css';
import '@ensembl/ensembl-elements-common/styles/global.css';
import '@ensembl/ensembl-elements-common/styles/custom-properties.css';

const preview: Preview = {
  parameters: {
    options: {
      // Hide the bottom panel (which is open by default and is used to show "controls" or "actions" tabs)
      bottomPanelHeight: 0
    }
  }
};

export default preview;
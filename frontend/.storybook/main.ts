import type { StorybookConfig } from '@storybook/web-components-vite';
 
const config: StorybookConfig = {
  framework: '@storybook/web-components-vite',
  stories: ['../stories/**/*.stories.ts'],
  core: {
    disableTelemetry: true // storybook runs telemetry by default; and one has to explicitly opt out to prevent that
  },
  features: {
    sidebarOnboardingChecklist: false, // removes the onboarding section from the sidebar
    changeDetection: false  // removes the 'Review new stories' button from the sidebar
  } 
};
 
export default config;
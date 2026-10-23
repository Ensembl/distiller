import { defineConfig } from 'vite';
import dts from 'vite-plugin-dts';

export default defineConfig({
  plugins: [
    dts({
      entryRoot: '.',
      include: ['src'],
      exclude: ['src/stories', 'src/**/*.test.ts']
    })
  ],
  base: '',
  build: {
    lib: {
      entry: ['src/distiller.ts'],
      formats: ['es'],
    },
    rollupOptions: {
      output: {
        preserveModulesRoot: '.',
        preserveModules: true
      },
      external: [
        /^lit/,
        /^@ensembl\/ensembl-elements-common/
      ],
    }
  }
});

import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { copyFile, readFile, writeFile } from 'fs/promises';
import { build } from 'vite';

import viteConfig from '../vite.config.ts';

const dirname = fileURLToPath(new URL('.', import.meta.url));
const rootPath = path.resolve(dirname, '..');

const buildDirectoryPath = path.resolve(rootPath, 'dist');
const packageJsonPath = path.resolve(rootPath, 'package.json');
const npmrcPath = path.resolve(rootPath, '.npmrc');

await build({
  ...viteConfig,
  root: rootPath,
});


await copyFile(npmrcPath, path.resolve(buildDirectoryPath, '.npmrc'));

const updatePackageJson = async () => {
  const packageJsonString = await readFile(packageJsonPath, 'utf8');
  const packageJson = JSON.parse(packageJsonString);
  const exports: Record<string, string> = packageJson.exports;

  for (const [key, value] of Object.entries(exports)) {
    if (value.endsWith('.ts')) {
      exports[key] = value.replace(/\.ts$/, '.js');
    }
  }

  const updatedPackageJsonString = JSON.stringify(packageJson, null, 2);
  const outPath = path.resolve(buildDirectoryPath, 'package.json');
  await writeFile(outPath, updatedPackageJsonString);
};

await updatePackageJson();
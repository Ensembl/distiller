import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dirname = fileURLToPath(new URL('.', import.meta.url));
const rootPath = path.resolve(dirname, '..');

const buildDirectoryPath = path.resolve(rootPath, 'dist');

import { execSync } from 'child_process';

const PUBLISH_TOKEN = process.env.PUBLISH_TOKEN;

if (!PUBLISH_TOKEN) {
  const errorMessage = 'The token for publishing the package is missing. Please add it to the .env file';
  console.error(errorMessage);
  process.exit(1);
}

process.chdir(buildDirectoryPath);

try {
  execSync(`npm publish --//gitlab.ebi.ac.uk/api/v4/projects/3500/packages/npm/:_authToken=${PUBLISH_TOKEN}`);
} catch {
  console.error("ERROR: the package has not been published");
}
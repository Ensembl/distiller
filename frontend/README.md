The frontend of Data Distiller is an npm library.

## Installation
The package is published to the Ensembl npm registry on GitLab. It expects the host application to provide `lit` and `@ensembl/ensembl-elements-common`.

```
npm install @ensembl/ensembl-data-distiller
```

## Usage
Import the package, and render the `ens-data-distiller` element with the base url of the Data Distiller api.

```html
<ens-data-distiller api-base-url="/api/distiller"></ens-data-distiller>
```

The element fills the height of its container. It relies on the css custom properties (colours, font weights, gutters) that ensembl-client and `@ensembl/ensembl-elements-common` define.

## Publishing
Update the version in `package.json`, add a `PUBLISH_TOKEN` to the `.env` file (see `.env.template`), then run `npm run build` followed by `npm run publish-lib`.

## Development
For local development, install the dependencies and run `npm run dev`. The playground expects the backend to be running on `http://localhost:8000` (see the backend README).

There also is a Storybook to help with developing components in isolation. Run it with `npm run storybook`.
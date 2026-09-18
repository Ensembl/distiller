# Frontend architecture

Date: 2026-09-18

## Underlying principles

The frontend for data distiller is being built in such a way that it can both be integrated into ensembl-client, and be able to function as a standalone app (there is an expectation that it should be usable outside of ensembl-client). To accommodate this, it is built as a web component. It uses Lit for convenience, and also because we already have Lit-based components integrated into ensembl-client. However, one of the objective is to reduce its own dependencies to a minimum — ideally, limiting them to just Lit — in order to reduce its byte size.
# Contributing to Freehand Digitize

Thanks for helping improve the plugin.

## Before changing code

1. Read [AGENTS.md](AGENTS.md) and
   [CHANGE_PROCEDURE.md](docs/maintainer/CHANGE_PROCEDURE.md).
2. For code, tests, metadata, CI, packaging or catalogs, write a
   `docs/maintainer/PLAN_<TOPIC>.md` and wait for approval.
3. Keep `core/` free of QGIS/Qt imports.

## Environment and checks

```bash
uv sync --frozen
make test
make test-qgis
make pre-release
make docs-check
make release-notes-check
```

On a machine with QGIS, `make test-qgis` auto-detects the interpreter or uses
`QGIS_PYTHON`. Without QGIS, integration tests are skipped.

## Commits and pull requests

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`,
  `chore:`.
- Keep changes scoped; update tests and English documentation.
- UI strings: English source with `QCoreApplication.translate` and the six
  catalogs; edit `scripts/i18n/master_data/<locale>.json`.
- Do not add generated files, build output or secrets.

## Release notes

Release notes live in `docs/releases/notes/vX.Y.Z.md`; see
[docs/releases/README.md](docs/releases/README.md).

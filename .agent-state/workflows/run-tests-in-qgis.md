---
description: How to run the integration suite inside a real QGIS (host or container).
agent: qa_engineer
skills: [testing-standards, freehand-digitizing]
validation: |
  - QGIS is installed (or the container is available)
  - tests/integration is discovered and every test runs
  - no import errors, no skipped integration tests when QGIS is present
---

# Workflow: Run Tests in QGIS

The integration suite exercises the real PyQGIS API: `QgsMapTool` events,
rubber bands, `QgsSnappingUtils`, `QgsVectorLayerUtils.createFeature`, the
attribute form and the plugin lifecycle. Unit tests (`tests/core/`) never need
QGIS.

## Host QGIS

```bash
# from the repository root
QT_QPA_PLATFORM=offscreen PYTHONPATH=.. python3 \
  -m unittest discover -s tests/integration -t . -v

# or through the Makefile (also tolerates a teardown segfault after OK)
make test-qgis
```

The system `python3` must be the one that can `import qgis`. In this workspace
QGIS 4.2.2 is installed for `/usr/bin/python3`.

## Container

```bash
make docker-test   # builds the Dockerfile and runs tests/integration
```

The image is `qgis/qgis:latest`; no pip/uv install is needed because the plugin
has no runtime dependencies.

## Expected output

```
Ran 48 tests in ~1s
OK
```

QGIS may segfault during teardown (`exit 139`) **after** printing `OK`. The
Makefile and CI accept 139 only when the log ends in `OK` and contains no
`FAILED`/`ERROR`. Never ignore any other non-zero exit.

## Troubleshooting

- **`No module named qgis`**: the `python3` in use is not QGIS's interpreter.
  Use the system Python or the container; do not install QGIS with pip.
- **Integration tests are skipped under `make test`**: expected; the uv
  environment has no QGIS. Use `make test-qgis`.
- **`ImportError` for `freehand_digitize`**: run from the repository root with
  `PYTHONPATH=..`.
- **GUI tests crash without a display**: keep `QT_QPA_PLATFORM=offscreen`.
- **A test hangs on a modal dialog**: the fake interface must return a
  `FakeDialog` or `None`; see `tests/integration/fakes.py`.

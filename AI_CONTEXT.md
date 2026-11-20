# Freehand Digitize — Working Context

> Session bundle for AI agents. Canonical rules live in
> [`AGENTS.md`](AGENTS.md); this file summarizes the current state and is reset
> at the start of each session.

## What this plugin is

A QGIS plugin that restores the freehand line/polygon digitizing features of the
classic [`freehandEditing`](https://github.com/vinayan/freehandEditing) plugin
for **QGIS 3.28–4.x** (Qt5/Qt6), without external Python dependencies.

## Current state (2026-11-19)

- Version **2.0.0**; `metadata.txt` validated with `qgis-manage validate --strict`.
- Feature parity restored: tolerance spinbox + persistence, geographic-CRS
  policy, CTRL snapping (first/last vertex), pencil cursor, layer-CRS geometry,
  attribute form, provider defaults, undo command, invalid-geometry prompt,
  layer enablement, secondary-button finish, ESC cancel.
- Freehand reshape (new in 2.0.0): a stroke reshapes the geometries under it;
  a selection filters the targets; one undo command per operation.
- Sampling settings: pixels or layer units (metres/degrees), separate per-unit
  distances, geographic-CRS warning; the tool recovers the options at press.
- Edit-session gating: create/reshape are enabled only while the layer is in
  edit mode; stopping editing cancels the stroke and deactivates the tool.
- Tests: `tests/core/` (no QGIS) + `tests/integration/` (real QGIS 4.2.2);
  the suite is green in both environments.
- QA: `pyproject.toml`/`uv.lock`, Makefile, ruff, flake8, mypy, analyzer,
  qgis-manage, pre-commit, CI, Docker, detect-secrets baseline.
- Agentic system: Agentic Forge vendored in `.agent/`, project state in
  `.agent-state/`, roles in `opencode.json`, config in `forge.toml`.
- Docs: `docs/user/USER_GUIDE.md`, `docs/ARCHITECTURE_EN.md`,
  `docs/maintainer/PLAN_FREEHAND_PARITY.md`,
  `docs/maintainer/FEATURE_PARITY.md`,
  `docs/maintainer/uv_modernization_guide.md`, the maintainer style/commit/
  logging/user-guide conventions and `docs/maintenance/DEVELOPMENT_LOG.md`.
- `make docs-check` validates relative Markdown links (script:
  `scripts/check_docs.py`).

## Architecture

```
core/     pure Python: constants, geometry rules, stroke sampling, settings
gui/      PyQGIS/Qt: freehand tool, creators, sampling dialog, cursor, geometry factory, compat
freehand_plugin.py   wiring: action, spinbox, signals, lifecycle
```

- `core/` has no QGIS/Qt imports.
- `core/settings.py` stores tolerance and sampling options; `core/stroke.py`
  implements pixel/layer thinning.
- `gui/qt_compat.py` centralizes PyQt5/PyQt6 and QGIS enum differences.
- The tool captures the layer at press time and emits
  `geometryFinished(geometry, layer)`; `FeatureCreator` persists the feature and
  `ReshapeCreator` modifies the features under a reshape stroke.

## Commands

```bash
uv sync --frozen
make test            # unit (no QGIS)
make test-qgis       # integration (host QGIS)
make pre-release     # all blocking gates
make zip             # package + validate ZIP
```

## Decisions

- **Spanish UI source + English catalog**; README, CHANGELOG, user guide and
  code/docs are English; internal plans, parity reports and logs may stay
  Spanish. The analyzer `MISSING_I18N` rule stays disabled because catalogs are
  maintained through `make transup`/`make i18n-check`.
- **Edit-session gating**: create/reshape require an active edit session; the
  plugin never calls `startEditing()` and deactivates on `editingStopped`.
- **Lines allow 2 points**; polygons require 3 distinct points before closing.
- **Reshape target**: features under the stroke; a selection restricts the set;
  the raw stroke is used (no tolerance) and the operation is one undo command.
- **Sampling**: pixels (default 1.5) or layer units (separate distances);
  geographic CRS warns that degrees are latitude-dependent.
- **`supportsQt6` is not used**: deprecated by qgis-manage 0.17; QGIS 4 Ready is
  `qgisMaximumVersion = 4.99`.
- Repository: <https://github.com/geociencio/freehand-digitize>; metadata URLs point there.

## Pending

- Tag `v2.0.0` and publish the ZIP.
- Real QGIS 3.28 smoke test (or raise `qgisMinimumVersion`).

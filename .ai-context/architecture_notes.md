# Freehand Digitize — Curated Architecture Notes

> Hand-maintained guidance injected into the context bundle. Keep it short and
> current. Canonical sources: `AGENTS.md`,
> `docs/maintainer/FEATURE_PARITY.md`,
> `docs/maintainer/uv_modernization_guide.md`.

## What this plugin is

A QGIS plugin (Python, PyQt via `qgis.PyQt`) that draws lines and polygons
freehand on the active vector layer, restoring the feature set of the classic
`freehandEditing` plugin for QGIS 3.28–4.x. No external runtime dependencies.
The UI is created programmatically (no `.ui` files, no `.qrc` resources).

## Layout

- `core/` — pure rules: geometry kinds/tolerance, stroke sampling, settings.
  **Must never import `qgis`, `qgis.gui` or Qt.**
- `gui/` — PyQGIS/Qt: `FreehandTool` (QgsMapTool, rubber band, snapping),
  `FeatureCreator` (defaults, attribute form, undo), `cursor`, `geometry_factory`
  and `qt_compat` (PyQt5/PyQt6 shims).
- `freehand_plugin.py` — action, tolerance spinbox, layer enablement, lifecycle.
- `tests/core/` — QGIS-free unit tests; `tests/integration/` — real QGIS tests.

## Data flow

1. `canvasPressEvent` captures the layer and converts the point with
   `toLayerCoordinates()` (layer CRS). CTRL snaps to a vertex through
   `canvas.snappingUtils()`.
2. `StrokeRecorder` thins the stroke by **device pixels** (CRS-independent).
3. `canvasReleaseEvent` builds the geometry in layer coordinates and emits
   `geometryFinished(geometry, layer)`.
4. `FeatureCreator` simplifies with the effective tolerance, validates, opens
   `iface.getFeatureForm()` and adds the feature inside
   `beginEditCommand`/`endEditCommand`.

## Non-negotiable principles

- Core/GUI separation: no QGIS/Qt in `core/`; the unit suite must import it in a
  plain venv.
- Always draw in layer coordinates, never in project coordinates.
- Keep Qt5/Qt6 differences in `gui/qt_compat.py`; import only from `qgis.PyQt`.
- A canvas event must never raise: log with `QgsMessageLog` and warn through
  `iface.messageBar()`.
- User-facing strings are Spanish; code/docs/tests are English.

## Conventions

- Python 3.9 runtime syntax (QGIS 3.28) gated by
  `tests/core/test_python_compat.py`; development/QA uses Python 3.12 via uv.
- Google docstrings, full type annotations, `ruff format` at 100 columns.
- `unittest` only (no pytest); integration tests skip when `qgis` is missing.
- Conventional Commits; `uv.lock` is authoritative.

## Known traps

- `QgsRubberBand` lives in `qgis.gui` in QGIS 4; `QgsSnappingUtils` lives in
  `qgis.core`.
- `QgsMapTool.toLayerCoordinates()` is required for OTF reprojection; using
  `event.mapPoint()` stores the geometry in the project CRS.
- `snapToCurrentLayer()` returns `QgsPointLocator.Match` in QGIS 4 (not a
  `(retval, result)` tuple) and respects the QGIS snapping configuration.
- `QAction` moved to `QtGui` in PyQt6; `Qt.LeftButton` became
  `Qt.MouseButton.LeftButton`.
- `QgsVectorLayerUtils.createFeature()` applies provider defaults and
  constraints; it replaces the old `provider.defaultValue()` loop.
- `qgis-manage` 0.17 warns that `supportsQt6` is deprecated for QGIS 4.

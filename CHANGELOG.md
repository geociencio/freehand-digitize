# Changelog

## Unreleased

### Changed

- English is now the UI source language; the Spanish catalog preserves the
  previous wording, and `pt_BR`, `fr`, `de`, `it` and `id` catalogs are included.
- Release is gated until the 2.0.x portal submissions are resolved.

### Fixed

- Terminal Ctrl snapping now keeps the snapped last vertex even when the cursor
  stops before release.
- Feature difference accepts valid edit-buffer features with negative or zero
  FIDs.
- A non-overlapping cutter no longer creates an empty edit command.
- Difference labels prefer the layer display expression/field.

## 2.0.2 — 2026-11-21

### Fixed

- Residual `RuntimeError` paths when the target layer is deleted during
  creation, reshape, difference or a stroke: guards in `FeatureCreator`,
  `ReshapeCreator`, `FreehandTool` and the plugin completion callbacks.
- The operation is cancelled with a translated warning and no partial edit.

## 2.0.1 — 2026-11-21

### Fixed

- `RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted`
  when the active layer was removed: the plugin now uses `sip.isdeleted`, clears
  the stored reference before disconnecting signals, and reacts to the layer's
  `destroyed` signal.
- Plugin unload no longer fails after the active layer has been deleted.
- The difference pick tool is released if its layer is destroyed.

## 2.0.0 — 2026-11-19

Modern rewrite of the plugin with full functional parity with
[`freehandEditing`](https://github.com/vinayan/freehandEditing) and support for
QGIS 3.28–4.x (Qt5/Qt6).

### Added

- **Freehand reshape** of existing line/polygon features under the stroke, with an
  optional selection filter, multi-feature support and a single undo command.
- **Vertex sampling settings**: choose one vertex every N device pixels or N
  layer units, with separate per-unit distances and a geographic-CRS warning.
- **Feature difference**: subtract a selected or mouse-picked cutter from a target
  feature in one undo command (same layer; cutter untouched).
- Adjustable simplification tolerance (0–5, 3 decimals) in the digitize toolbar,
  persisted in `QgsSettings` with migration of the legacy
  `/freehandEdit/tolerance` key.
- `Ctrl` snapping of the first and last vertex using the QGIS snapping engine.
- Pencil cursor (XPM) with a cross-cursor fallback.
- QGIS attribute form, with click suppression while it is modal.
- Provider defaults through `QgsVectorLayerUtils.createFeature`.
- Edit commands (`beginEditCommand`/`endEditCommand`) so the feature can be
  undone as a single operation.
- Invalid-geometry prompt (“use it anyway?”).
- Action enabled only for editable line/polygon vector layers, synchronised with
  the active layer and with tool changes.
- `core/` (QGIS-free) and `gui/` (PyQGIS) architecture with PyQt5/PyQt6 shims.
- Agentic system (Agentic Forge), unit and integration tests, CI, pre-commit and
  `qgis-manage` packaging.
- Maintainer documentation: architecture, style guide, commit guidelines,
  development log and link checker (`make docs-check`).
- English user guide for features and workflows.
- Internationalization: `QCoreApplication.translate` integration, an English
  catalog (`i18n/freehand_digitize_en.ts/.qm`), locale detection with Qt
  fallback, and `make transup`/`make i18n-check`.

### Changed

- Create/reshape actions are enabled only while the active layer is in edit
  mode; stopping editing cancels an in-progress stroke. The plugin no longer
  starts edit sessions automatically.
- The stroke is stored in layer coordinates (`toLayerCoordinates`), not in the
  project CRS; the risk of geometries in the wrong CRS is removed.
- Stroke sampling uses device-pixel distance, not `mapUnitsPerPixel` over layer
  coordinates.
- The secondary button finishes the stroke (original behaviour) instead of
  cancelling it; `Esc` still cancels.
- Simplification is no longer fixed at 2 px: it uses the configured tolerance.
- Invalid geometries are no longer fixed silently: the user is asked.

### Fixed

- Features created in the project CRS when the layer used a different CRS.
- Missing provider defaults and attribute form.
- Missing undo command for the created feature.
- Action always enabled on point or non-editable layers.
- `QAction` imported in a non-portable way between PyQt5/PyQt6.

### Removed

- Dependency on the upstream PyQt4/QGIS 2 code; it is kept as a reference in
  `freehandEditing/` (excluded from the ZIP).
- `supportsQt6` in `metadata.txt` (deprecated with qgis-manage 0.17; QGIS 4
  Ready is marked with `qgisMaximumVersion >= 4.0`).

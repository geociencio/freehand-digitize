---
name: project-context
description: Purpose, architecture and current state of the Freehand Digitize QGIS plugin. Use when starting a task, summarizing the project or explaining how the drawing pipeline works.
---

# Freehand Digitize Project Context

## What it is

A QGIS plugin that draws **lines and polygons freehand** on the active vector
layer. It is a modernized derivative of the classic
[`freehandEditing`](https://github.com/vinayan/freehandEditing) plugin for
QGIS 3.28–4.x (Qt5/Qt6), with no external Python dependencies.

## Current release

- Version **2.0.0** (`metadata.txt`), QGIS 3.28–4.99, GPL-2.0.
- Feature parity with the upstream plugin plus a Core/GUI split, tests, CI and
  an agentic system.

## Layout

```
freehand_plugin.py   action, tolerance spinbox, signals, lifecycle
core/                QGIS-agnostic: constants, geometry rules, stroke, settings
gui/                 PyQGIS/Qt: tool, feature creator, cursor, factory, compat
tests/core/          unit tests (no QGIS)
tests/integration/   real-QGIS tests (skipped when qgis is missing)
docs/maintainer/     plan, parity report, uv guide
.agent/              Agentic Forge framework (vendored)
.agent-state/        project state, overlay skills and workflows
```

## Drawing pipeline

1. The user activates **Dibujo a mano alzada** on an editable line/polygon layer.
2. `FreehandTool.canvasPressEvent` captures the layer and converts the pointer
   with `toLayerCoordinates()`; with CTRL it snaps to a vertex.
3. `StrokeRecorder` keeps the vertices in layer coordinates and thins them by
   device-pixel distance.
4. On release (any button) it emits `geometryFinished(geometry, layer)`.
5. `FeatureCreator` simplifies with the effective tolerance, validates the
   geometry, opens the attribute form (unless disabled in QGIS) and inserts the
   feature through `QgsVectorLayerUtils.createFeature` inside an undo command.
6. `FreehandDigitizePlugin` persists the tolerance in `QgsSettings` and enables
   or disables the action according to the active layer.

## Key rules

- `core/` never imports `qgis` or Qt; the unit suite runs in a plain uv venv.
- The stroke is always in **layer CRS**; `event.mapPoint()` is project CRS.
- Qt5/Qt6 differences live only in `gui/qt_compat.py`.
- The UI is Spanish; code, tests and technical docs are English.
- `make test` is QGIS-free; `make test-qgis` is the real GUI gate.

## Canonical sources

- Root [`AGENTS.md`](../../../AGENTS.md) — agent rules and gates.
- [`docs/maintainer/FEATURE_PARITY.md`](../../../docs/maintainer/FEATURE_PARITY.md)
  — upstream comparison.
- [`AI_CONTEXT.md`](../../../AI_CONTEXT.md) — session state.
- `.agent-state/task.md` / `.agent-state/next_steps.md` — live work.

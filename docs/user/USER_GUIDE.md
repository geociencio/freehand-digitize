# Freehand Digitize — User Guide

> Version 2.0.0 | Last Updated: 2026-11-19
>
> Feature and workflow guide for the Freehand Digitize QGIS plugin. For a quick
> start see [README.md](../../README.md); for the design see
> [ARCHITECTURE_EN.md](../ARCHITECTURE_EN.md).

## Contents

1. [What the plugin does](#1-what-the-plugin-does)
2. [Requirements](#2-requirements)
3. [Installation](#3-installation)
4. [Drawing a feature](#4-drawing-a-feature)
5. [The digitize toolbar](#5-the-digitize-toolbar)
6. [Snapping with Ctrl](#6-snapping-with-ctrl)
7. [Attribute form and defaults](#7-attribute-form-and-defaults)
8. [Undo, cancel and invalid geometries](#8-undo-cancel-and-invalid-geometries)
9. [CRS behaviour](#9-crs-behaviour)
10. [Keyboard and mouse reference](#10-keyboard-and-mouse-reference)
11. [Troubleshooting](#11-troubleshooting)
12. [Known limitations](#12-known-limitations)

---

## 1. What the plugin does

Freehand Digitize lets you draw **lines and polygons** by dragging the mouse over
the map. On release, the stroke becomes a feature in the active vector layer.

It restores the feature set of the classic `freehandEditing` plugin:

- freehand line and polygon drawing with a pencil cursor;
- adjustable simplification tolerance, persisted between sessions;
- `Ctrl` snapping of the first and last vertex;
- QGIS attribute form, provider defaults and a single undo command;
- a prompt when the resulting geometry is invalid;
- the action is enabled only for editable line/polygon layers.

The UI is available in Spanish (source language) and English. With an English
QGIS locale the action reads **Freehand digitize**; with a Spanish locale it
reads **Dibujo a mano alzada**. This guide uses the English labels and shows the
Spanish one where useful.

---

## 2. Requirements

- **QGIS 3.28 or newer**, including QGIS 4.x (Qt5/Qt6).
- No external Python packages. QGIS provides PyQt, GDAL and GEOS.
- A vector layer of type **line** or **polygon** that supports editing.

---

## 3. Installation

### From the ZIP

1. Download `dist/freehand_digitize.<version>.zip`.
2. In QGIS open **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select the ZIP and enable **Freehand Digitize** in the installed plugins
   list.

### From the repository (development)

```bash
uv run qgis-manage deploy --no-compile --qgis-version 4
```

Alternatively, copy the plugin folder to
`~/.local/share/QGIS/QGIS4/profiles/default/python/plugins/freehand_digitize`.

After installation, the action appears in the **Digitize** toolbar and in
**Vector → Freehand Digitize**.

---

## 4. Drawing a feature

1. Select the **line or polygon layer** where the feature must be created.
2. Start editing if needed; the tool also starts the edit session when it is
   activated.
3. Click **Freehand digitize** (Spanish: **Dibujo a mano alzada**) in the Digitize
   toolbar or choose **Vector → Freehand Digitize**.
4. Drag with the **left mouse button** to draw the stroke.
5. Release to finish. The feature is added to the active layer.

A polygon is closed automatically: you only need three distinct points, and the
first point is repeated to build the ring. A line needs at least two points.

If the stroke is too short (fewer points than the geometry needs), nothing is
created and the tool stays active.

### While drawing

- The **rubber band** follows the pointer: red with a translucent fill for
  polygons, a red line for lines.
- Vertices are thinned by device-pixel distance, so the stroke does not become
  excessively dense.
- Moving the pointer does not create intermediate features; only the release
  finishes the operation.

---

## 5. The digitize toolbar

The tolerance spin box sits in the QGIS **Digitize** toolbar, next to the
standard digitizing tools.

| Control | Behaviour |
| :--- | :--- |
| **Tolerance** (`0.000`–`5.000`) | Simplification tolerance in layer units. `0` disables simplification. |
| Decimals / step | 3 decimals, step `0.1`. |
| Persistence | The value is stored in QGIS settings (`freehand_digitize/tolerance`). |
| Legacy migration | The old `freehandEdit/tolerance` value is imported on first use. |
| Geographic CRS | The spin box is disabled and the effective tolerance is `0`. |

The simplification is applied before the feature is validated and inserted. If
the simplified geometry is empty, the original stroke is kept.

---

## 6. Snapping with Ctrl

Hold **Ctrl** when you press the mouse button to snap the **first vertex**, and
keep it held when you release to snap the **last vertex**.

The plugin uses the QGIS snapping engine:

1. it first tries the current layer (`snapToCurrentLayer`, vertex type);
2. if there is no match, it tries the configured background layers
   (`snapToMap`);
3. if there is still no match, the free pointer position is used.

Snapping respects the QGIS snapping configuration (mode, tolerance and enabled
layers). If snapping is disabled or the tolerance is too small, no vertex is
snapped and the stroke starts/ends at the pointer.

This is an improvement over the original plugin, which only snapped the first
point.

---

## 7. Attribute form and defaults

When QGIS is configured to **enter attribute values** after digitizing, the
attribute form opens before the feature is added.

- **Accept** adds the feature with the edited attributes.
- **Cancel** discards the feature and removes the pending undo command.
- If the form is disabled in QGIS options, the feature is added directly.

Provider default values, expressions and constraints are applied through
`QgsVectorLayerUtils.createFeature`, so required fields and defaults behave like
the standard QGIS digitizing tools.

While the form is open, canvas clicks are ignored so a stray click cannot start
a new stroke.

---

## 8. Undo, cancel and invalid geometries

| Situation | Result |
| :--- | :--- |
| Feature created | One undo command; `Ctrl+Z` removes the feature. |
| Form cancelled | No feature and no empty undo command. |
| Layer rejects the feature | The command is destroyed and a warning is shown. |
| Invalid geometry | A dialog asks whether to use it anyway. |
| Stroke cancelled with `Esc` | The rubber band is cleared; the tool stays active. |

The invalid-geometry dialog is intentional: the plugin does not silently call
`makeValid()`. Choose **No** to abandon the feature and redraw the stroke.

---

## 9. CRS behaviour

The stroke is recorded with `toLayerCoordinates`, so the geometry is created in
the **layer CRS**, not in the project CRS. This is safe when the layer and the
project use different CRSs (on-the-fly reprojection).

The tolerance is expressed in **layer units**. For a geographic CRS (degrees),
the spin box is disabled and `0` is used because a degree-based tolerance would
be meaningless.

---

## 10. Keyboard and mouse reference

| Input | Action |
| :--- | :--- |
| Left button + drag | Draw the stroke. |
| Release left button | Finish and create the feature. |
| Release secondary/middle button | Finish the stroke early (halt the drag). |
| `Ctrl` at press | Snap the first vertex. |
| `Ctrl` at release | Snap the last vertex. |
| `Esc` with a stroke | Cancel the stroke, keep the tool active. |
| `Esc` with no stroke | Deactivate the tool. |

---

## 11. Troubleshooting

| Symptom | Cause / fix |
| :--- | :--- |
| The action is disabled | The active layer is not a valid, editable line/polygon layer. Select one or start editing. |
| “Select the layer where you want to draw first.” | No active layer. Select the target layer first. |
| “This tool only draws on line or polygon layers.” | Point layers are not supported. |
| “Layer ‘…’ could not be put in edit mode.” | The layer is read-only or the provider rejected the edit session. |
| The tolerance spin box is disabled | The layer uses a geographic CRS; tolerance is forced to 0. |
| The attribute form does not open | QGIS is configured to skip the form, or the layer has no editable fields. |
| The feature is not where expected | Check the layer CRS and that you used the layer, not the project, as the target. |
| `Ctrl` does not snap | QGIS snapping is disabled, no target is within tolerance, or the snapping mode excludes the layer. |

Technical messages are written to the QGIS message log with the
**Freehand Digitize** tag. Open **View → Panels → Log Messages** to inspect them.

---

## 12. Known limitations

- **UI languages**: Spanish is the source language; an English catalog is
  included and additional catalogs can be added under `i18n/`.
- **Snapping depends on QGIS settings**; the plugin does not override them.
- **No background processing**: the drawing path is interactive and synchronous.
- **Repository** is <https://github.com/geociencio/freehand-digitize>; the upstream `freehandEditing` project is
  credited as the origin.
- **No screenshots** are bundled with this guide yet; if you add them, follow the
  [user guide conventions](../maintainer/USER_GUIDE_CONVENTIONS.md).

---

## Related documents

- [README.md](../../README.md) — quick start and installation.
- [ARCHITECTURE_EN.md](../ARCHITECTURE_EN.md) — technical design.
- [DOCS_STYLE_GUIDE.md](../maintainer/DOCS_STYLE_GUIDE.md) — documentation rules.
- [LICENSE](../../LICENSE) — GPL-2.0.

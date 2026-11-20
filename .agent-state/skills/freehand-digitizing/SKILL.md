---
name: freehand-digitizing
description: Domain knowledge for freehand digitizing in PyQGIS (layer-CRS strokes, CTRL snapping, rubber bands, feature defaults, attribute form and undo). Use when changing the map tool, the feature creator or the parity behaviour of freehandEditing.
---

# Freehand Digitizing in PyQGIS

## When to use this skill

- Changing `gui/freehand_tool.py`, `gui/feature_creator.py` or
  `gui/geometry_factory.py`.
- Reproducing or checking a `freehandEditing` behavior.
- Debugging misplaced geometries, snapping or attribute-form issues.

## Upstream capability map

| Capability | Upstream | Where it lives now |
| :--- | :--- | :--- |
| Freehand line/polygon | `freehandeditingtool.py` | `FreehandTool` |
| Pencil cursor (XPM) | `freehandeditingtool.py:21-40` | `gui/cursor.py` |
| Layer-CRS points | `toLayerCoordinates()` | `FreehandTool.canvasPressEvent` |
| CTRL snapping | `QgsMapCanvasSnapper` | `canvas.snappingUtils()` |
| Tolerance spinbox + settings | `freehandediting.py:59-90` | `FreehandDigitizePlugin` + `core/settings.py` |
| Geometric simplification | `geom.simplify(tolerance)` | `FeatureCreator._simplify` |
| Validity prompt | `validateGeometry()` + QMessageBox | `FeatureCreator._validate` |
| Provider defaults | `provider.defaultValue()` | `QgsVectorLayerUtils.createFeature` |
| Attribute form | `iface.getFeatureForm().exec_()` | `FeatureCreator._edit_attributes` |
| Undo command | `beginEditCommand` | `FeatureCreator._insert_feature` |
| Layer enablement | `toggle()` | `FreehandDigitizePlugin._update_ui_state` |

The full matrix is in
[`docs/maintainer/FEATURE_PARITY.md`](../../../docs/maintainer/FEATURE_PARITY.md).

## PyQGIS recipes

### Layer coordinates (OTF safe)

```python
device = event.pos()
map_point = event.mapPoint()                       # canvas/project CRS
layer_point = self.toLayerCoordinates(layer, device)  # layer CRS
```

Always store and build the geometry with `layer_point`; use `map_point` only for
the rubber band.

### Snap to a vertex (QGIS 3.30+/4)

```python
snapping = self.canvas.snappingUtils()
match = snapping.snapToCurrentLayer(device_point, SNAP_VERTEX)
if not match.isValid():
    match = snapping.snapToMap(device_point)
if match.isValid():
    snapped_map = match.point()
    snapped_layer = self.toLayerCoordinates(layer, snapped_map)
```

`SNAP_VERTEX` is resolved in `gui/qt_compat.py` (`QgsPointLocator.Type.Vertex`
with a flat fallback). `snapToCurrentLayer`/`snapToMap` return
`QgsPointLocator.Match`, not a `(retval, result)` tuple.

### Rubber band

```python
rubber = QgsRubberBand(canvas, RUBBERBAND_POLYGON)
rubber.setColor(QColor(255, 0, 0, 63))
rubber.setWidth(2)
rubber.addPoint(map_point)
```

`QgsRubberBand` is imported from `qgis.gui` in QGIS 4. Create one per stroke and
call `reset()` when finished or cancelled.

### Create the feature

```python
layer.beginEditCommand(EDIT_COMMAND_TEXT)
feature = QgsVectorLayerUtils.createFeature(layer, geometry=simplified)
# optional: iface.getFeatureForm(layer, feature).exec() with setIgnoreClick
layer.addFeature(feature)
layer.endEditCommand()
```

On cancel/failure call `layer.destroyEditCommand()` so no empty undo command is
left behind.

### Attribute form + clicks

Set `tool.setIgnoreClick(True)` before `dialog.exec()` and `False` afterwards so
canvas clicks during the modal cannot start a new stroke.

## Pitfalls

- **Project vs layer CRS**: `event.mapPoint()` is the project CRS; using it
  silently creates entities in the wrong CRS when the layer uses another one.
- **Snapping config**: CTRL snapping respects QGIS's snapping mode/tolerance. If
  there is no match, fall back to the free point; do not force project settings.
- **Pixel sampling**: compare device-pixel distances, not layer distances.
  `mapUnitsPerPixel` is in project units and is meaningless for a differently
  projected layer.
- **Polygon ring**: close the ring explicitly and require three distinct points;
  `fromPolygonXY` expects a list of rings.
- **Secondary button**: the upstream behavior is "halt the drag", i.e. release
  finishes the stroke. Keep `Esc` for cancellation.
- **Geographic CRS**: use tolerance 0; a 0–5 tolerance in degrees is meaningless.
- **Enums**: `QAction`, `Qt.MouseButton`, `Qgis.GeometryType` and
  `QgsPointLocator.Type` differ between Qt5 and Qt6 — always go through
  `gui/qt_compat.py`.
- **Layer capture**: capture the layer on press and finish the feature there even
  if the active layer changes mid-stroke.

## Verification

```bash
make test-qgis   # QGIS 4 integration: tool, snapping, creator, plugin
make test        # pure unit rules
```

Relevant tests: `tests/integration/test_freehand_tool.py`,
`tests/integration/test_feature_creator.py`,
`tests/integration/test_plugin.py`.

---
description: Headless QGIS 4 smoke test of Freehand Digitize (load the plugin, draw a line, create the feature).
agent: qa_engineer
skills: [testing-standards, freehand-digitizing, qgis-core]
validation: |
  - The plugin package imports with QGIS 4 / PyQt6
  - FreehandTool draws a line and emits geometryFinished
  - The feature is added to an in-memory layer with the expected CRS
---

# Workflow: Smoke test in QGIS 4 (headless)

Fast end-to-end check without opening the QGIS GUI. It uses the same APIs as the
integration suite but as a single copy-paste script, useful after a risky change.

## Steps

1. Ensure the environment can import QGIS:

   ```bash
   QT_QPA_PLATFORM=offscreen PYTHONPATH=.. python3 -c \
     "from qgis.core import Qgis; print(Qgis.version())"
   ```

2. Run the smoke script from the repository root:

   ```bash
   QT_QPA_PLATFORM=offscreen PYTHONPATH=.. python3 - <<'PY'
   from qgis.core import QgsApplication, QgsVectorLayer, QgsRectangle, QgsCoordinateReferenceSystem
   app = QgsApplication([], False); app.initQgis()

   from qgis.gui import QgsMapCanvas
   from tests.integration.fakes import (
       MOVE, PRESS, RELEASE, FakeIface, make_canvas, make_layer, mouse_event,
   )
   from freehand_digitize.freehand_plugin import FreehandDigitizePlugin

   layer = make_layer("LineString")
   canvas = make_canvas(layer)
   iface = FakeIface(canvas, layer)
   plugin = FreehandDigitizePlugin(iface)
   plugin.initGui()
   plugin._on_action_triggered(True)

   tool = plugin.tool
   tool.canvasPressEvent(mouse_event(canvas, PRESS, 100, 100))
   tool.canvasMoveEvent(mouse_event(canvas, MOVE, 150, 150))
   tool.canvasMoveEvent(mouse_event(canvas, MOVE, 200, 200))
   tool.canvasReleaseEvent(mouse_event(canvas, RELEASE, 200, 200))

   assert layer.featureCount() == 1, layer.featureCount()
   feature = next(layer.getFeatures())
   assert not feature.geometry().isEmpty()
   print("SMOKE OK:", feature.geometry().asWkt())
   plugin.unload(); iface.close(); canvas.deleteLater()
   PY
   ```

3. Optional: repeat with a polygon layer and with a layer whose CRS differs from
   the canvas (`make_layer("LineString", crs="EPSG:3857")` + a matching extent);
   verify the coordinates are in the layer CRS, not the canvas CRS.

4. For the full matrix (snapping, attribute form, undo, invalid geometry) run:

   ```bash
   make test-qgis
   ```

## Expected result

- `SMOKE OK: LineString (...)` with two or more points.
- `layer.featureCount() == 1` and the geometry in the layer CRS.
- No Qt/PyQt import error and no exception in the QGIS message log.

If the smoke test fails, inspect `QgsMessageLog` (tag `Freehand Digitize`) and
run the integration tests with `-v` to locate the failing step.

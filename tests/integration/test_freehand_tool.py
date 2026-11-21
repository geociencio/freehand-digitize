"""Integration tests for the freehand map tool."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis


@requires_qgis
class TestFreehandTool(unittest.TestCase):
    """Stroke lifecycle, rubber band, snapping and cancellation."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from qgis.core import QgsSnappingConfig, QgsTolerance
        from qgis.PyQt import sip
        from qgis.PyQt.QtCore import QObject

        from freehand_digitize.gui.freehand_tool import MODE_RESHAPE, FreehandTool
        from freehand_digitize.gui.qt_compat import KEY_CONTROL, KEY_ESCAPE, RIGHT_BUTTON
        from tests.integration.fakes import (
            MOVE,
            PRESS,
            RELEASE,
            FakeIface,
            add_polyline,
            device_point,
            make_canvas,
            make_layer,
            mouse_event,
        )

        cls.sip = sip
        cls.QObject = QObject
        cls.QgsSnappingConfig = QgsSnappingConfig
        cls.QgsTolerance = QgsTolerance
        cls.FreehandTool = FreehandTool
        cls.MODE_RESHAPE = MODE_RESHAPE
        cls.KEY_CONTROL = KEY_CONTROL
        cls.KEY_ESCAPE = KEY_ESCAPE
        cls.RIGHT_BUTTON = RIGHT_BUTTON
        cls.MOVE = MOVE
        cls.PRESS = PRESS
        cls.RELEASE = RELEASE
        cls.FakeIface = FakeIface
        cls.add_polyline = staticmethod(add_polyline)
        cls.device_point = staticmethod(device_point)
        cls.make_canvas = staticmethod(make_canvas)
        cls.make_layer = staticmethod(make_layer)
        cls.mouse_event = staticmethod(mouse_event)

    def setUp(self) -> None:
        """Create a line layer, canvas, fake interface and tool."""
        self.layer = self.make_layer("LineString")
        self.layer.startEditing()
        self.canvas = self.make_canvas(self.layer)
        self.iface = self.FakeIface(self.canvas, self.layer)
        self.tool = self.FreehandTool(self.canvas, self.iface)
        self.emitted: list[object] = []
        self.tool.geometryFinished.connect(self._capture)
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        """Release the canvas and window."""
        self.iface.close()
        self.canvas.deleteLater()

    def _capture(self, geometry, layer) -> None:
        """Store the emitted geometry and layer."""
        self.emitted.append((geometry, layer))

    def _draw(
        self,
        points: list[tuple[float, float]],
        release_button=None,
    ) -> None:
        """Simulate a press/move/release stroke."""
        first = points[0]
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, first[0], first[1]))
        for x, y in points[1:]:
            self.tool.canvasMoveEvent(
                self.mouse_event(self.canvas, self.MOVE, x, y, self.RIGHT_BUTTON)
            )
        last = points[-1]
        release = (
            self.mouse_event(self.canvas, self.RELEASE, last[0], last[1], release_button)
            if release_button is not None
            else self.mouse_event(self.canvas, self.RELEASE, last[0], last[1])
        )
        self.tool.canvasReleaseEvent(release)

    def test_line_stroke_emits_geometry(self) -> None:
        """A stroke emits a line in layer coordinates."""
        self._draw([(100, 100), (150, 150), (200, 200)])
        self.assertEqual(len(self.emitted), 1)
        geometry, layer = self.emitted[0]
        self.assertIs(layer, self.layer)
        self.assertFalse(geometry.isEmpty())
        self.assertEqual(len(geometry.asPolyline()), 3)

    def test_polygon_stroke_is_closed(self) -> None:
        """A polygon stroke closes the ring before emitting."""
        polygon_layer = self.make_layer("Polygon")
        polygon_layer.startEditing()
        self.iface.setActiveLayer(polygon_layer)
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        self.tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 200, 100))
        self.tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 200, 200))
        self.tool.canvasReleaseEvent(self.mouse_event(self.canvas, self.RELEASE, 200, 200))
        self.assertEqual(len(self.emitted), 1)
        rings = self.emitted[0][0].asPolygon()
        self.assertEqual(len(rings[0]), 4)
        self.assertEqual(rings[0][0], rings[0][-1])

    def test_tool_uses_the_layer_sampling_store(self) -> None:
        """A layer-unit threshold thins points even when the screen delta is large."""
        from freehand_digitize.core.constants import (
            SAMPLE_UNIT_LAYER,
            SAMPLING_LAYER_KEY,
            SAMPLING_UNIT_KEY,
        )
        from freehand_digitize.core.settings import SamplingStore
        from tests.mocks.settings import FakeSettings

        store = SamplingStore(
            FakeSettings(
                {
                    SAMPLING_UNIT_KEY: SAMPLE_UNIT_LAYER,
                    SAMPLING_LAYER_KEY: 1000.0,
                }
            )
        )
        tool = self.FreehandTool(self.canvas, self.iface, sampling_store=store)
        emitted = []
        tool.geometryFinished.connect(lambda geometry, layer: emitted.append(geometry))
        tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 200, 200))
        tool.canvasReleaseEvent(self.mouse_event(self.canvas, self.RELEASE, 200, 200))
        self.assertFalse(emitted)

    def test_press_after_layer_deleted_warns(self) -> None:
        """A deleted active layer is rejected without a traceback."""
        doomed = self.QObject()
        self.sip.delete(doomed)
        self.iface.setActiveLayer(doomed)
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        self.assertFalse(self.emitted)
        self.assertTrue(self.iface.messages.warnings)
        self.iface.setActiveLayer(self.layer)

    def test_press_without_edit_session_warns_and_emits_nothing(self) -> None:
        """The tool never starts editing on its own."""
        self.layer.rollBack()
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        self.tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 150, 150))
        self.tool.canvasReleaseEvent(self.mouse_event(self.canvas, self.RELEASE, 150, 150))
        self.assertFalse(self.emitted)
        self.assertFalse(self.layer.isEditable())
        self.assertTrue(self.iface.messages.warnings)

    def test_reshape_mode_emits_an_open_line(self) -> None:
        """Reshape mode emits a line even on a polygon layer."""
        polygon_layer = self.make_layer("Polygon")
        polygon_layer.startEditing()
        self.iface.setActiveLayer(polygon_layer)
        tool = self.FreehandTool(self.canvas, self.iface, mode=self.MODE_RESHAPE)
        emitted = []
        tool.geometryFinished.connect(lambda geometry, layer: emitted.append(geometry))
        tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 150, 150))
        tool.canvasReleaseEvent(self.mouse_event(self.canvas, self.RELEASE, 150, 150))
        self.assertEqual(len(emitted), 1)
        self.assertEqual(len(emitted[0].asPolyline()), 2)

    def test_short_stroke_is_ignored(self) -> None:
        """A polygon with fewer than three points emits nothing."""
        polygon_layer = self.make_layer("Polygon")
        polygon_layer.startEditing()
        self.iface.setActiveLayer(polygon_layer)
        self._draw([(100, 100), (150, 150)])
        self.assertEqual(self.emitted, [])
        self.assertFalse(self.tool.is_drawing)

    def test_secondary_release_finishes_the_stroke(self) -> None:
        """A secondary button release halts the drag (upstream behaviour)."""
        self._draw([(100, 100), (150, 150), (200, 200)], release_button=self.RIGHT_BUTTON)
        self.assertEqual(len(self.emitted), 1)

    def test_ignore_clicks_blocks_the_stroke(self) -> None:
        """Clicks are ignored while a modal dialog is open."""
        self.tool.setIgnoreClick(True)
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        self.assertFalse(self.tool.is_drawing)
        self.tool.setIgnoreClick(False)

    def test_escape_cancels_the_stroke(self) -> None:
        """Escape discards the current stroke without emitting."""
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        self.tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 150, 150))
        self.tool.keyPressEvent(SimpleNamespace(key=lambda: self.KEY_ESCAPE))
        self.assertFalse(self.tool.is_drawing)
        self.assertEqual(self.emitted, [])

    def test_deactivate_cancels_the_stroke(self) -> None:
        """Switching tools discards the stroke."""
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        self.tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 150, 150))
        self.tool.deactivate()
        self.assertFalse(self.tool.is_drawing)
        self.assertEqual(self.emitted, [])

    def test_point_layer_is_rejected(self) -> None:
        """Point layers are not supported."""
        point_layer = self.make_layer("Point")
        self.iface.setActiveLayer(point_layer)
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        self.assertFalse(self.tool.is_drawing)
        self.assertTrue(self.iface.messages.warnings)

    def test_ctrl_snaps_the_first_vertex(self) -> None:
        """CTRL snaps the start point to an existing vertex."""
        self.add_polyline(self.layer, [(5.0, 5.0), (6.0, 6.0)])
        snapping = self.canvas.snappingUtils()
        snapping.setCurrentLayer(self.layer)
        config = snapping.config()
        config.setEnabled(True)
        config.setMode(self.QgsSnappingConfig.SnappingMode.ActiveLayer)
        config.setType(self.QgsSnappingConfig.SnappingType.Vertex)
        config.setTolerance(20)
        config.setUnits(self.QgsTolerance.Pixels)
        snapping.setConfig(config)

        x, y = self.device_point(self.canvas, (5.0, 5.0))
        self.tool.keyPressEvent(SimpleNamespace(key=lambda: self.KEY_CONTROL))
        self.tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, x + 3, y + 3))
        self.tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 300, 300))
        self.tool.canvasReleaseEvent(self.mouse_event(self.canvas, self.RELEASE, 300, 300))

        self.assertEqual(len(self.emitted), 1)
        first, last = self.emitted[0][0].asPolyline()[0], self.emitted[0][0].asPolyline()[-1]
        self.assertAlmostEqual(first.x(), 5.0, places=3)
        self.assertAlmostEqual(first.y(), 5.0, places=3)
        self.assertNotAlmostEqual(last.x(), 5.0, places=3)


if __name__ == "__main__":
    unittest.main()

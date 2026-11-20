"""Integration tests for the plugin entry point."""

from __future__ import annotations

import unittest

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis


@requires_qgis
class TestFreehandDigitizePlugin(unittest.TestCase):
    """GUI wiring, layer enablement and end-to-end feature creation."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from freehand_digitize.freehand_plugin import FreehandDigitizePlugin
        from tests.integration.fakes import (
            MOVE,
            PRESS,
            RELEASE,
            FakeIface,
            make_canvas,
            make_layer,
            mouse_event,
        )

        cls.Plugin = FreehandDigitizePlugin
        cls.FakeIface = FakeIface
        cls.MOVE = MOVE
        cls.PRESS = PRESS
        cls.RELEASE = RELEASE
        cls.make_canvas = staticmethod(make_canvas)
        cls.make_layer = staticmethod(make_layer)
        cls.mouse_event = staticmethod(mouse_event)

    def setUp(self) -> None:
        """Create the layer, canvas, fake interface and initialised plugin."""
        self.layer = self.make_layer("LineString")
        self.canvas = self.make_canvas(self.layer)
        self.iface = self.FakeIface(self.canvas, self.layer)
        self.plugin = self.Plugin(self.iface)
        self.plugin.initGui()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        """Unload the plugin and release the widgets."""
        if self.plugin.action is not None:
            self.plugin.unload()
        self.iface.close()
        self.canvas.deleteLater()

    def test_init_creates_action_and_tool(self) -> None:
        """The action, spinbox and tool are created and wired."""
        self.assertIsNotNone(self.plugin.action)
        self.assertIsNotNone(self.plugin.spinbox)
        self.assertIsNotNone(self.plugin.tool)
        self.assertTrue(self.plugin.action.isEnabled())
        self.assertTrue(self.plugin.action.isCheckable())

    def test_action_disabled_for_point_layer(self) -> None:
        """Point layers disable the action."""
        self.iface.setActiveLayer(self.make_layer("Point"))
        self.assertFalse(self.plugin.action.isEnabled())

    def test_action_disabled_without_a_layer(self) -> None:
        """No active layer disables the action."""
        self.iface.setActiveLayer(None)
        self.assertFalse(self.plugin.action.isEnabled())

    def test_spinbox_disabled_for_geographic_crs(self) -> None:
        """Geographic layers disable the tolerance spinbox."""
        self.assertFalse(self.plugin.spinbox.isEnabled())
        projected = self.make_layer("LineString", crs="EPSG:3857")
        self.iface.setActiveLayer(projected)
        self.assertTrue(self.plugin.spinbox.isEnabled())

    def test_effective_tolerance_is_zero_for_geographic(self) -> None:
        """The effective tolerance honours the geographic CRS policy."""
        self.plugin.spinbox.blockSignals(True)
        self.plugin.spinbox.setValue(2.5)
        self.plugin.spinbox.blockSignals(False)
        self.assertEqual(self.plugin._effective_tolerance(self.layer), 0.0)

    def test_effective_tolerance_for_projected_layer(self) -> None:
        """Projected layers keep the configured tolerance."""
        projected = self.make_layer("LineString", crs="EPSG:3857")
        self.plugin.spinbox.blockSignals(True)
        self.plugin.spinbox.setValue(1.5)
        self.plugin.spinbox.blockSignals(False)
        self.assertEqual(self.plugin._effective_tolerance(projected), 1.5)

    def test_activate_tool_starts_editing(self) -> None:
        """Activating the action installs the tool and starts editing."""
        self.plugin._on_action_triggered(True)
        self.assertIs(self.canvas.mapTool(), self.plugin.tool)
        self.assertTrue(self.layer.isEditable())
        self.assertTrue(self.plugin.action.isChecked())

    def test_end_to_end_stroke_creates_a_feature(self) -> None:
        """A stroke through the tool is stored in the active layer."""
        self.plugin._on_action_triggered(True)
        tool = self.plugin.tool
        tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 150, 150))
        tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 200, 200))
        tool.canvasReleaseEvent(self.mouse_event(self.canvas, self.RELEASE, 200, 200))
        self.assertEqual(self.layer.featureCount(), 1)
        feature = next(self.layer.getFeatures())
        self.assertFalse(feature.geometry().isEmpty())

    def test_unload_removes_everything(self) -> None:
        """Unloading releases actions, tool and toolbar widgets."""
        tool = self.plugin.tool
        self.plugin.unload()
        self.assertIsNone(self.plugin.action)
        self.assertIsNone(self.plugin.tool)
        self.assertIsNone(self.plugin.spinbox)
        self.assertIsNot(self.canvas.mapTool(), tool)


if __name__ == "__main__":
    unittest.main()

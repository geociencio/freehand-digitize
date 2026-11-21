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
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY
        from qgis.PyQt import sip
        from qgis.PyQt.QtCore import QCoreApplication

        from freehand_digitize.freehand_plugin import FreehandDigitizePlugin
        from tests.integration.fakes import (
            MOVE,
            PRESS,
            RELEASE,
            FakeIface,
            device_point,
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
        cls.sip = sip
        cls.QCoreApplication = QCoreApplication
        cls.QgsFeature = QgsFeature
        cls.QgsGeometry = QgsGeometry
        cls.QgsPointXY = QgsPointXY
        cls.device_point = staticmethod(device_point)
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

    def _destroy_layer(self, layer) -> None:
        """Delete *layer* after releasing canvas references."""
        tool = self.canvas.mapTool()
        if tool is not None:
            self.canvas.unsetMapTool(tool)
        self.canvas.setLayers([])
        self.canvas.setCurrentLayer(None)
        self.sip.delete(layer)
        self.QCoreApplication.processEvents()

    def test_init_creates_action_and_tool(self) -> None:
        """The action, spinbox and tool are created and wired."""
        self.assertIsNotNone(self.plugin.action)
        self.assertIsNotNone(self.plugin.spinbox)
        self.assertIsNotNone(self.plugin.tool)
        self.assertFalse(self.plugin.action.isEnabled())
        self.assertTrue(self.plugin.action.isCheckable())

    def test_actions_enabled_when_editing_starts(self) -> None:
        """Starting the edit session enables both actions and the spinbox."""
        self.assertFalse(self.plugin.action.isEnabled())
        self.layer.startEditing()
        self.assertTrue(self.plugin.action.isEnabled())
        self.assertTrue(self.plugin.reshape_action.isEnabled())

    def test_difference_action_requires_editing(self) -> None:
        """Difference is disabled outside edit mode and enabled inside it."""
        self.assertFalse(self.plugin.difference_action.isEnabled())
        self.layer.startEditing()
        self.assertTrue(self.plugin.difference_action.isEnabled())

    def test_difference_pick_activation(self) -> None:
        """Without a selected pair, the pick tool is installed."""
        self.layer.startEditing()
        self.plugin._on_difference_triggered(True)
        self.assertIs(self.canvas.mapTool(), self.plugin._difference_pick_tool)
        self.assertTrue(self.plugin.difference_action.isChecked())
        self.assertTrue(self.iface.messages.infos)

    def test_deleted_active_layer_does_not_raise(self) -> None:
        """Deleting the active layer clears the stored reference safely."""
        doomed = self.make_layer("LineString")
        self.iface.setActiveLayer(doomed)
        self.plugin._on_current_layer_changed()
        self.assertIs(self.plugin._editing_layer, doomed)
        self._destroy_layer(doomed)
        self.plugin._on_current_layer_changed()
        self.assertIsNone(self.plugin._editing_layer)
        self.iface.setActiveLayer(self.layer)

    def test_force_dead_editing_reference_disconnects_safely(self) -> None:
        """A stale reference can be disconnected without touching C++ signals."""
        doomed = self.make_layer("LineString")
        self.iface.setActiveLayer(doomed)
        self.plugin._on_current_layer_changed()
        self._destroy_layer(doomed)
        self.plugin._editing_layer = doomed
        self.plugin._disconnect_editing_signals()
        self.assertIsNone(self.plugin._editing_layer)
        self.iface.setActiveLayer(self.layer)

    def test_unload_after_layer_deleted(self) -> None:
        """Plugin unload survives a layer deleted before shutdown."""
        doomed = self.make_layer("LineString")
        self.iface.setActiveLayer(doomed)
        self.plugin._on_current_layer_changed()
        self._destroy_layer(doomed)
        self.plugin._editing_layer = doomed
        self.plugin.unload()
        self.assertIsNone(self.plugin.action)
        self.assertIsNone(self.plugin.tool)

    def test_deleted_layer_cancels_difference_pick(self) -> None:
        """The difference pick tool is released when its layer is deleted."""
        doomed = self.make_layer("LineString")
        doomed.startEditing()
        self.iface.setActiveLayer(doomed)
        self.plugin._on_current_layer_changed()
        self.plugin._on_difference_triggered(True)
        self.assertIsNotNone(self.plugin._difference_pick_tool)
        self._destroy_layer(doomed)
        self.QCoreApplication.processEvents()
        self.assertIsNone(self.plugin._difference_pick_tool)
        self.iface.setActiveLayer(self.layer)

    def test_sampling_action_exists_without_editing(self) -> None:
        """Sampling settings stay available outside an edit session."""
        self.assertIsNotNone(self.plugin.sampling_action)
        self.assertTrue(self.plugin.sampling_action.isEnabled())

    def test_reshape_action_exists(self) -> None:
        """The reshape action and tool are created."""
        self.assertIsNotNone(self.plugin.reshape_action)
        self.assertIsNotNone(self.plugin.reshape_tool)
        self.layer.startEditing()
        self.assertTrue(self.plugin.reshape_action.isEnabled())

    def test_activate_reshape_without_selection(self) -> None:
        """Reshape activation does not require a preselected feature."""
        self.layer.startEditing()
        self.plugin._on_reshape_triggered(True)
        self.assertIs(self.canvas.mapTool(), self.plugin.reshape_tool)
        self.assertTrue(self.plugin.reshape_action.isChecked())
        self.assertTrue(self.layer.isEditable())

    def test_end_to_end_reshape(self) -> None:
        """A reshape stroke updates the feature under it."""
        feature = self.QgsFeature(self.layer.fields())
        feature.setGeometry(
            self.QgsGeometry.fromPolylineXY([self.QgsPointXY(0, 5), self.QgsPointXY(10, 5)])
        )
        self.layer.dataProvider().addFeature(feature)
        original = self.layer.getFeature(feature.id()).geometry().asWkt()
        self.layer.startEditing()
        self.plugin._on_reshape_triggered(True)
        tool = self.plugin.reshape_tool

        def event(event_type, x, y):
            return self.mouse_event(
                self.canvas, event_type, *self.device_point(self.canvas, (x, y))
            )

        tool.canvasPressEvent(event(self.PRESS, 3, 3))
        tool.canvasMoveEvent(event(self.MOVE, 3, 7))
        tool.canvasMoveEvent(event(self.MOVE, 7, 7))
        tool.canvasMoveEvent(event(self.MOVE, 7, 3))
        tool.canvasReleaseEvent(event(self.RELEASE, 7, 3))
        self.assertNotEqual(self.layer.getFeature(feature.id()).geometry().asWkt(), original)

    def test_action_disabled_for_point_layer(self) -> None:
        """Point layers disable the action."""
        self.iface.setActiveLayer(self.make_layer("Point"))
        self.assertFalse(self.plugin.action.isEnabled())

    def test_action_disabled_without_a_layer(self) -> None:
        """No active layer disables the action."""
        self.iface.setActiveLayer(None)
        self.assertFalse(self.plugin.action.isEnabled())

    def test_spinbox_disabled_for_geographic_crs(self) -> None:
        """Geographic layers disable the tolerance spinbox while editing."""
        self.layer.startEditing()
        self.assertFalse(self.plugin.spinbox.isEnabled())
        projected = self.make_layer("LineString", crs="EPSG:3857")
        projected.startEditing()
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

    def test_activation_requires_an_edit_session(self) -> None:
        """Activating the action does not start editing on its own."""
        self.plugin._on_action_triggered(True)
        self.assertIsNot(self.canvas.mapTool(), self.plugin.tool)
        self.assertFalse(self.layer.isEditable())
        self.assertFalse(self.plugin.action.isChecked())
        self.assertTrue(self.iface.messages.warnings)

    def test_editing_stopped_deactivates_tool_and_cancels_stroke(self) -> None:
        """Stopping editing cancels a stroke and unchecks the action."""
        self.layer.startEditing()
        self.plugin._on_action_triggered(True)
        tool = self.plugin.tool
        tool.canvasPressEvent(self.mouse_event(self.canvas, self.PRESS, 100, 100))
        tool.canvasMoveEvent(self.mouse_event(self.canvas, self.MOVE, 150, 150))
        self.layer.commitChanges()
        self.assertFalse(self.layer.isEditable())
        self.assertIsNot(self.canvas.mapTool(), tool)
        self.assertFalse(self.plugin.action.isChecked())
        self.assertEqual(self.layer.featureCount(), 0)

    def test_end_to_end_stroke_creates_a_feature(self) -> None:
        """A stroke through the tool is stored in the active layer."""
        self.layer.startEditing()
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
        self.assertIsNone(self.plugin.reshape_tool)
        self.assertIsNone(self.plugin.reshape_action)
        self.assertIsNone(self.plugin.sampling_action)
        self.assertIsNone(self.plugin.difference_action)
        self.assertIsNone(self.plugin._difference_pick_tool)
        self.assertIsNone(self.plugin.spinbox)
        self.assertIsNot(self.canvas.mapTool(), tool)


if __name__ == "__main__":
    unittest.main()

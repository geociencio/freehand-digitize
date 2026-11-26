"""Integration tests for the mouse pick tool used by feature difference."""

from __future__ import annotations

import unittest

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis


@requires_qgis
class TestDifferencePickTool(unittest.TestCase):
    """Target/cutter picking, duplicate guard and Esc cancellation."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY

        from freehand_digitize.gui.difference_pick_tool import DifferencePickTool
        from freehand_digitize.gui.qt_compat import KEY_ESCAPE
        from tests.integration.fakes import make_canvas, make_layer

        cls.QgsFeature = QgsFeature
        cls.QgsGeometry = QgsGeometry
        cls.QgsPointXY = QgsPointXY
        cls.DifferencePickTool = DifferencePickTool
        cls.KEY_ESCAPE = KEY_ESCAPE
        cls.make_canvas = staticmethod(make_canvas)
        cls.make_layer = staticmethod(make_layer)

    def setUp(self) -> None:
        """Create a polygon layer with two features and the pick tool."""
        self.layer = self.make_layer("Polygon")
        square = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        self.first = self._add(square)
        self.second = self._add(square)
        self.canvas = self.make_canvas(self.layer)
        self.tool = self.DifferencePickTool(self.canvas, self.layer)
        self.targets = []
        self.pairs = []
        self.duplicates = []
        self.cancelled = []
        self.tool.targetPicked.connect(self.targets.append)
        self.tool.featuresPicked.connect(lambda a, b: self.pairs.append((a, b)))
        self.tool.duplicateTarget.connect(lambda: self.duplicates.append(True))
        self.tool.pickCancelled.connect(lambda: self.cancelled.append(True))
        self.addCleanup(self.canvas.deleteLater)

    def _add(self, points) -> int:
        """Insert a polygon and return its id."""
        geometry = self.QgsGeometry.fromPolygonXY([[self.QgsPointXY(x, y) for x, y in points]])
        feature = self.QgsFeature(self.layer.fields())
        feature.setGeometry(geometry)
        feature.setAttribute(1, "feature")
        self.layer.dataProvider().addFeature(feature)
        return max(item.id() for item in self.layer.getFeatures())

    def _add_editing(self, points) -> int:
        """Add a feature in the edit buffer and return its (negative) id."""
        geometry = self.QgsGeometry.fromPolygonXY([[self.QgsPointXY(x, y) for x, y in points]])
        feature = self.QgsFeature(self.layer.fields())
        feature.setGeometry(geometry)
        feature.setAttribute(1, "edit feature")
        if not self.layer.isEditable():
            self.assertTrue(self.layer.startEditing())
        self.assertTrue(self.layer.addFeature(feature))
        return feature.id()

    def _click(self, feature_id: int) -> None:
        """Simulate identifying a feature."""
        self.tool._on_feature_identified(self.layer.getFeature(feature_id))

    def test_two_clicks_emit_target_and_pair(self) -> None:
        """First click is the target; second emits target/cutter."""
        self._click(self.first)
        self.assertEqual(self.targets, [self.first])
        self._click(self.second)
        self.assertEqual(self.pairs, [(self.first, self.second)])

    def test_edit_buffer_negative_fids_can_be_picked(self) -> None:
        """Features with negative edit-buffer ids are valid targets/cutters."""
        first = self._add_editing([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
        second = self._add_editing([(2, 2), (8, 2), (8, 8), (2, 8), (2, 2)])
        self.assertLess(first, 0)
        self._click(first)
        self._click(second)
        self.assertEqual(self.pairs, [(first, second)])

    def test_zero_fid_is_accepted(self) -> None:
        """A valid feature with id 0 is not rejected by the pick tool."""
        feature = self.layer.getFeature(self.first)
        feature.setId(0)
        self.tool._on_feature_identified(feature)
        self.assertEqual(self.targets, [0])

    def test_duplicate_target_is_rejected(self) -> None:
        """Clicking the target twice warns and keeps waiting."""
        self._click(self.first)
        self._click(self.first)
        self.assertEqual(self.pairs, [])
        self.assertEqual(self.duplicates, [True])

    def test_reset_forgets_target(self) -> None:
        """Reset starts a new pair."""
        self._click(self.first)
        self.tool.reset()
        self._click(self.second)
        self.assertEqual(self.targets[-1], self.second)
        self.assertEqual(self.pairs, [])

    def test_escape_emits_cancelled(self) -> None:
        """Esc cancels the pick."""
        escape = self.KEY_ESCAPE

        class Event:
            def key(self):
                return escape

            def accept(self):
                pass

        self.tool.keyPressEvent(Event())
        self.assertEqual(self.cancelled, [True])


if __name__ == "__main__":
    unittest.main()

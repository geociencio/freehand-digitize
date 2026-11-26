"""Integration tests for the feature-difference dialog."""

from __future__ import annotations

import unittest

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis


@requires_qgis
class TestDifferenceDialog(unittest.TestCase):
    """Target/cutter defaults, swap validation and accept/reject."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY

        from freehand_digitize.gui.difference_dialog import DifferenceDialog
        from tests.integration.fakes import FakeIface, make_layer

        cls.QgsFeature = QgsFeature
        cls.QgsGeometry = QgsGeometry
        cls.QgsPointXY = QgsPointXY
        cls.DifferenceDialog = DifferenceDialog
        cls.FakeIface = FakeIface
        cls.make_layer = staticmethod(make_layer)

    def setUp(self) -> None:
        """Create a layer with two polygon features."""
        self.layer = self.make_layer("Polygon")
        square = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        self.first = self._add(square)
        self.second = self._add(square)
        self.iface = self.FakeIface()
        self.addCleanup(self.iface.close)

    def _add(self, points) -> int:
        """Insert a polygon feature and return its id."""
        geometry = self.QgsGeometry.fromPolygonXY([[self.QgsPointXY(x, y) for x, y in points]])
        feature = self.QgsFeature(self.layer.fields())
        feature.setGeometry(geometry)
        feature.setAttribute(1, "feature")
        self.layer.dataProvider().addFeature(feature)
        return max(item.id() for item in self.layer.getFeatures())

    def _dialog(self):
        """Build the dialog for the two features."""
        dialog = self.DifferenceDialog(
            self.layer,
            [self.first, self.second],
            self.iface.mainWindow(),
        )
        self.addCleanup(dialog.deleteLater)
        return dialog

    def test_defaults_to_selection_order(self) -> None:
        """The first id is the target and the second the cutter."""
        dialog = self._dialog()
        self.assertEqual(dialog.target_combo.currentData(), self.first)
        self.assertEqual(dialog.cutter_combo.currentData(), self.second)
        self.assertTrue(dialog._apply_button.isEnabled())

    def test_uses_layer_display_expression(self) -> None:
        """The combo label prefers the layer display expression."""
        self.layer.setDisplayExpression('upper("name")')
        dialog = self._dialog()
        self.assertIn("FEATURE", dialog.target_combo.itemText(0))

    def test_same_feature_disables_apply(self) -> None:
        """Selecting the same target and cutter disables Apply."""
        dialog = self._dialog()
        dialog.cutter_combo.setCurrentIndex(dialog.cutter_combo.findData(self.first))
        self.assertFalse(dialog._apply_button.isEnabled())

    def test_accept_records_ids(self) -> None:
        """Accepting stores the selected pair."""
        dialog = self._dialog()
        dialog.target_combo.setCurrentIndex(dialog.target_combo.findData(self.second))
        dialog.cutter_combo.setCurrentIndex(dialog.cutter_combo.findData(self.first))
        dialog.accept()
        self.assertEqual(dialog.target_id, self.second)
        self.assertEqual(dialog.cutter_id, self.first)

    def test_reject_does_not_record_ids(self) -> None:
        """Rejecting leaves the ids unset."""
        dialog = self._dialog()
        dialog.reject()
        self.assertIsNone(dialog.target_id)
        self.assertIsNone(dialog.cutter_id)


if __name__ == "__main__":
    unittest.main()

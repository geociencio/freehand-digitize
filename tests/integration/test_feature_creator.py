"""Integration tests for feature creation (defaults, form, undo, validity)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis
from tests.mocks.settings import FakeSettings


@requires_qgis
class TestFeatureCreator(unittest.TestCase):
    """Feature creation against in-memory layers."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from qgis.core import QgsDefaultValue, QgsGeometry, QgsPointXY

        from freehand_digitize.gui.feature_creator import FeatureCreator
        from tests.integration.fakes import FakeIface, make_layer

        cls.QgsDefaultValue = QgsDefaultValue
        cls.QgsGeometry = QgsGeometry
        cls.QgsPointXY = QgsPointXY
        cls.FeatureCreator = FeatureCreator
        cls.FakeIface = FakeIface
        cls.make_layer = staticmethod(make_layer)

    def setUp(self) -> None:
        """Create a layer, a fake interface and a creator."""
        self.layer = self.make_layer("LineString")
        self.iface = self.FakeIface()
        self.settings = FakeSettings(
            {"qgis/digitizing/disable_enter_attribute_values_dialog": True}
        )
        self.creator = self.FeatureCreator(self.iface, self.settings)
        self.addCleanup(self.iface.close)

    def line(self, points: list[tuple[float, float]]):
        """Build a line geometry."""
        return self.QgsGeometry.fromPolylineXY([self.QgsPointXY(x, y) for x, y in points])

    def test_creates_feature_with_default_values(self) -> None:
        """Provider defaults are applied and an undo command is recorded."""
        self.layer.setDefaultValueDefinition(1, self.QgsDefaultValue("'auto'"))
        created = self.creator.create(self.layer, self.line([(0, 0), (1, 1)]), 0.0)
        self.assertTrue(created)
        self.assertTrue(self.layer.isEditable())
        self.assertEqual(self.layer.featureCount(), 1)
        feature = next(self.layer.getFeatures())
        self.assertEqual(feature["name"], "auto")
        self.assertGreater(self.layer.undoStack().count(), 0)

    def test_undo_removes_the_feature(self) -> None:
        """The edit command makes the creation undoable as one step."""
        self.creator.create(self.layer, self.line([(0, 0), (1, 1)]), 0.0)
        self.assertEqual(self.layer.featureCount(), 1)
        self.layer.undoStack().undo()
        self.assertEqual(self.layer.featureCount(), 0)

    def test_cancelled_form_discards_the_feature(self) -> None:
        """Cancelling the attribute form leaves no feature or undo command."""
        self.settings = FakeSettings()
        self.iface.form_result = 0
        self.creator = self.FeatureCreator(self.iface, self.settings)
        created = self.creator.create(self.layer, self.line([(0, 0), (1, 1)]), 0.0)
        self.assertFalse(created)
        self.assertEqual(self.layer.featureCount(), 0)
        self.assertEqual(self.layer.undoStack().count(), 0)
        self.assertEqual(len(self.iface.dialogs), 1)

    def test_accepted_form_adds_the_feature(self) -> None:
        """Accepting the attribute form keeps the feature."""
        self.settings = FakeSettings()
        self.iface.form_result = 1
        self.creator = self.FeatureCreator(self.iface, self.settings)
        created = self.creator.create(self.layer, self.line([(0, 0), (1, 1)]), 0.0)
        self.assertTrue(created)
        self.assertEqual(self.layer.featureCount(), 1)
        self.assertEqual(self.iface.dialogs[0].calls, 1)

    def test_invalid_geometry_is_rejected_when_user_declines(self) -> None:
        """The validity prompt can abort the creation."""
        from qgis.PyQt.QtWidgets import QMessageBox

        bowtie = self.QgsGeometry.fromPolygonXY(
            [
                [
                    self.QgsPointXY(0, 0),
                    self.QgsPointXY(2, 2),
                    self.QgsPointXY(2, 0),
                    self.QgsPointXY(0, 2),
                    self.QgsPointXY(0, 0),
                ]
            ]
        )
        self.assertFalse(bowtie.isGeosValid())
        polygon_layer = self.make_layer("Polygon")
        with patch(
            "freehand_digitize.gui.feature_creator.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ) as question:
            created = self.creator.create(polygon_layer, bowtie, 0.0)
        self.assertFalse(created)
        self.assertEqual(question.call_count, 1)
        self.assertEqual(polygon_layer.featureCount(), 0)

    def test_invalid_geometry_is_kept_when_user_accepts(self) -> None:
        """Accepting the prompt adds the invalid geometry."""
        from qgis.PyQt.QtWidgets import QMessageBox

        bowtie = self.QgsGeometry.fromPolygonXY(
            [
                [
                    self.QgsPointXY(0, 0),
                    self.QgsPointXY(2, 2),
                    self.QgsPointXY(2, 0),
                    self.QgsPointXY(0, 2),
                    self.QgsPointXY(0, 0),
                ]
            ]
        )
        polygon_layer = self.make_layer("Polygon")
        with patch(
            "freehand_digitize.gui.feature_creator.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            created = self.creator.create(polygon_layer, bowtie, 0.0)
        self.assertTrue(created)
        self.assertEqual(polygon_layer.featureCount(), 1)

    def test_simplification_reduces_vertices(self) -> None:
        """The tolerance is applied before the feature is stored."""
        points = [(0, 0), (0.1, 0.01), (0.2, 0.0), (0.3, 0.01), (1.0, 0.0)]
        created = self.creator.create(self.layer, self.line(points), 0.2)
        self.assertTrue(created)
        feature = next(self.layer.getFeatures())
        self.assertLess(len(feature.geometry().asPolyline()), len(points))

    def test_empty_geometry_is_rejected(self) -> None:
        """An empty geometry never creates a feature."""
        created = self.creator.create(self.layer, self.QgsGeometry(), 0.0)
        self.assertFalse(created)
        self.assertEqual(self.layer.featureCount(), 0)

    def test_starts_editing_when_needed(self) -> None:
        """A non-editable layer is put in edit mode automatically."""
        self.assertFalse(self.layer.isEditable())
        self.assertTrue(self.creator.create(self.layer, self.line([(0, 0), (1, 1)]), 0.0))
        self.assertTrue(self.layer.isEditable())


if __name__ == "__main__":
    unittest.main()

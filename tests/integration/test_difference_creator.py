"""Integration tests for the feature-difference creator."""

from __future__ import annotations

import unittest

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis

SQUARE_A = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
SQUARE_B = [(5, 0), (15, 0), (15, 10), (5, 10), (5, 0)]
SQUARE_FAR = [(30, 30), (40, 30), (40, 40), (30, 40), (30, 30)]
COVER = [(-1, -1), (11, -1), (11, 11), (-1, 11), (-1, -1)]


@requires_qgis
class TestDifferenceCreator(unittest.TestCase):
    """Target update, cutter preservation, empty results and undo."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY

        from freehand_digitize.gui.difference_creator import DifferenceCreator
        from tests.integration.fakes import FakeIface, make_layer

        cls.QgsFeature = QgsFeature
        cls.QgsGeometry = QgsGeometry
        cls.QgsPointXY = QgsPointXY
        cls.DifferenceCreator = DifferenceCreator
        cls.FakeIface = FakeIface
        cls.make_layer = staticmethod(make_layer)

    def setUp(self) -> None:
        """Create a fake interface and the creator."""
        self.iface = self.FakeIface()
        self.creator = self.DifferenceCreator(self.iface)
        self.addCleanup(self.iface.close)

    def _polygon(self, points):
        """Build a polygon geometry."""
        return self.QgsGeometry.fromPolygonXY([[self.QgsPointXY(x, y) for x, y in points]])

    def _add(self, layer, geometry, name="feature"):
        """Insert a feature with an attribute and return its id."""
        feature = self.QgsFeature(layer.fields())
        feature.setGeometry(geometry)
        feature.setAttribute(1, name)
        layer.dataProvider().addFeature(feature)
        return max(item.id() for item in layer.getFeatures())

    def _layer(self, *geometries):
        """Return an editable polygon layer with the given features."""
        layer = self.make_layer("Polygon")
        ids = [self._add(layer, self._polygon(points)) for points in geometries]
        layer.startEditing()
        return layer, ids

    def test_difference_polygons(self) -> None:
        """The target is cut and keeps its attributes."""
        layer, (target_id, cutter_id) = self._layer(SQUARE_A, SQUARE_B)
        original_cutter = layer.getFeature(cutter_id).geometry().asWkt()
        created = self.creator.apply(layer, target_id, cutter_id)
        self.assertTrue(created)
        geometry = layer.getFeature(target_id).geometry()
        self.assertTrue(geometry.isGeosValid())
        expected = self._polygon([(5, 0), (0, 0), (0, 10), (5, 10), (5, 0)])
        self.assertTrue(geometry.isTopologicallyEqual(expected))
        self.assertEqual(layer.getFeature(target_id)["name"], "feature")
        self.assertEqual(layer.getFeature(cutter_id).geometry().asWkt(), original_cutter)

    def test_difference_undo_restores_target(self) -> None:
        """One undo restores the original target geometry."""
        layer, (target_id, cutter_id) = self._layer(SQUARE_A, SQUARE_B)
        original = layer.getFeature(target_id).geometry().asWkt()
        self.assertTrue(self.creator.apply(layer, target_id, cutter_id))
        layer.undoStack().undo()
        self.assertEqual(layer.getFeature(target_id).geometry().asWkt(), original)

    def test_difference_without_overlap(self) -> None:
        """A non-overlapping cutter leaves the target and undo stack unchanged."""
        layer, (target_id, cutter_id) = self._layer(SQUARE_A, SQUARE_FAR)
        original = layer.getFeature(target_id).geometry()
        undo_count = layer.undoStack().count()
        self.assertFalse(self.creator.apply(layer, target_id, cutter_id))
        self.assertTrue(layer.getFeature(target_id).geometry().isTopologicallyEqual(original))
        self.assertEqual(layer.undoStack().count(), undo_count)
        self.assertTrue(self.iface.messages.infos)

    def test_empty_difference_is_rejected(self) -> None:
        """A cutter covering the target leaves it unchanged."""
        layer, (target_id, cutter_id) = self._layer(SQUARE_A, COVER)
        original = layer.getFeature(target_id).geometry().asWkt()
        self.assertFalse(self.creator.apply(layer, target_id, cutter_id))
        self.assertEqual(layer.getFeature(target_id).geometry().asWkt(), original)
        self.assertTrue(self.iface.messages.warnings)

    def test_same_feature_is_rejected(self) -> None:
        """Target and cutter must differ."""
        layer, (target_id, _cutter_id) = self._layer(SQUARE_A, SQUARE_FAR)
        self.assertFalse(self.creator.apply(layer, target_id, target_id))
        self.assertTrue(self.iface.messages.warnings)

    def test_non_editable_layer_is_rejected(self) -> None:
        """Difference requires an active edit session."""
        layer, (target_id, cutter_id) = self._layer(SQUARE_A, SQUARE_B)
        layer.rollBack()
        self.assertFalse(self.creator.apply(layer, target_id, cutter_id))
        self.assertFalse(layer.isEditable())
        self.assertTrue(self.iface.messages.warnings)

    def test_line_by_line_gives_multiline(self) -> None:
        """A line target minus a line segment becomes a multiline."""
        layer = self.make_layer("LineString")
        target = self.QgsGeometry.fromPolylineXY([self.QgsPointXY(0, 0), self.QgsPointXY(10, 0)])
        cutter = self.QgsGeometry.fromPolylineXY([self.QgsPointXY(4, 0), self.QgsPointXY(6, 0)])
        target_id = self._add(layer, target)
        cutter_id = self._add(layer, cutter, "cutter")
        layer.startEditing()
        self.assertTrue(self.creator.apply(layer, target_id, cutter_id))
        self.assertIn("MultiLineString", layer.getFeature(target_id).geometry().asWkt())


if __name__ == "__main__":
    unittest.main()

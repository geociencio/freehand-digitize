"""Integration tests for the reshape creator."""

from __future__ import annotations

import unittest

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis

SQUARE_A = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
SQUARE_B = [(0, 20), (10, 20), (10, 30), (0, 30), (0, 20)]


@requires_qgis
class TestReshapeCreator(unittest.TestCase):
    """Target detection, selection filter, reshape and undo."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY
        from qgis.PyQt import sip
        from qgis.PyQt.QtCore import QObject

        from freehand_digitize.gui.reshape_creator import ReshapeCreator
        from tests.integration.fakes import FakeIface, make_layer

        cls.sip = sip
        cls.QObject = QObject
        cls.QgsFeature = QgsFeature
        cls.QgsGeometry = QgsGeometry
        cls.QgsPointXY = QgsPointXY
        cls.ReshapeCreator = ReshapeCreator
        cls.FakeIface = FakeIface
        cls.make_layer = staticmethod(make_layer)

    def setUp(self) -> None:
        """Create a fake interface and the creator."""
        self.iface = self.FakeIface()
        self.creator = self.ReshapeCreator(self.iface)
        self.addCleanup(self.iface.close)

    # -- helpers ----------------------------------------------------------
    def _line(self, points: list[tuple[float, float]]):
        """Build a line geometry."""
        return self.QgsGeometry.fromPolylineXY([self.QgsPointXY(x, y) for x, y in points])

    def _polygon(self, points: list[tuple[float, float]]):
        """Build a polygon geometry."""
        return self.QgsGeometry.fromPolygonXY([[self.QgsPointXY(x, y) for x, y in points]])

    def _add(self, layer, geometry) -> int:
        """Insert a feature and return its id."""
        feature = self.QgsFeature(layer.fields())
        feature.setGeometry(geometry)
        layer.dataProvider().addFeature(feature)
        return feature.id()

    def _line_layer(self):
        """Return a line layer with a simple horizontal feature."""
        layer = self.make_layer("LineString")
        feature_id = self._add(layer, self._line([(0, 0), (5, 0), (10, 0)]))
        layer.startEditing()
        return layer, feature_id

    def _polygon_layer(self):
        """Return a polygon layer with one square feature."""
        layer = self.make_layer("Polygon")
        feature_id = self._add(layer, self._polygon(SQUARE_A))
        layer.startEditing()
        return layer, feature_id

    def _stacked_polygons(self):
        """Return a polygon layer with two stacked squares."""
        layer = self.make_layer("Polygon")
        first = self._add(layer, self._polygon(SQUARE_A))
        second = self._add(layer, self._polygon(SQUARE_B))
        layer.startEditing()
        return layer, first, second

    # -- tests ------------------------------------------------------------
    def test_line_under_stroke_without_selection(self) -> None:
        """A stroke over a line reshapes it without preselection."""
        layer, feature_id = self._line_layer()
        original = layer.getFeature(feature_id).geometry().asWkt()
        created = self.creator.reshape(
            layer,
            self._line([(3, -1), (3, 1), (7, 1), (7, -1)]),
        )
        self.assertTrue(created)
        self.assertNotEqual(layer.getFeature(feature_id).geometry().asWkt(), original)

    def test_polygon_under_stroke_without_selection(self) -> None:
        """A stroke over a polygon reshapes its ring."""
        layer, feature_id = self._polygon_layer()
        created = self.creator.reshape(layer, self._line([(5, -2), (5, 12)]))
        self.assertTrue(created)
        polygon = layer.getFeature(feature_id).geometry().asPolygon()
        self.assertTrue(polygon)
        self.assertGreaterEqual(len(polygon[0]), 4)

    def test_multiple_features_one_undo(self) -> None:
        """All features under the stroke are reshaped in one undo command."""
        layer, first, second = self._stacked_polygons()
        original_first = layer.getFeature(first).geometry().asWkt()
        original_second = layer.getFeature(second).geometry().asWkt()
        created = self.creator.reshape(layer, self._line([(5, -2), (5, 32)]))
        self.assertTrue(created)
        self.assertNotEqual(layer.getFeature(first).geometry().asWkt(), original_first)
        self.assertNotEqual(layer.getFeature(second).geometry().asWkt(), original_second)
        self.assertEqual(len(self.iface.messages.infos), 1)
        layer.undoStack().undo()
        self.assertEqual(layer.getFeature(first).geometry().asWkt(), original_first)
        self.assertEqual(layer.getFeature(second).geometry().asWkt(), original_second)

    def test_selection_filters_targets(self) -> None:
        """With a selection, only selected features under the stroke change."""
        layer, first, _second = self._stacked_polygons()
        layer.selectByIds([first])
        original_second = layer.getFeature(_second).geometry().asWkt()
        created = self.creator.reshape(layer, self._line([(5, -2), (5, 32)]))
        self.assertTrue(created)
        self.assertNotEqual(
            layer.getFeature(first).geometry().asWkt(),
            self._polygon(SQUARE_A).asWkt(),
        )
        self.assertEqual(layer.getFeature(_second).geometry().asWkt(), original_second)

    def test_selection_without_intersection_warns(self) -> None:
        """A selection outside the stroke does not reshape anything."""
        layer, first, _second = self._stacked_polygons()
        layer.selectByIds([first])
        created = self.creator.reshape(layer, self._line([(5, 18), (5, 32)]))
        self.assertFalse(created)
        self.assertTrue(self.iface.messages.warnings)

    def test_no_feature_under_stroke(self) -> None:
        """A stroke in an empty area warns and changes nothing."""
        layer, feature_id = self._line_layer()
        original = layer.getFeature(feature_id).geometry().asWkt()
        created = self.creator.reshape(layer, self._line([(3, 20), (7, 20)]))
        self.assertFalse(created)
        self.assertTrue(self.iface.messages.warnings)
        self.assertEqual(layer.getFeature(feature_id).geometry().asWkt(), original)

    def test_no_successful_reshape(self) -> None:
        """A candidate that cannot be reshaped warns and changes nothing."""
        layer, feature_id = self._line_layer()
        original = layer.getFeature(feature_id).geometry().asWkt()
        created = self.creator.reshape(layer, self._line([(3, -1), (3, 1)]))
        self.assertFalse(created)
        self.assertTrue(self.iface.messages.warnings)
        self.assertEqual(layer.getFeature(feature_id).geometry().asWkt(), original)

    def test_rejects_deleted_layer(self) -> None:
        """Reshape returns cleanly when the layer was deleted."""
        layer = self.make_layer("Polygon")
        self.sip.delete(layer)
        self.assertFalse(self.creator.reshape(layer, self._line([(5, -2), (5, 12)])))
        self.assertTrue(self.iface.messages.warnings)

    def test_rejects_non_editable_layer(self) -> None:
        """Reshape requires an active edit session."""
        layer = self.make_layer("Polygon")
        feature_id = self._add(layer, self._polygon(SQUARE_A))
        original = layer.getFeature(feature_id).geometry().asWkt()
        self.assertFalse(layer.isEditable())
        created = self.creator.reshape(layer, self._line([(5, -2), (5, 12)]))
        self.assertFalse(created)
        self.assertFalse(layer.isEditable())
        self.assertEqual(layer.getFeature(feature_id).geometry().asWkt(), original)


if __name__ == "__main__":
    unittest.main()

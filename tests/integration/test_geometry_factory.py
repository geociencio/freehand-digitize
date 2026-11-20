"""Integration tests for the geometry factory."""

from __future__ import annotations

import unittest

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis


@requires_qgis
class TestGeometryFactory(unittest.TestCase):
    """Line and polygon construction in layer coordinates."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the module under test."""
        ensure_qgis_app()
        from freehand_digitize.gui.geometry_factory import build_geometry

        cls.build_geometry = staticmethod(build_geometry)

    def test_line_geometry(self) -> None:
        """Two or more points produce a polyline."""
        geometry = self.build_geometry([(0.0, 0.0), (1.0, 1.0), (2.0, 0.5)], "line")
        self.assertIsNotNone(geometry)
        self.assertFalse(geometry.isEmpty())
        self.assertEqual(len(geometry.asPolyline()), 3)

    def test_polygon_geometry_is_closed(self) -> None:
        """A polygon ring repeats its first vertex."""
        geometry = self.build_geometry(
            [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)],
            "polygon",
        )
        self.assertIsNotNone(geometry)
        rings = geometry.asPolygon()
        self.assertEqual(len(rings), 1)
        self.assertEqual(len(rings[0]), 4)
        self.assertEqual(rings[0][0], rings[0][-1])

    def test_line_needs_two_points(self) -> None:
        """A single point cannot build a line."""
        self.assertIsNone(self.build_geometry([(0.0, 0.0)], "line"))

    def test_polygon_needs_three_points(self) -> None:
        """Two points cannot build a polygon."""
        self.assertIsNone(self.build_geometry([(0.0, 0.0), (1.0, 1.0)], "polygon"))

    def test_empty_input(self) -> None:
        """Empty strokes return no geometry."""
        self.assertIsNone(self.build_geometry([], "line"))
        self.assertIsNone(self.build_geometry([], "polygon"))


if __name__ == "__main__":
    unittest.main()

"""Unit tests for the pure geometry rules."""

from __future__ import annotations

import unittest

from freehand_digitize.core.constants import (
    MIN_LINE_POINTS,
    MIN_POLYGON_POINTS,
    TOLERANCE_MAX,
)
from freehand_digitize.core.geometry_rules import (
    KIND_LINE,
    KIND_POINT,
    KIND_POLYGON,
    KIND_UNKNOWN,
    clamp_tolerance,
    close_ring,
    effective_tolerance,
    geometry_kind,
    has_enough_points,
    is_supported_geometry,
    is_supported_kind,
    min_vertex_count,
    to_xy,
)


class TestGeometryKind(unittest.TestCase):
    """Geometry type mapping and support checks."""

    def test_known_types(self) -> None:
        """Map the three QGIS geometry type values."""
        self.assertEqual(geometry_kind(0), KIND_POINT)
        self.assertEqual(geometry_kind(1), KIND_LINE)
        self.assertEqual(geometry_kind(2), KIND_POLYGON)

    def test_coercible_and_unknown_types(self) -> None:
        """Accept numeric strings and reject everything else."""
        self.assertEqual(geometry_kind("1"), KIND_LINE)
        self.assertEqual(geometry_kind(3), KIND_UNKNOWN)
        self.assertEqual(geometry_kind(None), KIND_UNKNOWN)
        self.assertEqual(geometry_kind("polygon"), KIND_UNKNOWN)

    def test_supported_geometries(self) -> None:
        """Only lines and polygons are drawable."""
        self.assertFalse(is_supported_geometry(0))
        self.assertTrue(is_supported_geometry(1))
        self.assertTrue(is_supported_geometry(2))
        self.assertFalse(is_supported_geometry(99))

    def test_supported_kinds(self) -> None:
        """Only line/polygon kinds are supported."""
        self.assertTrue(is_supported_kind(KIND_LINE))
        self.assertTrue(is_supported_kind(KIND_POLYGON))
        self.assertFalse(is_supported_kind(KIND_POINT))
        self.assertFalse(is_supported_kind(KIND_UNKNOWN))


class TestVertexCounts(unittest.TestCase):
    """Minimum vertex requirements."""

    def test_min_counts(self) -> None:
        """Lines need two points, polygons three."""
        self.assertEqual(min_vertex_count(KIND_LINE), MIN_LINE_POINTS)
        self.assertEqual(min_vertex_count(KIND_POLYGON), MIN_POLYGON_POINTS)

    def test_has_enough_points(self) -> None:
        """Respect the minimum and reject unsupported kinds."""
        self.assertFalse(has_enough_points([(0, 0)], KIND_LINE))
        self.assertTrue(has_enough_points([(0, 0), (1, 1)], KIND_LINE))
        self.assertFalse(has_enough_points([(0, 0), (1, 1)], KIND_POLYGON))
        self.assertTrue(has_enough_points([(0, 0), (1, 1), (2, 0)], KIND_POLYGON))
        self.assertFalse(has_enough_points([(0, 0), (1, 1), (2, 0)], KIND_POINT))


class TestTolerance(unittest.TestCase):
    """Tolerance clamping and geographic policy."""

    def test_clamp_range(self) -> None:
        """Clamp to the configured range."""
        self.assertEqual(clamp_tolerance(-1), 0.0)
        self.assertEqual(clamp_tolerance(0), 0.0)
        self.assertEqual(clamp_tolerance(1.25), 1.25)
        self.assertEqual(clamp_tolerance(TOLERANCE_MAX + 1), TOLERANCE_MAX)

    def test_clamp_invalid_values(self) -> None:
        """Non-numeric and non-finite values become zero."""
        self.assertEqual(clamp_tolerance("not-a-number"), 0.0)
        self.assertEqual(clamp_tolerance(None), 0.0)
        self.assertEqual(clamp_tolerance(float("nan")), 0.0)
        self.assertEqual(clamp_tolerance(float("inf")), 0.0)
        self.assertEqual(clamp_tolerance("1.5"), 1.5)

    def test_effective_tolerance_geographic(self) -> None:
        """Geographic layers always use zero."""
        self.assertEqual(effective_tolerance(2.0, True), 0.0)
        self.assertEqual(effective_tolerance(2.0, False), 2.0)
        self.assertEqual(effective_tolerance(9.0, False), TOLERANCE_MAX)


class FakePoint:
    """Point object exposing the QgsPointXY interface."""

    def __init__(self, x: float, y: float) -> None:
        self._x = x
        self._y = y

    def x(self) -> float:
        """Return the x coordinate."""
        return self._x

    def y(self) -> float:
        """Return the y coordinate."""
        return self._y


class TestPointConversion(unittest.TestCase):
    """Tuple and QgsPointXY-like normalisation."""

    def test_to_xy_tuples(self) -> None:
        """Tuples pass through as floats."""
        self.assertEqual(to_xy([(1, 2), (3.5, 4.5)]), [(1.0, 2.0), (3.5, 4.5)])

    def test_to_xy_point_objects(self) -> None:
        """Objects with x()/y() are normalised."""
        self.assertEqual(to_xy([FakePoint(1, 2)]), [(1.0, 2.0)])

    def test_close_ring_open(self) -> None:
        """An open ring gets the first point appended."""
        self.assertEqual(
            close_ring([(0, 0), (1, 0), (1, 1)]),
            [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0)],
        )

    def test_close_ring_already_closed(self) -> None:
        """A closed ring is not duplicated."""
        points = [(0, 0), (1, 0), (1, 1), (0, 0)]
        self.assertEqual(close_ring(points), [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0)])

    def test_close_ring_empty(self) -> None:
        """An empty stroke stays empty."""
        self.assertEqual(close_ring([]), [])


if __name__ == "__main__":
    unittest.main()

"""Build ``QgsGeometry`` objects from recorded stroke points.

The stroke is stored in layer coordinates, so the resulting geometry is already
in the layer CRS and no on-the-fly reprojection is needed when the feature is
created.
"""

from __future__ import annotations

from collections.abc import Sequence

from qgis.core import QgsGeometry, QgsPointXY

from ..core.constants import MIN_POLYGON_RING_POINTS
from ..core.geometry_rules import KIND_POLYGON, close_ring, to_xy


def build_geometry(points: Sequence[object], kind: str) -> QgsGeometry | None:
    """Build a line or polygon geometry from stroke points.

    Args:
        points: Stroke vertices in layer coordinates (tuples or QgsPointXY).
        kind: ``"line"`` or ``"polygon"``.

    Returns:
        A geometry, or ``None`` when there are not enough points.
    """
    if kind == KIND_POLYGON:
        coords = close_ring(points)
        if len(coords) < MIN_POLYGON_RING_POINTS:
            return None
        return QgsGeometry.fromPolygonXY([[QgsPointXY(x, y) for x, y in coords]])

    coords = to_xy(points)
    if len(coords) < 2:
        return None
    return QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in coords])

"""Pure rules describing what can be drawn and how the stroke is built.

The GUI layer converts ``layer.geometryType()`` and ``layer.crs().isGeographic()``
into plain values before calling these helpers, which keeps the module QGIS-free
and directly unit-testable.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from .constants import (
    MIN_LINE_POINTS,
    MIN_POLYGON_POINTS,
    TOLERANCE_MAX,
    TOLERANCE_MIN,
)

GEOMETRY_POINT = 0
GEOMETRY_LINE = 1
GEOMETRY_POLYGON = 2

KIND_POINT = "point"
KIND_LINE = "line"
KIND_POLYGON = "polygon"
KIND_UNKNOWN = "unknown"

_KIND_BY_TYPE: dict[int, str] = {
    GEOMETRY_POINT: KIND_POINT,
    GEOMETRY_LINE: KIND_LINE,
    GEOMETRY_POLYGON: KIND_POLYGON,
}
_SUPPORTED_KINDS = frozenset({KIND_LINE, KIND_POLYGON})


def geometry_kind(geometry_type: Any) -> str:
    """Return ``"point"``, ``"line"``, ``"polygon"`` or ``"unknown"``.

    Args:
        geometry_type: Value returned by ``QgsVectorLayer.geometryType()``.

    Returns:
        A stable string identifier for the geometry type.
    """
    try:
        return _KIND_BY_TYPE.get(int(geometry_type), KIND_UNKNOWN)
    except (TypeError, ValueError):
        return KIND_UNKNOWN


def is_supported_geometry(geometry_type: Any) -> bool:
    """Return whether freehand drawing supports *geometry_type*.

    Args:
        geometry_type: Value returned by ``QgsVectorLayer.geometryType()``.

    Returns:
        ``True`` for line and polygon layers.
    """
    return geometry_kind(geometry_type) in _SUPPORTED_KINDS


def is_supported_kind(kind: str) -> bool:
    """Return whether a kind produced by :func:`geometry_kind` is drawable."""
    return kind in _SUPPORTED_KINDS


def min_vertex_count(kind: str) -> int:
    """Return the minimum number of stroke points required for *kind*.

    A line needs two points; a polygon needs three distinct points before the
    ring is closed.
    """
    return MIN_LINE_POINTS if kind == KIND_LINE else MIN_POLYGON_POINTS


def has_enough_points(points: Sequence[Any], kind: str) -> bool:
    """Return whether *points* can produce a valid geometry of *kind*.

    Args:
        points: Stroke points (tuples or objects exposing ``x()``/``y()``).
        kind: One of the ``KIND_*`` constants.

    Returns:
        ``True`` when the stroke has the minimum number of vertices.
    """
    return is_supported_kind(kind) and len(points) >= min_vertex_count(kind)


def clamp_tolerance(value: Any) -> float:
    """Clamp a tolerance to the supported range.

    Non-numeric and non-finite values fall back to ``0`` so the plugin never
    passes ``NaN`` to ``QgsGeometry.simplify``.

    Args:
        value: Raw user or settings value.

    Returns:
        A finite float within ``[TOLERANCE_MIN, TOLERANCE_MAX]``.
    """
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return TOLERANCE_MIN
    if not math.isfinite(numeric):
        return TOLERANCE_MIN
    return max(TOLERANCE_MIN, min(TOLERANCE_MAX, numeric))


def effective_tolerance(tolerance: Any, is_geographic: bool) -> float:
    """Return the tolerance actually applied to a layer.

    Geographic layers use ``0`` because a unit-based tolerance is meaningless
    in degrees (the upstream plugin disabled the spinbox for this reason).

    Args:
        tolerance: User-configured tolerance in layer units.
        is_geographic: Whether the layer CRS is geographic.

    Returns:
        The clamped tolerance, or ``0.0`` for geographic layers.
    """
    if is_geographic:
        return 0.0
    return clamp_tolerance(tolerance)


def _as_xy(point: Any) -> tuple[float, float]:
    """Normalise a point-like value to an ``(x, y)`` tuple."""
    if isinstance(point, (tuple, list)) and len(point) >= 2:
        return float(point[0]), float(point[1])
    return float(point.x()), float(point.y())


def close_ring(points: Sequence[Any]) -> list[tuple[float, float]]:
    """Return the points as ``(x, y)`` tuples with the first point repeated.

    Args:
        points: Open (or already closed) ring vertices.

    Returns:
        A closed list of tuples; empty input returns an empty list.
    """
    closed = [_as_xy(point) for point in points]
    if closed and closed[0] != closed[-1]:
        closed.append(closed[0])
    return closed


def to_xy(points: Sequence[Any]) -> list[tuple[float, float]]:
    """Return every point as an ``(x, y)`` tuple without closing the ring."""
    return [_as_xy(point) for point in points]

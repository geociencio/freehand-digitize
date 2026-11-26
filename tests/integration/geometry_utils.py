"""Geometry comparison helpers across supported QGIS versions."""

from __future__ import annotations

from typing import Any


def geometries_equal(left: Any, right: Any) -> bool:
    """Return topological equality using the API available in this QGIS."""
    topologically_equal = getattr(left, "isTopologicallyEqual", None)
    if topologically_equal is not None:
        return bool(topologically_equal(right))
    return bool(left.isGeosEqual(right))

"""Helpers for working with QGIS layers that may have been deleted."""

from __future__ import annotations

from typing import Any

from qgis.PyQt import sip


def is_layer_alive(layer: Any) -> bool:
    """Return whether *layer* still has a live C++ object."""
    if layer is None:
        return False
    try:
        return not sip.isdeleted(layer)
    except (AttributeError, RuntimeError, TypeError):
        return False

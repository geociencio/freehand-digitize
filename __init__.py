"""QGIS plugin entry point for Freehand Digitize."""

from __future__ import annotations

from typing import Any


def classFactory(iface: Any) -> Any:  # noqa: N802 - QGIS API name
    """Return the plugin instance for QGIS."""
    from .freehand_plugin import FreehandDigitizePlugin

    return FreehandDigitizePlugin(iface)

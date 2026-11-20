"""Small Qt/PyQGIS compatibility layer for PyQt5 (QGIS 3) and PyQt6 (QGIS 4).

Enums changed shape between Qt5 and Qt6 (``Qt.LeftButton`` vs
``Qt.MouseButton.LeftButton``) and a few classes moved between modules. The
constants below are resolved once at import time so the rest of the plugin can
use stable names.
"""

from __future__ import annotations

from typing import Any

from qgis.core import Qgis, QgsPointLocator
from qgis.PyQt.QtCore import Qt

try:  # PyQt6 ships QAction in QtGui; PyQt5 keeps it in QtWidgets.
    from qgis.PyQt.QtGui import QAction
except ImportError:  # pragma: no cover - exercised on QGIS 3/PyQt5 only
    from qgis.PyQt.QtWidgets import QAction  # noqa: F401 - re-exported

try:
    LEFT_BUTTON = Qt.MouseButton.LeftButton
    RIGHT_BUTTON = Qt.MouseButton.RightButton
    KEY_CONTROL = Qt.Key.Key_Control
    KEY_ESCAPE = Qt.Key.Key_Escape
    CROSS_CURSOR = Qt.CursorShape.CrossCursor
except AttributeError:  # pragma: no cover - exercised on PyQt5 only
    # getattr keeps the static Qt6 checker from seeing dead flat-enum access.
    LEFT_BUTTON = getattr(Qt, "LeftButton")
    RIGHT_BUTTON = getattr(Qt, "RightButton")
    KEY_CONTROL = getattr(Qt, "Key_Control")
    KEY_ESCAPE = getattr(Qt, "Key_Escape")
    CROSS_CURSOR = getattr(Qt, "CrossCursor")

try:
    RUBBERBAND_LINE = Qgis.GeometryType.Line
    RUBBERBAND_POLYGON = Qgis.GeometryType.Polygon
except AttributeError:  # pragma: no cover - QGIS 3.28 without scoped enums
    RUBBERBAND_LINE = getattr(Qgis, "Line")
    RUBBERBAND_POLYGON = getattr(Qgis, "Polygon")

try:
    SNAP_VERTEX = QgsPointLocator.Type.Vertex
except AttributeError:  # pragma: no cover - QGIS 3.28 without scoped enums
    SNAP_VERTEX = getattr(QgsPointLocator, "Vertex")


def exec_dialog(dialog: Any) -> bool:
    """Execute a QGIS dialog and return whether it was accepted.

    PyQt6 uses ``exec()``; PyQt5 also provides ``exec_()``.
    """
    execute = getattr(dialog, "exec", None) or getattr(dialog, "exec_", None)
    if execute is None:
        return True
    return bool(execute())

"""Pencil cursor used while the freehand tool is active.

The cursor is a 16x16 XPM (the format used by the original ``freehandEditing``
plugin, GPL-2.0, Pavol Kapusta) so it needs no binary resource file. QGIS themes
do not ship a pencil cursor, and a cross cursor hides the drawing point.
"""

from __future__ import annotations

from qgis.PyQt.QtGui import QCursor, QPixmap

from .qt_compat import CROSS_CURSOR

PENCIL_XPM = [
    "16 16 3 1",
    "      c None",
    ".     c #FF0000",
    "+     c #faed55",
    "                ",
    "       +.+      ",
    "      ++.++     ",
    "     +.....+    ",
    "    +.  .  .+   ",
    "   +.   .   .+  ",
    "  +.    .    .+ ",
    " ++.    .    .++",
    " ... ...+... ...",
    " ++.    .    .++",
    "  +.    .    .+ ",
    "   +.   .   .+  ",
    "   ++.  .  .+   ",
    "    ++.....+    ",
    "      ++.++     ",
    "       +.+      ",
]

#: Hot spot: the pencil tip sits on the centre column of the 16x16 pixmap.
HOTSPOT = (8, 8)


def build_pencil_cursor() -> QCursor:
    """Return the pencil cursor, falling back to a cross cursor.

    Returns:
        A ``QCursor`` usable by ``QgsMapTool.setCursor``.
    """
    try:
        pixmap = QPixmap(PENCIL_XPM)
    except (TypeError, ValueError, RuntimeError):
        return QCursor(CROSS_CURSOR)
    if pixmap.isNull():
        return QCursor(CROSS_CURSOR)
    return QCursor(pixmap, *HOTSPOT)

"""Test doubles and factories for the QGIS integration tests.

This module imports PyQGIS, so it must only be imported after
``ensure_qgis_app()`` has run (integration tests do that in ``setUpClass``).
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsRectangle,
    QgsVectorLayer,
)
from qgis.gui import QgsMapCanvas, QgsMapMouseEvent
from qgis.PyQt.QtCore import QEvent, QObject, QPointF, Qt, pyqtSignal
from qgis.PyQt.QtGui import QMouseEvent
from qgis.PyQt.QtWidgets import QMainWindow, QToolBar

from freehand_digitize.gui.qt_compat import LEFT_BUTTON

try:  # PyQt6
    NO_MODIFIER = Qt.KeyboardModifier.NoModifier
    PRESS = QEvent.Type.MouseButtonPress
    MOVE = QEvent.Type.MouseMove
    RELEASE = QEvent.Type.MouseButtonRelease
except AttributeError:  # pragma: no cover - PyQt5
    NO_MODIFIER = Qt.NoModifier
    PRESS = QEvent.MouseButtonPress
    MOVE = QEvent.MouseMove
    RELEASE = QEvent.MouseButtonRelease


def make_layer(
    geometry_type: str = "LineString",
    crs: str = "EPSG:4326",
    fields: tuple[str, ...] = ("id:integer", "name:string"),
) -> QgsVectorLayer:
    """Create a valid in-memory vector layer."""
    field_defs = "&".join(f"field={field}" for field in fields)
    uri = f"{geometry_type}?crs={crs}&{field_defs}"
    layer = QgsVectorLayer(uri, "test_layer", "memory")
    if not layer.isValid():
        raise RuntimeError(f"invalid memory layer: {uri}")
    return layer


def make_canvas(
    layer: QgsVectorLayer,
    crs: str = "EPSG:4326",
    extent: tuple[float, float, float, float] = (0.0, 0.0, 10.0, 10.0),
) -> QgsMapCanvas:
    """Create a canvas showing *layer* with a deterministic extent."""
    canvas = QgsMapCanvas()
    canvas.setLayers([layer])
    canvas.setDestinationCrs(QgsCoordinateReferenceSystem(crs))
    canvas.setExtent(QgsRectangle(*extent))
    canvas.resize(400, 400)
    canvas.setCurrentLayer(layer)
    return canvas


def add_polyline(layer: QgsVectorLayer, points: list[tuple[float, float]]) -> QgsFeature:
    """Insert an existing line feature (useful to test snapping)."""
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in points]))
    layer.dataProvider().addFeature(feature)
    return feature


def device_point(canvas: QgsMapCanvas, point: tuple[float, float]) -> tuple[float, float]:
    """Convert a map coordinate to canvas device coordinates."""
    mapped = canvas.mapSettings().mapToPixel().transform(QgsPointXY(*point))
    return mapped.x(), mapped.y()


def mouse_event(
    canvas: QgsMapCanvas,
    event_type: Any,
    x: float,
    y: float,
    button: Any = LEFT_BUTTON,
) -> QgsMapMouseEvent:
    """Build a QgsMapMouseEvent for the canvas."""
    point = QPointF(float(x), float(y))
    try:
        event = QMouseEvent(event_type, point, point, button, button, NO_MODIFIER)
    except TypeError:  # pragma: no cover - PyQt5 signature
        event = QMouseEvent(event_type, point, button, button, NO_MODIFIER)
    return QgsMapMouseEvent(canvas, event)


class FakeMessageBar:
    """Collect warnings instead of showing them."""

    def __init__(self) -> None:
        self.warnings: list[tuple[str, str]] = []
        self.infos: list[tuple[str, str]] = []

    def pushWarning(self, title: str, message: str) -> None:  # noqa: N802
        """Record a warning."""
        self.warnings.append((title, message))

    def pushInfo(self, title: str, message: str) -> None:  # noqa: N802
        """Record an informational message."""
        self.infos.append((title, message))


class FakeDialog:
    """Minimal QgsAttributeDialog replacement."""

    def __init__(self, result: int) -> None:
        self.result = result
        self.calls = 0

    def exec(self) -> int:
        """Pretend to execute the dialog."""
        self.calls += 1
        return self.result

    def exec_(self) -> int:  # pragma: no cover - PyQt5 name
        """Pretend to execute the dialog (PyQt5 name)."""
        return self.exec()


class FakeIface(QObject):
    """QGIS interface double exposing only what the plugin uses.

    Args:
        canvas: Map canvas.
        layer: Layer returned by ``activeLayer()``.
        form_result: ``None`` to skip the attribute form, or the dialog result.
    """

    currentLayerChanged = pyqtSignal(object)

    def __init__(
        self,
        canvas: QgsMapCanvas | None = None,
        layer: QgsVectorLayer | None = None,
        form_result: int | None = None,
    ) -> None:
        super().__init__()
        self._canvas = canvas
        self._layer = layer
        self.form_result = form_result
        self.messages = FakeMessageBar()
        self.form_calls = 0
        self.dialogs: list[FakeDialog] = []
        self._window = QMainWindow()
        self._toolbar = QToolBar(self._window)
        self._window.addToolBar(self._toolbar)

    def activeLayer(self) -> QgsVectorLayer | None:  # noqa: N802
        """Return the configured active layer."""
        return self._layer

    def setActiveLayer(self, layer: QgsVectorLayer | None) -> None:  # noqa: N802
        """Change the active layer and emulate the QGIS signal."""
        self._layer = layer
        self.currentLayerChanged.emit(layer)

    def mapCanvas(self) -> QgsMapCanvas | None:  # noqa: N802
        """Return the map canvas."""
        return self._canvas

    def messageBar(self) -> FakeMessageBar:  # noqa: N802
        """Return the message bar double."""
        return self.messages

    def mainWindow(self) -> QMainWindow:  # noqa: N802
        """Return the main window."""
        return self._window

    def digitizeToolBar(self) -> QToolBar:  # noqa: N802
        """Return the digitize toolbar."""
        return self._toolbar

    def addToolBar(self, name: str) -> QToolBar:  # noqa: N802
        """Create and return a toolbar."""
        toolbar = QToolBar(name, self._window)
        self._window.addToolBar(toolbar)
        return toolbar

    def addPluginToVectorMenu(self, name: str, action: Any) -> None:  # noqa: N802
        """Accept the menu registration."""

    def removePluginVectorMenu(self, name: str, action: Any) -> None:  # noqa: N802
        """Accept the menu removal."""

    def getFeatureForm(  # noqa: N802
        self,
        layer: QgsVectorLayer,
        feature: QgsFeature,
    ) -> FakeDialog | None:
        """Return a fake attribute dialog when configured."""
        self.form_calls += 1
        if self.form_result is None:
            return None
        dialog = FakeDialog(self.form_result)
        self.dialogs.append(dialog)
        return dialog

    def close(self) -> None:
        """Destroy the fake main window."""
        self._window.close()
        self._window.deleteLater()

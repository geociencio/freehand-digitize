"""Map tool that records a freehand stroke and emits the finished geometry."""

from __future__ import annotations

from typing import Any

from qgis.core import QgsMessageLog, QgsPointXY
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtCore import QCoreApplication, pyqtSignal
from qgis.PyQt.QtGui import QColor

from ..core.constants import LOG_TAG, PLUGIN_NAME
from ..core.geometry_rules import (
    KIND_LINE,
    KIND_POLYGON,
    KIND_UNKNOWN,
    geometry_kind,
    has_enough_points,
    is_supported_geometry,
)
from ..core.stroke import SamplingOptions, StrokeRecorder
from .cursor import build_pencil_cursor
from .geometry_factory import build_geometry
from .qt_compat import (
    KEY_CONTROL,
    KEY_ESCAPE,
    LEFT_BUTTON,
    RUBBERBAND_LINE,
    RUBBERBAND_POLYGON,
    SNAP_VERTEX,
)
from .texts import edit_mode_required_text

MODE_CREATE = "create"
MODE_RESHAPE = "reshape"


class FreehandTool(QgsMapTool):
    """Drag-to-draw tool for line and polygon layers.

    The tool owns the rubber band, the CTRL snapping and the stroke sampling.
    It emits :attr:`geometryFinished` with the geometry **in layer coordinates**
    and the layer captured at press time; feature creation (defaults, attribute
    form, edit command) belongs to the plugin/feature creator.

    Signals:
        geometryFinished: ``(QgsGeometry, QgsVectorLayer)`` when a stroke ends
            with enough vertices.
    """

    geometryFinished = pyqtSignal(object, object)

    def __init__(
        self,
        canvas: Any,
        iface: Any = None,
        mode: str = MODE_CREATE,
        sampling_store: Any = None,
    ) -> None:
        """Create the tool.

        Args:
            canvas: Map canvas the tool draws on.
            iface: Optional QGIS interface used for messages and active layer.
            mode: ``MODE_CREATE`` for new features or ``MODE_RESHAPE`` for an
                open line stroke used to reshape existing geometries.
            sampling_store: Optional ``SamplingStore`` used to rebuild the
                recorder at the start of every stroke.
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.iface = iface
        self.mode = mode if mode in (MODE_CREATE, MODE_RESHAPE) else MODE_CREATE
        self._sampling_store = sampling_store
        self._recorder = StrokeRecorder()
        self._rubber: QgsRubberBand | None = None
        self._layer: Any = None
        self._kind = KIND_UNKNOWN
        self._drawing = False
        self._ignore_clicks = False
        self._ctrl_pressed = False
        self._cursor = build_pencil_cursor()
        self.setCursor(self._cursor)

    # -- public API -------------------------------------------------------
    def setIgnoreClick(self, ignore: bool) -> None:  # noqa: N802 - Qt-style API
        """Ignore canvas clicks while a modal dialog is open.

        Args:
            ignore: ``True`` while the attribute form is blocking.
        """
        self._ignore_clicks = bool(ignore)

    @property
    def is_drawing(self) -> bool:
        """Return whether a stroke is currently in progress."""
        return self._drawing

    def cancel_stroke(self) -> None:
        """Discard the current stroke and hide the rubber band."""
        self._drawing = False
        self._recorder.reset()
        self._clear_rubber()
        self._layer = None
        self._kind = KIND_UNKNOWN

    # -- lifecycle --------------------------------------------------------
    def activate(self) -> None:
        """Apply the pencil cursor when QGIS activates the tool."""
        super().activate()
        self.setCursor(self._cursor)

    def deactivate(self) -> None:
        """Cancel an unfinished stroke when QGIS switches tools."""
        self.cancel_stroke()
        super().deactivate()

    # -- canvas events ----------------------------------------------------
    def canvasPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        """Start a stroke, or ignore repeat/secondary presses."""
        if self._ignore_clicks:
            return
        if self._drawing:
            # Upstream freehandEditing ignored presses while drawing; the
            # matching release event still ends the stroke.
            return
        if event.button() != LEFT_BUTTON:
            return

        layer = self._active_layer()
        if layer is None:
            self._warn(
                QCoreApplication.translate(
                    "FreehandDigitize", "Selecciona primero la capa donde quieres dibujar."
                )
            )
            return
        if not is_supported_geometry(int(layer.geometryType())):
            self._warn(
                QCoreApplication.translate(
                    "FreehandDigitize", "Esta herramienta solo dibuja en capas de línea o polígono."
                )
            )
            return
        if not self._require_editable(layer):
            return

        self._layer = layer
        self._kind = (
            KIND_LINE if self.mode == MODE_RESHAPE else geometry_kind(int(layer.geometryType()))
        )
        self._drawing = True
        self._recorder = self._new_recorder()

        device = event.pos()
        map_point = event.mapPoint()
        layer_point = self.toLayerCoordinates(layer, device)
        if self._ctrl_pressed:
            layer_point, map_point = self._snapped_point(layer, device, layer_point, map_point)

        self._recorder.start(
            (layer_point.x(), layer_point.y()),
            (device.x(), device.y()),
        )
        self._create_rubber(self._kind)
        if self._rubber is not None:
            self._rubber.addPoint(map_point)

    def canvasMoveEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        """Record a vertex when the pointer moved far enough."""
        if not self._drawing or self._ignore_clicks or self._rubber is None:
            return
        layer = self._layer
        if layer is None:
            return
        device = event.pos()
        layer_point = self.toLayerCoordinates(layer, device)
        if self._recorder.add(
            (layer_point.x(), layer_point.y()),
            (device.x(), device.y()),
        ):
            self._rubber.addPoint(event.mapPoint())

    def canvasReleaseEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        """Finish the stroke on any button release (upstream behaviour)."""
        if self._ignore_clicks or not self._drawing:
            return

        layer = self._layer
        kind = self._kind
        if layer is not None and self._ctrl_pressed:
            device = event.pos()
            layer_point = self.toLayerCoordinates(layer, device)
            layer_point, map_point = self._snapped_point(
                layer, device, layer_point, event.mapPoint()
            )
            if (
                self._recorder.add(
                    (layer_point.x(), layer_point.y()),
                    (device.x(), device.y()),
                )
                and self._rubber is not None
            ):
                self._rubber.addPoint(map_point)

        points = self._recorder.points
        geometry = build_geometry(points, kind) if has_enough_points(points, kind) else None

        self._drawing = False
        self._recorder.reset()
        self._clear_rubber()
        self._layer = None
        self._kind = KIND_UNKNOWN

        if geometry is not None and not geometry.isEmpty() and layer is not None:
            self.geometryFinished.emit(geometry, layer)

    def keyPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        """Track CTRL for snapping and handle Escape."""
        if event.key() == KEY_CONTROL:
            self._ctrl_pressed = True
            return
        if event.key() == KEY_ESCAPE:
            if self._drawing:
                self.cancel_stroke()
                self.canvas.refresh()
                return
            self.canvas.unsetMapTool(self)
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        """Stop snapping when CTRL is released."""
        if event.key() == KEY_CONTROL:
            self._ctrl_pressed = False
            return
        super().keyReleaseEvent(event)

    # -- helpers ----------------------------------------------------------
    def _new_recorder(self) -> StrokeRecorder:
        """Build a recorder from the current sampling options."""
        options = SamplingOptions()
        if self._sampling_store is not None:
            try:
                options = self._sampling_store.load()
            except (AttributeError, RuntimeError, TypeError, ValueError):
                pass
        return StrokeRecorder(options)

    def _require_editable(self, layer: Any) -> bool:
        """Return whether the layer is already in edit mode."""
        if layer.isEditable():
            return True
        self._warn(edit_mode_required_text(layer.name()))
        return False

    def _active_layer(self) -> Any:
        """Return the layer the user is drawing on, if any."""
        if self.iface is not None:
            layer = self.iface.activeLayer()
            if layer is not None:
                return layer
        return self.canvas.currentLayer()

    def _snapped_point(
        self,
        layer: Any,
        device_point: Any,
        layer_point: QgsPointXY,
        map_point: QgsPointXY,
    ) -> tuple[QgsPointXY, QgsPointXY]:
        """Snap to a vertex when the snapping engine finds one.

        Args:
            layer: Layer being edited.
            device_point: Pointer position in device coordinates.
            layer_point: Pointer position in layer coordinates (fallback).
            map_point: Pointer position in map coordinates (fallback).

        Returns:
            ``(layer_point, map_point)`` snapped when a match exists.
        """
        try:
            snapping = self.canvas.snappingUtils()
            if snapping is None:
                return layer_point, map_point
            match = snapping.snapToCurrentLayer(device_point, SNAP_VERTEX)
            if not match.isValid():
                match = snapping.snapToMap(device_point)
            if match.isValid():
                snapped_map = match.point()
                return self.toLayerCoordinates(layer, snapped_map), snapped_map
        except (AttributeError, RuntimeError, TypeError) as exc:
            self._log(f"snapping failed: {exc}")
        return layer_point, map_point

    def _create_rubber(self, kind: str) -> None:
        """Create the rubber band matching the layer geometry type."""
        self._clear_rubber()
        rubber_type = RUBBERBAND_POLYGON if kind == KIND_POLYGON else RUBBERBAND_LINE
        rubber = QgsRubberBand(self.canvas, rubber_type)
        if kind == KIND_POLYGON:
            rubber.setColor(QColor(255, 0, 0, 63))
            rubber.setWidth(2)
        else:
            rubber.setColor(QColor(255, 0, 0, 150))
            rubber.setWidth(1)
        self._rubber = rubber

    def _clear_rubber(self) -> None:
        """Reset and drop the current rubber band."""
        if self._rubber is not None:
            try:
                self._rubber.reset()
            except RuntimeError:
                pass
            self._rubber = None

    def _warn(self, message: str) -> None:
        """Show a warning in the QGIS message bar."""
        self._log(message)
        if self.iface is None:
            return
        try:
            self.iface.messageBar().pushWarning(PLUGIN_NAME, message)
        except (AttributeError, RuntimeError):
            pass

    @staticmethod
    def _log(message: str) -> None:
        """Write a message to the QGIS log."""
        QgsMessageLog.logMessage(str(message), LOG_TAG)

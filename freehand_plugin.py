# -*- coding: utf-8 -*-
"""Freehand Digitize — digitalización a mano alzada para QGIS 3.28+ / QGIS 4.x.

Compatible con PyQt5 (QGIS 3) y PyQt6 (QGIS 4): los enums de Qt se resuelven
en tiempo de importación para evitar el cambio de enums con ámbito de PyQt6.
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QCursor
from qgis.PyQt.QtWidgets import QAction

from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsMessageLog,
    QgsPointXY,
    QgsProject,
)
from qgis.gui import QgsMapTool, QgsRubberBand

# --- enums compatibles PyQt5 / PyQt6 -------------------------------------
try:                                    # PyQt6 / QGIS 4
    LEFT = Qt.MouseButton.LeftButton
    RIGHT = Qt.MouseButton.RightButton
    ESC = Qt.Key.Key_Escape
    CROSS = Qt.CursorShape.CrossCursor
except AttributeError:                  # PyQt5 / QGIS 3
    LEFT = Qt.LeftButton
    RIGHT = Qt.RightButton
    ESC = Qt.Key_Escape
    CROSS = Qt.CrossCursor

POLYGON, LINE, POINT = 2, 1, 0           # valores de geometryType, iguales en ambas APIs


def log(msg):
    QgsMessageLog.logMessage(str(msg), "Freehand Digitize")


class FreehandTool(QgsMapTool):
    """Arrastra para dibujar; al soltar se crea la entidad en la capa activa."""

    def __init__(self, canvas, iface):
        super().__init__(canvas)
        self.canvas = canvas
        self.iface = iface
        self.points = []
        self.drawing = False
        self.rb = QgsRubberBand(canvas)
        self.rb.setColor(QColor(220, 30, 30, 140))
        self.rb.setWidth(2)
        try:
            self.setCursor(QCursor(CROSS))
        except Exception:
            pass

    # -- helpers ----------------------------------------------------------
    def _reset(self):
        self.points = []
        self.drawing = False
        self.rb.reset()

    def _too_close(self, p):
        if not self.points:
            return False
        last = self.points[-1]
        tol = self.canvas.mapUnitsPerPixel() * 1.5
        return abs(p.x() - last.x()) < tol and abs(p.y() - last.y()) < tol

    # -- eventos del canvas ----------------------------------------------
    def canvasPressEvent(self, e):
        try:
            if e.button() == LEFT:
                self._reset()
                self.drawing = True
                self.points = [QgsPointXY(e.mapPoint())]
            elif e.button() == RIGHT:
                self._reset()
        except Exception as exc:                      # noqa: BLE001
            log(f"press: {exc}")

    def canvasMoveEvent(self, e):
        if not self.drawing:
            return
        try:
            p = QgsPointXY(e.mapPoint())
            if not self._too_close(p):
                self.points.append(p)
                self.rb.setToGeometry(QgsGeometry.fromPolylineXY(self.points), None)
        except Exception as exc:                      # noqa: BLE001
            log(f"move: {exc}")

    def canvasReleaseEvent(self, e):
        if not self.drawing or e.button() != LEFT:
            return
        self.drawing = False
        try:
            self._finish()
        except Exception as exc:                      # noqa: BLE001
            log(f"release: {exc}")
            self._message(f"Error al crear la entidad: {exc}")
        finally:
            self.rb.reset()

    def keyPressEvent(self, e):
        if e.key() == ESC:
            self._reset()
            self.canvas.unsetMapTool(self)
            return
        super().keyPressEvent(e)

    # -- creación de la entidad ------------------------------------------
    def _finish(self):
        layer = self.iface.activeLayer()
        if layer is None:
            self._message("Selecciona primero la capa donde quieres dibujar.")
            return

        gtype = int(layer.geometryType())
        if gtype == POINT:
            self._message("Esta herramienta es para capas de línea o polígono.")
            return

        pts = self.points
        if len(pts) < 3:
            return                                     # trazo demasiado corto

        if gtype == POLYGON:
            if pts[0] != pts[-1]:
                pts.append(pts[0])                     # cierra el anillo
            geom = QgsGeometry.fromPolygonXY([pts])
        else:
            geom = QgsGeometry.fromPolylineXY(pts)

        if geom is None or geom.isEmpty():
            return

        # suaviza el temblor del trazo (aprox. 2 px de pantalla)
        tol = self.canvas.mapUnitsPerPixel() * 2.0
        simple = geom.simplify(tol)
        if simple is not None and not simple.isEmpty():
            geom = simple

        if not geom.isGeosValid():
            fixed = geom.makeValid()
            if fixed is not None and not fixed.isEmpty():
                geom = fixed

        if not layer.isEditable():
            if not layer.startEditing():
                self._message(f"No se pudo poner «{layer.name()}» en edición.")
                return

        feat = QgsFeature(layer.fields())
        feat.setGeometry(geom)
        feat.setValid(True)

        ok = layer.addFeature(feat)
        layer.triggerRepaint()
        if ok:
            self.iface.mapCanvas().refresh()
        else:
            self._message(f"La capa «{layer.name()}» rechazó la entidad "
                          f"(¿tipo de geometría incompatible?).")

    def _message(self, text):
        try:
            self.iface.messageBar().pushWarning("Freehand Digitize", text)
        except Exception:
            log(text)

    def deactivate(self):
        self._reset()
        super().deactivate()


class FreehandDigitizePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.tool = None
        self.toolbar = None

    def initGui(self):
        icon = QgsApplication.getThemeIcon("mActionCapturePolygon.svg")
        self.action = QAction(icon, "Dibujo a mano alzada", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.setToolTip("Arrastra para dibujar polígonos o líneas a mano alzada "
                               "sobre la capa activa (ESC cancela)")
        self.action.triggered.connect(self.activate_tool)

        self.toolbar = self.iface.addToolBar("Freehand Digitize")
        self.toolbar.setObjectName("FreehandDigitizeToolbar")
        self.toolbar.addAction(self.action)
        self.iface.addPluginToVectorMenu("&Freehand Digitize", self.action)

    def activate_tool(self):
        if self.tool is None:
            self.tool = FreehandTool(self.iface.mapCanvas(), self.iface)
            self.tool.setAction(self.action)

        self.iface.mapCanvas().setMapTool(self.tool)
        self.action.setChecked(True)

        layer = self.iface.activeLayer()
        if layer is None:
            self.iface.messageBar().pushWarning(
                "Freehand Digitize",
                "No hay capa activa: selecciona la capa donde vas a dibujar.")
        elif not layer.isEditable():
            layer.startEditing()

    def unload(self):
        if self.tool is not None:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.tool = None
        if self.action is not None:
            self.iface.removePluginVectorMenu("&Freehand Digitize", self.action)
            self.action.deleteLater()
            self.action = None
        if self.toolbar is not None:
            self.toolbar.deleteLater()
            self.toolbar = None

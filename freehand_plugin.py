"""Freehand Digitize — freehand digitizing for QGIS 3.28+ / QGIS 4.x.

The plugin wires three collaborators:

* :class:`~freehand_digitize.gui.freehand_tool.FreehandTool` records the stroke;
* :class:`~freehand_digitize.gui.feature_creator.FeatureCreator` inserts it;
* :class:`~freehand_digitize.core.settings.ToleranceStore` persists the
  simplification tolerance.

Importing ``qgis.PyQt`` (never ``PyQt5``/``PyQt6`` directly) keeps the same
code working on Qt5 and Qt6.
"""

from __future__ import annotations

from qgis.core import (
    QgsApplication,
    QgsMessageLog,
    QgsSettings,
    QgsVectorLayer,
)
from qgis.PyQt.QtWidgets import QDoubleSpinBox

from .core.constants import (
    ACTION_TEXT,
    ACTION_TOOLTIP,
    DEFAULT_TOLERANCE,
    LOG_TAG,
    PLUGIN_NAME,
    TOLERANCE_DECIMALS,
    TOLERANCE_MAX,
    TOLERANCE_MIN,
    TOLERANCE_STEP,
    TOLERANCE_TOOLTIP,
    TOLERANCE_TOOLTIP_GEOGRAPHIC,
)
from .core.geometry_rules import effective_tolerance, is_supported_geometry
from .core.settings import ToleranceStore
from .gui.feature_creator import FeatureCreator
from .gui.freehand_tool import FreehandTool
from .gui.qt_compat import QAction

MENU_NAME = "&Freehand Digitize"
TOOLBAR_NAME = "Freehand Digitize"


class FreehandDigitizePlugin:
    """QGIS plugin entry point.

    Args:
        iface: QGIS interface passed to ``classFactory``.
    """

    def __init__(self, iface) -> None:
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.action = None
        self.spinbox = None
        self.spinbox_action = None
        self.tool = None
        self._creator = None
        self._toolbar = None
        self._own_toolbar = False
        self._settings = None
        self._store = None

    # -- QGIS lifecycle ---------------------------------------------------
    def initGui(self) -> None:
        """Create the toolbar action, the tolerance spinbox and the map tool."""
        self._settings = QgsSettings()
        self._store = ToleranceStore(self._settings)
        self._creator = FeatureCreator(self.iface, self._settings)
        self.tool = FreehandTool(self.canvas, self.iface)
        self.tool.geometryFinished.connect(self._on_geometry_finished)

        self.action = QAction(
            QgsApplication.getThemeIcon("mActionCaptureLine.svg"),
            ACTION_TEXT,
            self.iface.mainWindow(),
        )
        self.action.setObjectName("freehandDigitizeAction")
        self.action.setCheckable(True)
        self.action.setToolTip(ACTION_TOOLTIP)
        self.action.triggered.connect(self._on_action_triggered)
        self.tool.setAction(self.action)

        self._toolbar = self.iface.digitizeToolBar()
        if self._toolbar is None:
            self._toolbar = self.iface.addToolBar(TOOLBAR_NAME)
            self._toolbar.setObjectName("FreehandDigitizeToolbar")
            self._own_toolbar = True
        self._toolbar.addAction(self.action)
        self.iface.addPluginToVectorMenu(MENU_NAME, self.action)

        self._create_spinbox()
        self.iface.currentLayerChanged.connect(self._update_ui_state)
        self.canvas.mapToolSet.connect(self._on_map_tool_set)
        self._update_ui_state()

    def unload(self) -> None:
        """Remove every widget, action and signal connection."""
        self._disconnect(self.iface.currentLayerChanged, self._update_ui_state)
        self._disconnect(self.canvas.mapToolSet, self._on_map_tool_set)
        if self.tool is not None:
            self._disconnect(self.tool.geometryFinished, self._on_geometry_finished)
        self._deactivate_tool()

        if self.tool is not None:
            self.tool.cancel_stroke()
            self.tool = None

        if self.spinbox_action is not None and self._toolbar is not None:
            self._toolbar.removeAction(self.spinbox_action)
            self.spinbox_action = None
        if self.spinbox is not None:
            self.spinbox.deleteLater()
            self.spinbox = None

        if self.action is not None:
            self.iface.removePluginVectorMenu(MENU_NAME, self.action)
            if self._toolbar is not None:
                self._toolbar.removeAction(self.action)
            self.action.deleteLater()
            self.action = None

        if self._own_toolbar and self._toolbar is not None:
            self._toolbar.deleteLater()
        self._toolbar = None

    # -- action / tool ----------------------------------------------------
    def _on_action_triggered(self, checked: bool) -> None:
        """Activate or deactivate the map tool from the toolbar action."""
        if checked:
            self._activate_tool()
        else:
            self._deactivate_tool()

    def _activate_tool(self) -> None:
        """Validate the active layer, start editing and install the map tool."""
        if self.tool is None:
            return
        layer = self.iface.activeLayer()
        if not self._is_drawable(layer):
            if self.action is not None:
                self.action.setChecked(False)
            self._warn(
                "Selecciona una capa vectorial de línea o polígono editable antes de dibujar."
            )
            self._update_ui_state()
            return
        if not layer.isEditable():
            try:
                if not layer.startEditing():
                    if self.action is not None:
                        self.action.setChecked(False)
                    self._warn(f"No se pudo poner «{layer.name()}» en edición.")
                    return
            except (AttributeError, RuntimeError) as exc:
                if self.action is not None:
                    self.action.setChecked(False)
                self._warn(f"No se pudo poner «{layer.name()}» en edición: {exc}")
                return
        self.canvas.setMapTool(self.tool)
        if self.action is not None:
            self.action.setChecked(True)
        self._update_ui_state()

    def _deactivate_tool(self) -> None:
        """Unset the map tool and uncheck the action."""
        if self.tool is not None:
            try:
                if self.canvas.mapTool() is self.tool:
                    self.canvas.unsetMapTool(self.tool)
            except (AttributeError, RuntimeError):
                pass
        if self.action is not None:
            self.action.setChecked(False)

    def _on_map_tool_set(self, new_tool, old_tool=None) -> None:  # noqa: ARG002
        """Keep the action check state in sync with the canvas tool."""
        if self.action is None:
            return
        self.action.setChecked(self.tool is not None and new_tool is self.tool)

    def _on_geometry_finished(self, geometry, layer) -> None:
        """Create the feature for a finished stroke."""
        if self._creator is None or self.spinbox is None:
            return
        tolerance = self._effective_tolerance(layer)
        self._creator.create(
            layer,
            geometry,
            tolerance,
            self.tool.setIgnoreClick if self.tool is not None else None,
        )

    # -- tolerance spinbox ------------------------------------------------
    def _create_spinbox(self) -> None:
        """Create the tolerance spinbox and add it to the digitize toolbar."""
        spinbox = QDoubleSpinBox(self.iface.mainWindow())
        spinbox.setObjectName("freehandDigitizeTolerance")
        spinbox.setDecimals(TOLERANCE_DECIMALS)
        spinbox.setRange(TOLERANCE_MIN, TOLERANCE_MAX)
        spinbox.setSingleStep(TOLERANCE_STEP)
        spinbox.setToolTip(TOLERANCE_TOOLTIP)
        spinbox.setValue(self._store.load() if self._store is not None else DEFAULT_TOLERANCE)
        spinbox.valueChanged.connect(self._on_tolerance_changed)
        self.spinbox = spinbox
        if self._toolbar is not None:
            self.spinbox_action = self._toolbar.addWidget(spinbox)

    def _on_tolerance_changed(self, value: float) -> None:
        """Persist the tolerance when the spinbox changes."""
        if self._store is not None:
            self._store.save(value)

    def _effective_tolerance(self, layer) -> float:
        """Return the tolerance to apply to *layer* (0 for geographic CRS)."""
        if self.spinbox is None:
            return DEFAULT_TOLERANCE
        geographic = True
        try:
            geographic = bool(layer.crs().isGeographic())
        except (AttributeError, RuntimeError):
            pass
        return effective_tolerance(self.spinbox.value(), geographic)

    # -- UI state ---------------------------------------------------------
    def _update_ui_state(self, *_args) -> None:
        """Enable the action and spinbox according to the active layer."""
        if self.action is None:
            return
        layer = self.iface.activeLayer()
        drawable = self._is_drawable(layer)
        self.action.setEnabled(drawable)

        geographic = self._is_geographic(layer)
        tolerance_enabled = drawable and not geographic
        if self.spinbox_action is not None:
            self.spinbox_action.setEnabled(tolerance_enabled)
        if self.spinbox is not None:
            self.spinbox.setEnabled(tolerance_enabled)
            self.spinbox.setToolTip(
                TOLERANCE_TOOLTIP_GEOGRAPHIC if geographic else TOLERANCE_TOOLTIP
            )

        if not drawable and self.action.isChecked():
            self._deactivate_tool()

    @staticmethod
    def _is_geographic(layer) -> bool:
        """Return whether *layer* uses a geographic CRS."""
        if layer is None:
            return False
        try:
            return bool(layer.crs().isGeographic())
        except (AttributeError, RuntimeError):
            return False

    @staticmethod
    def _is_drawable(layer) -> bool:
        """Return whether *layer* supports editable freehand drawing."""
        if layer is None or not isinstance(layer, QgsVectorLayer):
            return False
        try:
            if not layer.isValid():
                return False
            if not is_supported_geometry(int(layer.geometryType())):
                return False
            supports_editing = getattr(layer, "supportsEditing", None)
            if callable(supports_editing):
                return bool(supports_editing())
        except (AttributeError, RuntimeError, TypeError):
            return False
        return True

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _disconnect(signal, slot) -> None:
        """Disconnect *slot* from *signal*, ignoring missing connections."""
        try:
            signal.disconnect(slot)
        except (TypeError, RuntimeError):
            pass

    def _warn(self, message: str) -> None:
        """Show a warning in the QGIS message bar."""
        QgsMessageLog.logMessage(str(message), LOG_TAG)
        try:
            self.iface.messageBar().pushWarning(PLUGIN_NAME, message)
        except (AttributeError, RuntimeError):
            pass

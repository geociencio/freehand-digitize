"""Freehand Digitize — freehand digitizing for QGIS 3.28+ / QGIS 4.x.

The plugin wires four collaborators:

* :class:`~freehand_digitize.gui.freehand_tool.FreehandTool` records strokes;
* :class:`~freehand_digitize.gui.feature_creator.FeatureCreator` inserts new
  features;
* :class:`~freehand_digitize.gui.reshape_creator.ReshapeCreator` reshapes
  existing features under a stroke;
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
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QDoubleSpinBox

from .core.constants import (
    DEFAULT_TOLERANCE,
    LOG_TAG,
    PLUGIN_NAME,
    TOLERANCE_DECIMALS,
    TOLERANCE_MAX,
    TOLERANCE_MIN,
    TOLERANCE_STEP,
)
from .core.geometry_rules import effective_tolerance, is_supported_geometry
from .core.settings import SamplingStore, ToleranceStore
from .gui.feature_creator import FeatureCreator
from .gui.freehand_tool import MODE_RESHAPE, FreehandTool
from .gui.i18n import install_translations, remove_translations
from .gui.qt_compat import QAction, exec_dialog
from .gui.reshape_creator import ReshapeCreator
from .gui.sampling_dialog import SamplingDialog
from .gui.texts import (
    action_text,
    action_tooltip,
    edit_mode_required_text,
    reshape_action_text,
    reshape_action_tooltip,
    sampling_action_text,
    sampling_action_tooltip,
    tolerance_tooltip,
    tolerance_tooltip_geographic,
)

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
        self.reshape_action = None
        self.sampling_action = None
        self.spinbox = None
        self.spinbox_action = None
        self.tool = None
        self.reshape_tool = None
        self._creator = None
        self._reshape_creator = None
        self._toolbar = None
        self._own_toolbar = False
        self._settings = None
        self._store = None
        self._sampling_store = None
        self._translator = None
        self._editing_layer = None

    # -- QGIS lifecycle ---------------------------------------------------
    def initGui(self) -> None:
        """Create the toolbar actions, the tolerance spinbox and the tools."""
        self._settings = QgsSettings()
        if self._translator is not None:
            remove_translations(self._translator)
        self._translator = install_translations(self._settings)
        self._store = ToleranceStore(self._settings)
        self._sampling_store = SamplingStore(self._settings)
        self._creator = FeatureCreator(self.iface, self._settings)
        self._reshape_creator = ReshapeCreator(self.iface)

        self.tool = FreehandTool(self.canvas, self.iface, sampling_store=self._sampling_store)
        self.tool.geometryFinished.connect(self._on_geometry_finished)
        self.reshape_tool = FreehandTool(
            self.canvas,
            self.iface,
            mode=MODE_RESHAPE,
            sampling_store=self._sampling_store,
        )
        self.reshape_tool.geometryFinished.connect(self._on_reshape_finished)

        self.action = self._make_action(
            "mActionCaptureLine.svg",
            action_text(),
            action_tooltip(),
            "freehandDigitizeAction",
        )
        self.reshape_action = self._make_action(
            "mActionReshape.svg",
            reshape_action_text(),
            reshape_action_tooltip(),
            "freehandDigitizeReshapeAction",
        )
        self.sampling_action = self._make_action(
            "mActionOptions.svg",
            sampling_action_text(),
            sampling_action_tooltip(),
            "freehandDigitizeSamplingAction",
        )
        self.action.triggered.connect(self._on_action_triggered)
        self.reshape_action.triggered.connect(self._on_reshape_triggered)
        self.sampling_action.triggered.connect(self._on_sampling_settings)
        self.tool.setAction(self.action)
        self.reshape_tool.setAction(self.reshape_action)

        self._toolbar = self.iface.digitizeToolBar()
        if self._toolbar is None:
            self._toolbar = self.iface.addToolBar(TOOLBAR_NAME)
            self._toolbar.setObjectName("FreehandDigitizeToolbar")
            self._own_toolbar = True
        self._toolbar.addAction(self.action)
        self._toolbar.addAction(self.reshape_action)
        self._toolbar.addAction(self.sampling_action)
        self.iface.addPluginToVectorMenu(MENU_NAME, self.action)
        self.iface.addPluginToVectorMenu(MENU_NAME, self.reshape_action)
        self.iface.addPluginToVectorMenu(MENU_NAME, self.sampling_action)

        self._create_spinbox()
        self.iface.currentLayerChanged.connect(self._on_current_layer_changed)
        self.canvas.mapToolSet.connect(self._on_map_tool_set)
        self._on_current_layer_changed()

    def unload(self) -> None:
        """Remove every widget, action and signal connection."""
        self._disconnect_signals()
        self._deactivate_tool()
        self._cleanup_tools()
        self._cleanup_actions()
        self._remove_translator()

    # -- cleanup helpers --------------------------------------------------
    def _disconnect_signals(self) -> None:
        """Disconnect interface, canvas and tool signals."""
        self._disconnect(self.iface.currentLayerChanged, self._on_current_layer_changed)
        self._disconnect(self.canvas.mapToolSet, self._on_map_tool_set)
        self._disconnect_editing_signals()
        if self.tool is not None:
            self._disconnect(self.tool.geometryFinished, self._on_geometry_finished)
        if self.reshape_tool is not None:
            self._disconnect(self.reshape_tool.geometryFinished, self._on_reshape_finished)

    def _cleanup_tools(self) -> None:
        """Cancel and release both map tools."""
        for tool in (self.tool, self.reshape_tool):
            if tool is not None:
                tool.cancel_stroke()
        self.tool = None
        self.reshape_tool = None

    def _cleanup_actions(self) -> None:
        """Remove the spinbox, both actions and the fallback toolbar."""
        if self.spinbox_action is not None and self._toolbar is not None:
            self._toolbar.removeAction(self.spinbox_action)
            self.spinbox_action = None
        if self.spinbox is not None:
            self.spinbox.deleteLater()
            self.spinbox = None

        for action in (self.action, self.reshape_action, self.sampling_action):
            if action is not None:
                self.iface.removePluginVectorMenu(MENU_NAME, action)
                if self._toolbar is not None:
                    self._toolbar.removeAction(action)
                action.deleteLater()
        self.action = None
        self.reshape_action = None
        self.sampling_action = None

        if self._own_toolbar and self._toolbar is not None:
            self._toolbar.deleteLater()
        self._toolbar = None

    def _remove_translator(self) -> None:
        """Remove the installed translation catalog, if any."""
        if self._translator is not None:
            remove_translations(self._translator)
            self._translator = None
        self._editing_layer = None

    # -- actions and tools ------------------------------------------------
    def _on_action_triggered(self, checked: bool) -> None:
        """Activate or deactivate the creation tool from the toolbar action."""
        if checked:
            self._activate_tool()
        else:
            self._deactivate_tool()

    def _on_reshape_triggered(self, checked: bool) -> None:
        """Activate or deactivate the reshape tool from the toolbar action."""
        if checked:
            self._activate_reshape_tool()
        else:
            self._deactivate_tool()

    def _activate_tool(self) -> None:
        """Validate the active layer, start editing and install the creation tool."""
        if self.tool is None:
            return
        layer = self.iface.activeLayer()
        if not self._is_drawable(layer):
            self._set_checked(self.action, False)
            self._warn(self._activation_warning(layer))
            self._update_ui_state()
            return
        self.canvas.setMapTool(self.tool)
        self._set_checked(self.action, True)
        self._update_ui_state()

    def _activate_reshape_tool(self) -> None:
        """Validate the active layer, start editing and install the reshape tool."""
        if self.reshape_tool is None:
            return
        layer = self.iface.activeLayer()
        if not self._is_drawable(layer):
            self._set_checked(self.reshape_action, False)
            self._warn(self._activation_warning(layer))
            self._update_ui_state()
            return
        self.canvas.setMapTool(self.reshape_tool)
        self._set_checked(self.reshape_action, True)
        self._update_ui_state()

    def _deactivate_tool(self) -> None:
        """Cancel strokes, unset the active map tool and uncheck both actions."""
        for tool in (self.tool, self.reshape_tool):
            if tool is not None:
                tool.cancel_stroke()
                try:
                    if self.canvas.mapTool() is tool:
                        self.canvas.unsetMapTool(tool)
                except (AttributeError, RuntimeError):
                    pass
        self._set_checked(self.action, False)
        self._set_checked(self.reshape_action, False)

    def _on_map_tool_set(self, new_tool, old_tool=None) -> None:  # noqa: ARG002
        """Keep both action check states in sync with the canvas tool."""
        if self.action is not None:
            self.action.setChecked(new_tool is self.tool)
        if self.reshape_action is not None:
            self.reshape_action.setChecked(new_tool is self.reshape_tool)

    def _on_geometry_finished(self, geometry, layer) -> None:
        """Create the feature for a finished creation stroke."""
        if self._creator is None or self.spinbox is None:
            return
        tolerance = self._effective_tolerance(layer)
        self._creator.create(
            layer,
            geometry,
            tolerance,
            self.tool.setIgnoreClick if self.tool is not None else None,
        )

    def _on_reshape_finished(self, geometry, layer) -> None:
        """Reshape the geometries under a finished reshape stroke."""
        if self._reshape_creator is not None:
            self._reshape_creator.reshape(layer, geometry)

    def _on_sampling_settings(self, _checked: bool = False) -> None:
        """Open the sampling settings dialog."""
        dialog = SamplingDialog(
            self.iface.activeLayer(),
            self._sampling_store,
            self.iface.mainWindow(),
        )
        exec_dialog(dialog)

    # -- tolerance spinbox ------------------------------------------------
    def _make_action(
        self,
        icon_name: str,
        text: str,
        tooltip: str,
        object_name: str,
    ) -> QAction:
        """Build a checkable toolbar action."""
        action = QAction(
            QgsApplication.getThemeIcon(icon_name),
            text,
            self.iface.mainWindow(),
        )
        action.setObjectName(object_name)
        action.setCheckable(True)
        action.setToolTip(tooltip)
        return action

    def _create_spinbox(self) -> None:
        """Create the tolerance spinbox and add it to the digitize toolbar."""
        spinbox = QDoubleSpinBox(self.iface.mainWindow())
        spinbox.setObjectName("freehandDigitizeTolerance")
        spinbox.setDecimals(TOLERANCE_DECIMALS)
        spinbox.setRange(TOLERANCE_MIN, TOLERANCE_MAX)
        spinbox.setSingleStep(TOLERANCE_STEP)
        spinbox.setToolTip(tolerance_tooltip())
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

    # -- editing session --------------------------------------------------
    def _on_current_layer_changed(self, *_args) -> None:
        """Reconnect the active layer's editing signals and refresh the UI."""
        layer = self.iface.activeLayer()
        if layer is not self._editing_layer:
            self._disconnect_editing_signals()
            self._editing_layer = layer
            if isinstance(layer, QgsVectorLayer):
                try:
                    layer.editingStarted.connect(self._on_editing_started)
                    layer.editingStopped.connect(self._on_editing_stopped)
                except (AttributeError, RuntimeError, TypeError) as exc:
                    self._log(f"editing signal connection failed: {exc}")
        self._update_ui_state()

    def _disconnect_editing_signals(self) -> None:
        """Disconnect the stored layer's editing signals."""
        layer = self._editing_layer
        if layer is not None:
            self._disconnect(layer.editingStarted, self._on_editing_started)
            self._disconnect(layer.editingStopped, self._on_editing_stopped)
            self._editing_layer = None

    def _on_editing_started(self, *_args) -> None:
        """Enable the tools when the active layer enters edit mode."""
        self._update_ui_state()

    def _on_editing_stopped(self, *_args) -> None:
        """Deactivate the tools when the active layer leaves edit mode."""
        self._deactivate_tool()
        self._update_ui_state()

    # -- UI state ---------------------------------------------------------
    def _update_ui_state(self, *_args) -> None:
        """Enable the actions and spinbox according to the active layer."""
        if self.action is None:
            return
        layer = self.iface.activeLayer()
        drawable = self._is_drawable(layer)
        self.action.setEnabled(drawable)
        if self.reshape_action is not None:
            self.reshape_action.setEnabled(drawable)

        geographic = self._is_geographic(layer)
        tolerance_enabled = drawable and not geographic
        if self.spinbox_action is not None:
            self.spinbox_action.setEnabled(tolerance_enabled)
        if self.spinbox is not None:
            self.spinbox.setEnabled(tolerance_enabled)
            self.spinbox.setToolTip(
                tolerance_tooltip_geographic() if geographic else tolerance_tooltip()
            )

        if not drawable and self._any_action_checked():
            self._deactivate_tool()

    def _activation_warning(self, layer) -> str:
        """Return the appropriate warning for an unavailable layer."""
        if layer is not None and isinstance(layer, QgsVectorLayer):
            try:
                if (
                    layer.isValid()
                    and is_supported_geometry(int(layer.geometryType()))
                    and layer.supportsEditing()
                    and not layer.isEditable()
                ):
                    return edit_mode_required_text(layer.name())
            except (AttributeError, RuntimeError, TypeError):
                pass
        return _invalid_layer_text()

    def _any_action_checked(self) -> bool:
        """Return whether either toolbar action is checked."""
        return bool(
            (self.action is not None and self.action.isChecked())
            or (self.reshape_action is not None and self.reshape_action.isChecked())
        )

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
            if callable(supports_editing) and not bool(supports_editing()):
                return False
            if not layer.isEditable():
                return False
        except (AttributeError, RuntimeError, TypeError):
            return False
        return True

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _set_checked(action, checked: bool) -> None:
        """Set an action check state when the action exists."""
        if action is not None:
            action.setChecked(checked)

    @staticmethod
    def _disconnect(signal, slot) -> None:
        """Disconnect *slot* from *signal*, ignoring missing connections."""
        try:
            signal.disconnect(slot)
        except (TypeError, RuntimeError):
            pass

    def _warn(self, message: str) -> None:
        """Show a warning in the QGIS message bar."""
        self._log(message)
        try:
            self.iface.messageBar().pushWarning(PLUGIN_NAME, message)
        except (AttributeError, RuntimeError):
            pass

    @staticmethod
    def _log(message: str) -> None:
        """Write a message to the QGIS log."""
        QgsMessageLog.logMessage(str(message), LOG_TAG)


def _invalid_layer_text() -> str:
    """Return the warning shown when no drawable layer is active."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Selecciona una capa vectorial de línea o polígono editable antes de dibujar.",
    )

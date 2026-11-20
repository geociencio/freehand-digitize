"""Create features from finished strokes, with QGIS defaults and attribute form.

The tool only builds geometry; this module owns the QGIS side effects that the
original ``freehandEditing`` plugin had and the simplified rewrite dropped:
simplification, validity prompt, provider default values, the attribute form
(with click suppression while it is modal) and undo commands.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from qgis.core import QgsMessageLog, QgsSettings, QgsVectorLayerUtils
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox

from ..core.constants import LOG_TAG, PLUGIN_NAME
from ..core.settings import SettingsBackend, show_attribute_form
from .qt_compat import exec_dialog
from .texts import edit_command_text, edit_mode_required_text

IgnoreClicks = Optional[Callable[[bool], None]]


def _yes_no_buttons() -> tuple[Any, Any]:
    """Return the Yes/No buttons for both PyQt5 and PyQt6."""
    try:
        return QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No
    except AttributeError:  # pragma: no cover - PyQt5 only
        return getattr(QMessageBox, "Yes"), getattr(QMessageBox, "No")


class FeatureCreator:
    """Insert a digitized geometry into a vector layer.

    Args:
        iface: QGIS interface used for the attribute form and messages.
        settings: Settings backend; ``QgsSettings`` is used when omitted.
    """

    def __init__(self, iface: Any, settings: Optional[SettingsBackend] = None) -> None:
        self.iface = iface
        self._settings = settings

    # -- public API -------------------------------------------------------
    def create(
        self,
        layer: Any,
        geometry: Any,
        tolerance: float,
        ignore_clicks: IgnoreClicks = None,
    ) -> bool:
        """Add *geometry* to *layer* as a new feature.

        Args:
            layer: Target vector layer (line or polygon).
            geometry: Geometry in layer coordinates.
            tolerance: Simplification tolerance in layer units.
            ignore_clicks: Callback used to disable the map tool while the
                attribute form is modal.

        Returns:
            ``True`` when the feature was added to the edit buffer.
        """
        simplified = self._prepare_geometry(geometry, tolerance)
        if simplified is None:
            return False
        if not self._validate(simplified):
            return False
        if not self._ensure_editable(layer):
            return False
        return self._insert_feature(layer, simplified, ignore_clicks)

    # -- internals --------------------------------------------------------
    def _prepare_geometry(self, geometry: Any, tolerance: float) -> Any:
        """Simplify the stroke and reject empty results."""
        simplified = self._simplify(geometry, tolerance)
        if simplified is None or simplified.isEmpty():
            self._warn(
                QCoreApplication.translate(
                    "FreehandDigitize",
                    "La geometría resultante está vacía; no se añadió nada.",
                )
            )
            return None
        return simplified

    def _validate(self, geometry: Any) -> bool:
        """Return whether the geometry is valid or the user accepted it."""
        return bool(geometry.isGeosValid()) or self._confirm_invalid()

    def _insert_feature(
        self,
        layer: Any,
        geometry: Any,
        ignore_clicks: IgnoreClicks,
    ) -> bool:
        """Create the feature and commit it as a single undo command."""
        layer.beginEditCommand(edit_command_text())
        feature = self._create_feature(layer, geometry)
        if feature is None:
            layer.destroyEditCommand()
            return False

        if show_attribute_form(self._settings_backend()) and not self._edit_attributes(
            layer, feature, ignore_clicks
        ):
            self._abort(layer)
            return False

        if not self._add_feature(layer, feature):
            self._abort(layer)
            return False

        layer.endEditCommand()
        layer.triggerRepaint()
        self._refresh_canvas()
        return True

    def _create_feature(self, layer: Any, geometry: Any) -> Any:
        """Create a feature with the layer defaults applied."""
        try:
            return QgsVectorLayerUtils.createFeature(layer, geometry=geometry)
        except (RuntimeError, TypeError) as exc:
            self._warn(
                QCoreApplication.translate(
                    "FreehandDigitize", "No se pudo crear la entidad: {error}"
                ).format(error=exc)
            )
            return None

    def _add_feature(self, layer: Any, feature: Any) -> bool:
        """Add the feature, reporting provider failures."""
        try:
            added = bool(layer.addFeature(feature))
        except (RuntimeError, TypeError) as exc:
            self._log(f"addFeature failed: {exc}")
            added = False
        if not added:
            self._warn(
                QCoreApplication.translate(
                    "FreehandDigitize", "La capa «{name}» rechazó la entidad."
                ).format(name=layer.name())
            )
        return added

    def _abort(self, layer: Any) -> None:
        """Discard the pending undo command and repaint."""
        layer.destroyEditCommand()
        layer.triggerRepaint()

    def _settings_backend(self) -> SettingsBackend:
        """Return the settings backend, creating the QGIS one on demand."""
        if self._settings is None:
            self._settings = QgsSettings()
        return self._settings

    def _simplify(self, geometry: Any, tolerance: float) -> Any:
        """Simplify the geometry, falling back to the original on failure."""
        if tolerance <= 0:
            return geometry
        try:
            simplified = geometry.simplify(tolerance)
        except (RuntimeError, TypeError) as exc:
            self._log(f"simplify failed: {exc}")
            return geometry
        if simplified is None or simplified.isEmpty():
            return geometry
        return simplified

    def _confirm_invalid(self) -> bool:
        """Ask the user whether to keep an invalid geometry."""
        yes, no = _yes_no_buttons()
        try:
            reply = QMessageBox.question(
                self._parent(),
                QCoreApplication.translate("FreehandDigitize", "Entidad no válida"),
                QCoreApplication.translate(
                    "FreehandDigitize",
                    "La geometría de la entidad que acabas de dibujar no es válida.\n"
                    "¿Quieres usarla de todos modos?",
                ),
                yes | no,
                no,
            )
        except (RuntimeError, TypeError) as exc:
            self._log(f"validity dialog failed: {exc}")
            return False
        return reply == yes

    def _ensure_editable(self, layer: Any) -> bool:
        """Return whether the layer is already in edit mode."""
        if layer.isEditable():
            return True
        self._warn(edit_mode_required_text(layer.name()))
        return False

    def _edit_attributes(
        self,
        layer: Any,
        feature: Any,
        ignore_clicks: IgnoreClicks,
    ) -> bool:
        """Show the QGIS attribute form and return whether it was accepted."""
        try:
            dialog = self.iface.getFeatureForm(layer, feature)
        except (AttributeError, RuntimeError, TypeError) as exc:
            self._log(f"getFeatureForm failed: {exc}")
            return True
        if dialog is None:
            return True
        if ignore_clicks is not None:
            ignore_clicks(True)
        try:
            return exec_dialog(dialog)
        except (AttributeError, RuntimeError, TypeError) as exc:
            self._log(f"attribute dialog failed: {exc}")
            return True
        finally:
            if ignore_clicks is not None:
                ignore_clicks(False)

    def _parent(self) -> Any:
        """Return the main window when available."""
        try:
            return self.iface.mainWindow()
        except (AttributeError, RuntimeError):
            return None

    def _refresh_canvas(self) -> None:
        """Repaint the map canvas after a feature was added."""
        try:
            self.iface.mapCanvas().refresh()
        except (AttributeError, RuntimeError):
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

"""Apply a geometry difference to an existing feature."""

from __future__ import annotations

from typing import Any

from qgis.core import QgsGeometry, QgsMessageLog

from ..core.constants import LOG_TAG, PLUGIN_NAME
from .texts import (
    difference_applied_text,
    difference_edit_command_text,
    difference_empty_text,
    difference_invalid_text,
    difference_rejected_text,
    difference_same_feature_text,
    edit_mode_required_text,
)


class DifferenceCreator:
    """Subtract a cutter feature from a target feature.

    Args:
        iface: QGIS interface used for messages and canvas refresh.
    """

    def __init__(self, iface: Any) -> None:
        self.iface = iface

    def apply(self, layer: Any, target_id: int, cutter_id: int) -> bool:
        """Update *target_id* with ``target.difference(cutter)``.

        Args:
            layer: Active editable line/polygon layer.
            target_id: Feature that will be modified.
            cutter_id: Feature that is subtracted; it is not modified.

        Returns:
            ``True`` when the target geometry was updated.
        """
        if target_id == cutter_id:
            self._warn(difference_same_feature_text())
            return False
        if not layer.isEditable():
            self._warn(edit_mode_required_text(layer.name()))
            return False
        result = self._result(layer, target_id, cutter_id)
        if result is None:
            return False
        return self._write(layer, target_id, result)

    def _result(self, layer: Any, target_id: int, cutter_id: int) -> QgsGeometry | None:
        """Return the validated difference or ``None`` after a warning."""
        target = layer.getFeature(target_id)
        cutter = layer.getFeature(cutter_id)
        if not target.isValid() or not cutter.isValid():
            self._warn(difference_invalid_text())
            return None
        if target.geometry().isEmpty() or cutter.geometry().isEmpty():
            self._warn(difference_invalid_text())
            return None
        result = self._difference(target.geometry(), cutter.geometry())
        if result is None:
            return None
        if result.isEmpty():
            self._warn(difference_empty_text())
            return None
        if not result.isGeosValid():
            self._warn(difference_invalid_text())
            return None
        return result

    def _write(self, layer: Any, target_id: int, result: QgsGeometry) -> bool:
        """Apply the result in one edit command."""
        layer.beginEditCommand(difference_edit_command_text())
        try:
            changed = layer.changeGeometry(target_id, result)
        except (RuntimeError, TypeError) as exc:
            self._log(f"difference changeGeometry failed: {exc}")
            changed = False
        if not changed:
            layer.destroyEditCommand()
            self._warn(difference_rejected_text(layer.name()))
            return False
        layer.endEditCommand()
        layer.triggerRepaint()
        self._refresh_canvas()
        self._info(difference_applied_text())
        return True

    def _difference(self, target: QgsGeometry, cutter: QgsGeometry) -> QgsGeometry | None:
        """Return the difference or ``None`` on a geometry engine error."""
        try:
            return target.difference(cutter)
        except (RuntimeError, TypeError, ValueError) as exc:
            self._log(f"difference failed: {exc}")
            self._warn(difference_invalid_text())
            return None

    # -- messages ---------------------------------------------------------
    def _refresh_canvas(self) -> None:
        """Repaint the map canvas after the difference."""
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

    def _info(self, message: str) -> None:
        """Show an informational message in the QGIS message bar."""
        try:
            self.iface.messageBar().pushInfo(PLUGIN_NAME, message)
        except (AttributeError, RuntimeError):
            pass

    @staticmethod
    def _log(message: str) -> None:
        """Write a message to the QGIS log."""
        QgsMessageLog.logMessage(str(message), LOG_TAG)

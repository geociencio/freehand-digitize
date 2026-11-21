"""Reshape existing line/polygon features from a freehand stroke.

The target is every feature under the stroke (bounded by the stroke's
bounding box); when a selection exists, only selected features are considered.
All successful reshapes are applied in a single undo command.
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    Qgis,
    QgsFeatureRequest,
    QgsGeometry,
    QgsLineString,
    QgsMessageLog,
    QgsPoint,
)

from ..core.constants import LOG_TAG, PLUGIN_NAME
from .layer_utils import is_layer_alive
from .texts import (
    edit_mode_required_text,
    invalid_reshaped_geometry_text,
    layer_gone_text,
    no_feature_under_stroke_text,
    no_reshape_happened_text,
    reshape_edit_command_text,
    reshape_rejected_text,
    reshaped_count_text,
)


class ReshapeCreator:
    """Apply ``QgsGeometry.reshapeGeometry`` to the features under a stroke.

    Args:
        iface: QGIS interface used for the message bar and canvas refresh.
    """

    def __init__(self, iface: Any) -> None:
        self.iface = iface

    def reshape(self, layer: Any, stroke_geometry: QgsGeometry) -> bool:
        """Reshape the features intersected by *stroke_geometry*.

        Args:
            layer: Active line or polygon vector layer.
            stroke_geometry: Open line geometry in layer coordinates.

        Returns:
            ``True`` when at least one feature was reshaped.
        """
        if not is_layer_alive(layer):
            self._warn(layer_gone_text())
            return False
        if stroke_geometry is None or stroke_geometry.isEmpty():
            self._warn(no_feature_under_stroke_text())
            return False

        points = stroke_geometry.asPolyline()
        if len(points) < 2:
            self._warn(no_feature_under_stroke_text())
            return False
        line = QgsLineString([QgsPoint(point.x(), point.y()) for point in points])

        candidates = self._candidates(layer, stroke_geometry)
        if not candidates:
            self._warn(no_feature_under_stroke_text())
            return False

        if not self._ensure_editable(layer):
            return False

        reshaped = self._reshape_candidates(candidates, line)
        if not reshaped:
            self._warn(no_reshape_happened_text())
            return False
        if not self._apply(layer, reshaped):
            return False

        layer.triggerRepaint()
        self._refresh_canvas()
        if len(reshaped) > 1:
            self._info(reshaped_count_text(len(reshaped)))
        return True

    # -- target detection -------------------------------------------------
    def _candidates(self, layer: Any, stroke_geometry: QgsGeometry) -> list[Any]:
        """Return the features under the stroke, filtered by selection if any."""
        selected = layer.selectedFeatureIds()
        if selected:
            features = [layer.getFeature(feature_id) for feature_id in selected]
        else:
            request = QgsFeatureRequest().setFilterRect(stroke_geometry.boundingBox())
            features = list(layer.getFeatures(request))

        return [
            feature
            for feature in features
            if feature.isValid()
            and not feature.geometry().isEmpty()
            and feature.geometry().intersects(stroke_geometry)
        ]

    def _reshape_candidates(
        self,
        candidates: list[Any],
        line: QgsLineString,
    ) -> list[tuple[int, QgsGeometry]]:
        """Return ``(fid, geometry)`` pairs that reshaped successfully."""
        reshaped: list[tuple[int, QgsGeometry]] = []
        for feature in candidates:
            geometry = feature.geometry()
            if geometry is None or geometry.isEmpty():
                continue
            try:
                result = geometry.reshapeGeometry(line)
            except (RuntimeError, TypeError, ValueError) as exc:
                self._log(f"reshape failed for feature {feature.id()}: {exc}")
                continue
            if result != Qgis.GeometryOperationResult.Success:
                self._log(f"reshape skipped for feature {feature.id()}: {result}")
                continue
            if geometry.isEmpty() or not geometry.isGeosValid():
                self._warn(invalid_reshaped_geometry_text())
                continue
            reshaped.append((feature.id(), geometry))
        return reshaped

    # -- edit buffer ------------------------------------------------------
    def _apply(self, layer: Any, reshaped: list[tuple[int, QgsGeometry]]) -> bool:
        """Apply all reshapes in one edit command, rolling back on failure."""
        originals = {
            feature_id: layer.getFeature(feature_id).geometry() for feature_id, _ in reshaped
        }
        changed: list[int] = []
        layer.beginEditCommand(reshape_edit_command_text())
        try:
            for feature_id, geometry in reshaped:
                if not layer.changeGeometry(feature_id, geometry):
                    self._restore(layer, originals, changed)
                    layer.destroyEditCommand()
                    self._warn(reshape_rejected_text(layer.name()))
                    return False
                changed.append(feature_id)
        except (RuntimeError, TypeError) as exc:
            self._log(f"changeGeometry failed: {exc}")
            self._restore(layer, originals, changed)
            layer.destroyEditCommand()
            self._warn(reshape_rejected_text(layer.name()))
            return False

        layer.endEditCommand()
        return True

    def _restore(
        self,
        layer: Any,
        originals: dict[int, QgsGeometry],
        changed: list[int],
    ) -> None:
        """Best-effort restoration of features already changed."""
        for feature_id in changed:
            try:
                layer.changeGeometry(feature_id, originals[feature_id])
            except (KeyError, RuntimeError, TypeError) as exc:
                self._log(f"rollback failed for feature {feature_id}: {exc}")

    def _ensure_editable(self, layer: Any) -> bool:
        """Return whether the layer is already in edit mode."""
        if not is_layer_alive(layer):
            self._warn(layer_gone_text())
            return False
        if layer.isEditable():
            return True
        self._warn(edit_mode_required_text(layer.name()))
        return False

    # -- messages ---------------------------------------------------------
    def _refresh_canvas(self) -> None:
        """Repaint the map canvas after a reshape."""
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

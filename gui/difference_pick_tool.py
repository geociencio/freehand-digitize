"""Map tool that picks the target and cutter features with two clicks."""

from __future__ import annotations

from typing import Any

from qgis.core import QgsFeature
from qgis.gui import QgsMapToolIdentifyFeature
from qgis.PyQt.QtCore import pyqtSignal

from .qt_compat import KEY_ESCAPE


class DifferencePickTool(QgsMapToolIdentifyFeature):
    """Pick a target and a cutter on one layer.

    Signals:
        targetPicked: ``(fid)`` after the first click.
        featuresPicked: ``(target_fid, cutter_fid)`` after the second click.
        duplicateTarget: emitted when the user clicks the target again.
        pickCancelled: emitted on ``Esc``.
    """

    targetPicked = pyqtSignal(int)  # noqa: N815
    featuresPicked = pyqtSignal(int, int)  # noqa: N815
    duplicateTarget = pyqtSignal()  # noqa: N815
    pickCancelled = pyqtSignal()  # noqa: N815

    def __init__(self, canvas: Any, layer: Any) -> None:
        super().__init__(canvas, layer)
        self._target_id: int | None = None
        self._connect_identify_signal()

    def _connect_identify_signal(self) -> None:
        """Connect the feature overload when the binding exposes it."""
        try:
            signal = self.featureIdentified[QgsFeature]
        except (KeyError, TypeError):
            signal = self.featureIdentified
        signal.connect(self._on_feature_identified)

    def _on_feature_identified(self, feature: Any) -> None:
        """Handle the first and second clicks."""
        try:
            feature_id = feature.id() if isinstance(feature, QgsFeature) else int(feature)
        except (AttributeError, TypeError, ValueError):
            return
        if feature_id <= 0:
            return
        if self._target_id is None:
            self._target_id = feature_id
            self.targetPicked.emit(feature_id)
            return
        if feature_id == self._target_id:
            self.duplicateTarget.emit()
            return
        target = self._target_id
        self._target_id = None
        self.featuresPicked.emit(target, feature_id)

    def keyPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        """Cancel the pick on Esc."""
        if event.key() == KEY_ESCAPE:
            self.reset()
            self.pickCancelled.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def reset(self) -> None:
        """Forget the picked target."""
        self._target_id = None

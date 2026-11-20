"""Choose the target and cutter features for a difference operation."""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from .texts import (
    difference_apply_text,
    difference_cutter_label,
    difference_dialog_title,
    difference_help_text,
    difference_target_label,
    sampling_cancel_text,
)


class DifferenceDialog(QDialog):
    """Select the target and cutter from two feature ids.

    Args:
        layer: Vector layer that owns the features.
        feature_ids: Exactly two feature ids (selected or picked).
        parent: Optional dialog parent.
    """

    def __init__(
        self,
        layer: Any,
        feature_ids: list[int],
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._layer = layer
        self._ids = list(feature_ids)
        self.target_id: int | None = None
        self.cutter_id: int | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the two feature combos and the buttons."""
        self.setWindowTitle(difference_dialog_title())
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.target_combo = QComboBox(self)
        self.cutter_combo = QComboBox(self)
        for feature_id in self._ids:
            label = _feature_label(self._layer, feature_id)
            self.target_combo.addItem(label, feature_id)
            self.cutter_combo.addItem(label, feature_id)
        if self.target_combo.count() > 1:
            self.target_combo.setCurrentIndex(0)
            self.cutter_combo.setCurrentIndex(1)
        self.target_combo.currentIndexChanged.connect(self._update_apply_state)
        self.cutter_combo.currentIndexChanged.connect(self._update_apply_state)
        form.addRow(difference_target_label(), self.target_combo)
        form.addRow(difference_cutter_label(), self.cutter_combo)
        layout.addLayout(form)

        help_label = QLabel(difference_help_text(), self)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        buttons = QDialogButtonBox(self)
        ok_button = _button(QDialogButtonBox, "Ok")
        buttons.addButton(ok_button)
        buttons.addButton(_button(QDialogButtonBox, "Cancel"))
        buttons.button(ok_button).setText(difference_apply_text())
        buttons.button(_button(QDialogButtonBox, "Cancel")).setText(sampling_cancel_text())
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self._on_reject)
        self._apply_button = buttons.button(ok_button)
        layout.addWidget(buttons)
        self._update_apply_state()

    def _update_apply_state(self, *_args) -> None:
        """Disable Apply when target and cutter are the same feature."""
        target = self.target_combo.currentData()
        cutter = self.cutter_combo.currentData()
        self._apply_button.setEnabled(
            target is not None and cutter is not None and target != cutter
        )

    def _on_reject(self) -> None:
        """Close without recording ids."""
        self.reject()

    def accept(self) -> None:
        """Validate the pair and close the dialog."""
        target = self.target_combo.currentData()
        cutter = self.cutter_combo.currentData()
        if target is None or cutter is None or target == cutter:
            return
        self.target_id = int(target)
        self.cutter_id = int(cutter)
        super().accept()


def _feature_label(layer: Any, feature_id: int) -> str:
    """Return a compact label for a feature."""
    label = f"fid {feature_id}"
    try:
        feature = layer.getFeature(feature_id)
        for field in layer.fields():
            value = feature[field.name()]
            if value is not None and str(value) != "":
                return f"{label} — {field.name()}={str(value)[:30]}"
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
        pass
    return label


def _button(box: Any, name: str) -> Any:
    """Return a ``QDialogButtonBox`` standard button for Qt5/Qt6."""
    standard = getattr(box, "StandardButton", None)
    if standard is not None:
        button = getattr(standard, name, None)
        if button is not None:
            return button
    return getattr(box, name)

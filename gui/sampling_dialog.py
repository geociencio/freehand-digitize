"""Sampling settings dialog (pixels vs layer units)."""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from ..core.constants import (
    DEFAULT_SAMPLE_PX,
    SAMPLE_LAYER_DECIMALS,
    SAMPLE_LAYER_MAX,
    SAMPLE_LAYER_MIN,
    SAMPLE_LAYER_STEP,
    SAMPLE_PX_DECIMALS,
    SAMPLE_PX_MAX,
    SAMPLE_PX_MIN,
    SAMPLE_PX_STEP,
    SAMPLE_UNIT_LAYER,
    SAMPLE_UNIT_PX,
)
from ..core.settings import SamplingStore
from ..core.stroke import SamplingOptions
from .texts import (
    sampling_cancel_text,
    sampling_dialog_title,
    sampling_distance_label,
    sampling_distance_tooltip,
    sampling_geographic_warning_text,
    sampling_help_text,
    sampling_layer_units_text,
    sampling_ok_text,
    sampling_pixels_text,
    sampling_reset_text,
    sampling_unit_label,
)


class SamplingDialog(QDialog):
    """Choose pixels or layer units and the minimum vertex distance.

    Args:
        layer: Active vector layer, used only to show the geographic warning.
        store: Persistence for the sampling options.
        parent: Optional dialog parent.
    """

    def __init__(
        self,
        layer: Any,
        store: SamplingStore,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._layer = layer
        self._store = store
        self._options = store.load()
        self._unit = self._options.unit
        self._px_value = self._options.distance_px
        self._layer_value = self._options.distance_layer
        self._geographic = _is_geographic(layer)
        self._build_ui()

    # -- UI ---------------------------------------------------------------
    def _build_ui(self) -> None:
        """Build the dialog widgets."""
        self.setWindowTitle(sampling_dialog_title())
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.unit_combo = QComboBox(self)
        self.unit_combo.addItem(sampling_pixels_text(), SAMPLE_UNIT_PX)
        self.unit_combo.addItem(sampling_layer_units_text(), SAMPLE_UNIT_LAYER)
        index = self.unit_combo.findData(self._unit)
        self.unit_combo.setCurrentIndex(max(0, index))
        self.unit_combo.currentIndexChanged.connect(self._on_unit_changed)
        form.addRow(sampling_unit_label(), self.unit_combo)

        self.distance_spin = QDoubleSpinBox(self)
        self.distance_spin.setToolTip(sampling_distance_tooltip())
        form.addRow(sampling_distance_label(), self.distance_spin)
        layout.addLayout(form)

        self.help_label = QLabel(sampling_help_text(), self)
        self.help_label.setWordWrap(True)
        layout.addWidget(self.help_label)

        self.warning_label = QLabel(sampling_geographic_warning_text(), self)
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #8a6d3b;")
        layout.addWidget(self.warning_label)

        buttons = QDialogButtonBox(self)
        buttons.addButton(_button(QDialogButtonBox, "Ok"))
        buttons.addButton(_button(QDialogButtonBox, "Cancel"))
        buttons.addButton(_button(QDialogButtonBox, "Reset"))
        buttons.button(_button(QDialogButtonBox, "Ok")).setText(sampling_ok_text())
        buttons.button(_button(QDialogButtonBox, "Cancel")).setText(sampling_cancel_text())
        buttons.button(_button(QDialogButtonBox, "Reset")).setText(sampling_reset_text())
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self._on_reject)
        buttons.button(_button(QDialogButtonBox, "Reset")).clicked.connect(self._on_reset)
        layout.addWidget(buttons)

        self._apply_unit(self._unit, set_value=True)

    def _on_unit_changed(self, _index: int) -> None:
        """Keep the edited value per unit and switch the spinbox."""
        self._remember_current_value()
        unit = self.unit_combo.currentData()
        if unit not in (SAMPLE_UNIT_PX, SAMPLE_UNIT_LAYER):
            unit = SAMPLE_UNIT_PX
        self._unit = unit
        self._apply_unit(unit, set_value=True)

    def _remember_current_value(self) -> None:
        """Store the spinbox value in the slot of the current unit."""
        value = self.distance_spin.value()
        if self._unit == SAMPLE_UNIT_LAYER:
            self._layer_value = value
        else:
            self._px_value = value

    def _apply_unit(self, unit: str, set_value: bool) -> None:
        """Update range, decimals, suffix and visibility for *unit*."""
        self.distance_spin.blockSignals(True)
        if unit == SAMPLE_UNIT_LAYER:
            self.distance_spin.setRange(SAMPLE_LAYER_MIN, SAMPLE_LAYER_MAX)
            self.distance_spin.setDecimals(SAMPLE_LAYER_DECIMALS)
            self.distance_spin.setSingleStep(SAMPLE_LAYER_STEP)
            self.distance_spin.setSuffix("")
            value = self._layer_value
        else:
            self.distance_spin.setRange(SAMPLE_PX_MIN, SAMPLE_PX_MAX)
            self.distance_spin.setDecimals(SAMPLE_PX_DECIMALS)
            self.distance_spin.setSingleStep(SAMPLE_PX_STEP)
            self.distance_spin.setSuffix(" px")
            value = self._px_value
        if set_value:
            self.distance_spin.setValue(value)
        self.distance_spin.blockSignals(False)
        self._show_warning()

    def _show_warning(self) -> None:
        """Show the geographic warning only for layer units."""
        self.warning_label.setVisible(self._geographic and self._unit == SAMPLE_UNIT_LAYER)

    def _on_reset(self) -> None:
        """Restore the default for the selected unit."""
        if self._unit == SAMPLE_UNIT_LAYER:
            self._layer_value = self._store.layer_default(self._geographic)
            self.distance_spin.setValue(self._layer_value)
        else:
            self._px_value = DEFAULT_SAMPLE_PX
            self.distance_spin.setValue(self._px_value)

    # -- result -----------------------------------------------------------
    def _on_reject(self) -> None:
        """Close the dialog without saving."""
        self.reject()

    def accept(self) -> None:
        """Persist the selected options and close the dialog."""
        self._remember_current_value()
        self._store.save_options(
            SamplingOptions(
                unit=self._unit,
                distance_px=self._px_value,
                distance_layer=self._layer_value,
            )
        )
        super().accept()


def _button(box: Any, name: str) -> Any:
    """Return a ``QDialogButtonBox`` standard button for Qt5/Qt6."""
    standard = getattr(box, "StandardButton", None)
    if standard is not None:
        button = getattr(standard, name, None)
        if button is not None:
            return button
    return getattr(box, name)


def _is_geographic(layer: Any) -> bool:
    """Return whether *layer* uses a geographic CRS."""
    if layer is None:
        return False
    try:
        return bool(layer.crs().isGeographic())
    except (AttributeError, RuntimeError, TypeError):
        return False

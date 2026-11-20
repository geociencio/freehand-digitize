"""Integration tests for the sampling settings dialog."""

from __future__ import annotations

import unittest

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis


@requires_qgis
class TestSamplingDialog(unittest.TestCase):
    """Units, per-unit values, geographic warning and persistence."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from freehand_digitize.core.constants import (
            DEFAULT_SAMPLE_LAYER,
            DEFAULT_SAMPLE_PX,
            GEOGRAPHIC_SAMPLE_LAYER,
            SAMPLE_UNIT_LAYER,
            SAMPLE_UNIT_PX,
        )
        from freehand_digitize.core.settings import SamplingStore
        from freehand_digitize.gui.sampling_dialog import SamplingDialog
        from tests.integration.fakes import FakeIface, make_layer
        from tests.mocks.settings import FakeSettings

        cls.DEFAULT_SAMPLE_LAYER = DEFAULT_SAMPLE_LAYER
        cls.DEFAULT_SAMPLE_PX = DEFAULT_SAMPLE_PX
        cls.GEOGRAPHIC_SAMPLE_LAYER = GEOGRAPHIC_SAMPLE_LAYER
        cls.SAMPLE_UNIT_LAYER = SAMPLE_UNIT_LAYER
        cls.SAMPLE_UNIT_PX = SAMPLE_UNIT_PX
        cls.SamplingDialog = SamplingDialog
        cls.SamplingStore = SamplingStore
        cls.FakeIface = FakeIface
        cls.FakeSettings = FakeSettings
        cls.make_layer = staticmethod(make_layer)

    def setUp(self) -> None:
        """Create a fake interface and a fresh store."""
        self.iface = self.FakeIface()
        self.settings = self.FakeSettings()
        self.store = self.SamplingStore(self.settings)
        self.addCleanup(self.iface.close)

    def _dialog(self, crs: str = "EPSG:4326"):
        """Build a dialog for a layer with *crs*."""
        layer = self.make_layer("LineString", crs=crs)
        dialog = self.SamplingDialog(layer, self.store, self.iface.mainWindow())
        self.addCleanup(dialog.deleteLater)
        return dialog

    def test_defaults_are_pixels(self) -> None:
        """A fresh store shows pixels and 1.5."""
        dialog = self._dialog()
        self.assertEqual(dialog.unit_combo.currentData(), self.SAMPLE_UNIT_PX)
        self.assertEqual(dialog.distance_spin.value(), self.DEFAULT_SAMPLE_PX)
        self.assertTrue(dialog.warning_label.isHidden())

    def test_geographic_warning_for_layer_units(self) -> None:
        """Geographic layers show the degrees warning in layer mode."""
        dialog = self._dialog()
        layer_index = dialog.unit_combo.findData(self.SAMPLE_UNIT_LAYER)
        dialog.unit_combo.setCurrentIndex(layer_index)
        self.assertFalse(dialog.warning_label.isHidden())
        self.assertEqual(dialog.distance_spin.decimals(), 6)

    def test_projected_layer_has_no_warning(self) -> None:
        """Projected layers do not show the geographic warning."""
        dialog = self._dialog("EPSG:3857")
        layer_index = dialog.unit_combo.findData(self.SAMPLE_UNIT_LAYER)
        dialog.unit_combo.setCurrentIndex(layer_index)
        self.assertTrue(dialog.warning_label.isHidden())

    def test_accept_persists_layer_distance(self) -> None:
        """Accepting saves the selected unit and distance."""
        dialog = self._dialog()
        dialog.unit_combo.setCurrentIndex(dialog.unit_combo.findData(self.SAMPLE_UNIT_LAYER))
        dialog.distance_spin.setValue(2.5)
        dialog.accept()
        options = self.store.load()
        self.assertEqual(options.unit, self.SAMPLE_UNIT_LAYER)
        self.assertEqual(options.distance_layer, 2.5)
        self.assertEqual(options.distance_px, self.DEFAULT_SAMPLE_PX)

    def test_cancel_does_not_save(self) -> None:
        """Rejecting leaves the store unchanged."""
        dialog = self._dialog()
        dialog.distance_spin.setValue(9.0)
        dialog.reject()
        self.assertEqual(self.store.load().distance_px, self.DEFAULT_SAMPLE_PX)

    def test_reset_uses_crs_aware_default(self) -> None:
        """Reset restores the layer default for the CRS."""
        dialog = self._dialog()
        dialog.unit_combo.setCurrentIndex(dialog.unit_combo.findData(self.SAMPLE_UNIT_LAYER))
        dialog.distance_spin.setValue(100.0)
        dialog._on_reset()
        self.assertAlmostEqual(dialog.distance_spin.value(), self.GEOGRAPHIC_SAMPLE_LAYER)

    def test_values_are_kept_per_unit(self) -> None:
        """Switching units keeps the edited value of each unit."""
        dialog = self._dialog()
        dialog.distance_spin.setValue(3.0)
        dialog.unit_combo.setCurrentIndex(dialog.unit_combo.findData(self.SAMPLE_UNIT_LAYER))
        dialog.distance_spin.setValue(2.5)
        dialog.unit_combo.setCurrentIndex(dialog.unit_combo.findData(self.SAMPLE_UNIT_PX))
        self.assertEqual(dialog.distance_spin.value(), 3.0)
        dialog.accept()
        options = self.store.load()
        self.assertEqual(options.distance_px, 3.0)
        self.assertEqual(options.distance_layer, 2.5)


if __name__ == "__main__":
    unittest.main()

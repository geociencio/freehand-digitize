"""Unit tests for the settings persistence layer."""

from __future__ import annotations

import unittest

from freehand_digitize.core.constants import (
    DEFAULT_SAMPLE_LAYER,
    DEFAULT_SAMPLE_PX,
    DISABLE_FORM_KEY,
    GEOGRAPHIC_SAMPLE_LAYER,
    LEGACY_TOLERANCE_KEY,
    SAMPLE_LAYER_MAX,
    SAMPLE_PX_MAX,
    SAMPLE_UNIT_LAYER,
    SAMPLE_UNIT_PX,
    SAMPLING_LAYER_KEY,
    SAMPLING_PX_KEY,
    SAMPLING_UNIT_KEY,
    TOLERANCE_KEY,
    TOLERANCE_MAX,
)
from freehand_digitize.core.settings import (
    SamplingStore,
    ToleranceStore,
    show_attribute_form,
)
from freehand_digitize.core.stroke import SamplingOptions
from tests.mocks.settings import FakeSettings


class TestToleranceStore(unittest.TestCase):
    """Reading, migrating and writing the tolerance."""

    def test_default_when_missing(self) -> None:
        """No stored value returns zero."""
        store = ToleranceStore(FakeSettings())
        self.assertEqual(store.load(), 0.0)

    def test_reads_current_key(self) -> None:
        """The current key takes precedence."""
        store = ToleranceStore(FakeSettings({TOLERANCE_KEY: 2.5}))
        self.assertEqual(store.load(), 2.5)

    def test_reads_and_migrates_legacy_key(self) -> None:
        """The upstream key is reused and copied to the new key."""
        backend = FakeSettings({LEGACY_TOLERANCE_KEY: 1.75})
        store = ToleranceStore(backend)
        self.assertEqual(store.load(), 1.75)
        self.assertEqual(backend.values[TOLERANCE_KEY], 1.75)

    def test_current_key_wins_over_legacy(self) -> None:
        """The current key is not overwritten by the legacy one."""
        backend = FakeSettings({TOLERANCE_KEY: 1.0, LEGACY_TOLERANCE_KEY: 4.0})
        store = ToleranceStore(backend)
        self.assertEqual(store.load(), 1.0)

    def test_clamps_stored_value(self) -> None:
        """Out-of-range stored values are clamped."""
        store = ToleranceStore(FakeSettings({TOLERANCE_KEY: TOLERANCE_MAX + 3}))
        self.assertEqual(store.load(), TOLERANCE_MAX)

    def test_save_clamps_and_writes(self) -> None:
        """Saving clamps the value and returns what was written."""
        backend = FakeSettings()
        store = ToleranceStore(backend)
        self.assertEqual(store.save(9.5), TOLERANCE_MAX)
        self.assertEqual(backend.values[TOLERANCE_KEY], TOLERANCE_MAX)

    def test_invalid_backend_values_are_ignored(self) -> None:
        """A backend returning a non-numeric value falls back to zero."""
        store = ToleranceStore(FakeSettings({TOLERANCE_KEY: "bad"}))
        self.assertEqual(store.load(), 0.0)


class TestSamplingStore(unittest.TestCase):
    """Sampling unit and per-unit distances."""

    def test_defaults(self) -> None:
        """Missing keys return pixels and the default distances."""
        store = SamplingStore(FakeSettings())
        options = store.load()
        self.assertEqual(options.unit, SAMPLE_UNIT_PX)
        self.assertEqual(options.distance_px, DEFAULT_SAMPLE_PX)
        self.assertEqual(options.distance_layer, DEFAULT_SAMPLE_LAYER)

    def test_roundtrip_per_unit(self) -> None:
        """Saving one unit preserves the other distance."""
        backend = FakeSettings()
        store = SamplingStore(backend)
        store.save(SAMPLE_UNIT_LAYER, 2.5)
        self.assertEqual(backend.values[SAMPLING_LAYER_KEY], 2.5)
        self.assertEqual(backend.values[SAMPLING_PX_KEY], DEFAULT_SAMPLE_PX)
        store.save(SAMPLE_UNIT_PX, 3.0)
        options = store.load()
        self.assertEqual(options.unit, SAMPLE_UNIT_PX)
        self.assertEqual(options.distance_px, 3.0)
        self.assertEqual(options.distance_layer, 2.5)

    def test_invalid_unit_falls_back_to_pixels(self) -> None:
        """Unknown units are rejected."""
        store = SamplingStore(FakeSettings({SAMPLING_UNIT_KEY: "bad"}))
        self.assertEqual(store.load().unit, SAMPLE_UNIT_PX)

    def test_clamps_distances(self) -> None:
        """Out-of-range values are clamped."""
        store = SamplingStore(FakeSettings())
        options = store.save_options(
            SamplingOptions(
                unit=SAMPLE_UNIT_PX,
                distance_px=SAMPLE_PX_MAX + 10,
                distance_layer=SAMPLE_LAYER_MAX + 10,
            )
        )
        self.assertEqual(options.distance_px, SAMPLE_PX_MAX)
        self.assertEqual(options.distance_layer, SAMPLE_LAYER_MAX)

    def test_layer_default_depends_on_crs(self) -> None:
        """Geographic layers use a smaller degree default."""
        self.assertEqual(SamplingStore.layer_default(True), GEOGRAPHIC_SAMPLE_LAYER)
        self.assertEqual(SamplingStore.layer_default(False), DEFAULT_SAMPLE_LAYER)


class TestAttributeFormSetting(unittest.TestCase):
    """The QGIS attribute-form preference."""

    def test_default_shows_form(self) -> None:
        """The form is shown by default."""
        self.assertTrue(show_attribute_form(FakeSettings()))

    def test_disabled_setting_hides_form(self) -> None:
        """The QGIS 'disable attribute values dialog' option is honoured."""
        self.assertFalse(show_attribute_form(FakeSettings({DISABLE_FORM_KEY: True})))

    def test_enabled_setting_shows_form(self) -> None:
        """An explicit false value keeps the form enabled."""
        self.assertTrue(show_attribute_form(FakeSettings({DISABLE_FORM_KEY: False})))


if __name__ == "__main__":
    unittest.main()

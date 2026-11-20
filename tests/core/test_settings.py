"""Unit tests for the settings persistence layer."""

from __future__ import annotations

import unittest

from freehand_digitize.core.constants import (
    DISABLE_FORM_KEY,
    LEGACY_TOLERANCE_KEY,
    TOLERANCE_KEY,
    TOLERANCE_MAX,
)
from freehand_digitize.core.settings import ToleranceStore, show_attribute_form
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

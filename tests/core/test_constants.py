"""Unit tests for the plugin constants."""

from __future__ import annotations

import unittest

from freehand_digitize.core import constants


class TestConstants(unittest.TestCase):
    """The documented limits and settings keys."""

    def test_tolerance_range(self) -> None:
        """The spinbox range matches the upstream plugin."""
        self.assertEqual(constants.TOLERANCE_MIN, 0.0)
        self.assertEqual(constants.TOLERANCE_MAX, 5.0)
        self.assertEqual(constants.TOLERANCE_DECIMALS, 3)
        self.assertEqual(constants.TOLERANCE_STEP, 0.1)

    def test_settings_keys(self) -> None:
        """The plugin key and the upstream migration key are stable."""
        self.assertEqual(constants.TOLERANCE_KEY, "freehand_digitize/tolerance")
        self.assertEqual(constants.LEGACY_TOLERANCE_KEY, "freehandEdit/tolerance")
        self.assertEqual(
            constants.DISABLE_FORM_KEY,
            "qgis/digitizing/disable_enter_attribute_values_dialog",
        )

    def test_minimum_points(self) -> None:
        """Lines need two points and polygons three."""
        self.assertEqual(constants.MIN_LINE_POINTS, 2)
        self.assertEqual(constants.MIN_POLYGON_POINTS, 3)

    def test_stroke_safety_limits(self) -> None:
        """The sampling and safety caps are positive."""
        self.assertGreater(constants.MIN_SAMPLE_PIXELS, 0)
        self.assertGreater(constants.MAX_STROKE_POINTS, 0)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for the stroke recorder."""

from __future__ import annotations

import unittest

from freehand_digitize.core.constants import SAMPLE_UNIT_LAYER, SAMPLE_UNIT_PX
from freehand_digitize.core.stroke import SamplingOptions, StrokeRecorder


class TestStrokeRecorder(unittest.TestCase):
    """Sampling, reset and safety cap."""

    def test_start_records_first_point(self) -> None:
        """The first vertex is always recorded."""
        recorder = StrokeRecorder()
        recorder.start((10.0, 20.0), (100.0, 200.0))
        self.assertEqual(recorder.points, [(10.0, 20.0)])
        self.assertEqual(len(recorder), 1)
        self.assertFalse(recorder.is_empty)

    def test_start_resets_previous_stroke(self) -> None:
        """Starting a new stroke discards the previous points."""
        recorder = StrokeRecorder()
        recorder.start((0, 0), (0, 0))
        recorder.add((1, 1), (10, 10))
        recorder.start((5, 5), (50, 50))
        self.assertEqual(recorder.points, [(5.0, 5.0)])

    def test_near_points_are_thinned(self) -> None:
        """Vertices closer than the pixel threshold are ignored."""
        recorder = StrokeRecorder(SamplingOptions(distance_px=2.0))
        recorder.start((0, 0), (0, 0))
        self.assertFalse(recorder.add((1, 1), (1, 1)))
        self.assertEqual(len(recorder), 1)

    def test_far_points_are_recorded(self) -> None:
        """Vertices beyond the threshold are appended."""
        recorder = StrokeRecorder(SamplingOptions(distance_px=2.0))
        recorder.start((0, 0), (0, 0))
        self.assertTrue(recorder.add((3, 3), (3, 0)))
        self.assertEqual(recorder.points, [(0.0, 0.0), (3.0, 3.0)])

    def test_threshold_uses_device_distance(self) -> None:
        """Layer distance does not matter; device distance does."""
        recorder = StrokeRecorder(SamplingOptions(distance_px=2.0))
        recorder.start((0, 0), (0, 0))
        self.assertTrue(recorder.add((1000, 1000), (3, 0)))
        self.assertEqual(recorder.points[-1], (1000.0, 1000.0))
        self.assertFalse(recorder.add((2000, 2000), (4, 0)))

    def test_layer_threshold_uses_layer_distance(self) -> None:
        """Layer mode compares layer coordinates, not device pixels."""
        recorder = StrokeRecorder(SamplingOptions(unit=SAMPLE_UNIT_LAYER, distance_layer=2.0))
        recorder.start((0, 0), (0, 0))
        self.assertFalse(recorder.add((1, 1), (100, 100)))
        self.assertTrue(recorder.add((3, 3), (1, 1)))
        self.assertEqual(recorder.points[-1], (3.0, 3.0))

    def test_layer_mode_ignores_large_device_delta(self) -> None:
        """A large screen delta with a small layer delta is thinned."""
        recorder = StrokeRecorder(SamplingOptions(unit=SAMPLE_UNIT_LAYER, distance_layer=2.0))
        recorder.start((0, 0), (0, 0))
        self.assertFalse(recorder.add((1, 0), (500, 500)))

    def test_pixel_mode_ignores_large_layer_delta(self) -> None:
        """Pixel mode keeps the existing device-distance behavior."""
        recorder = StrokeRecorder(SamplingOptions(unit=SAMPLE_UNIT_PX, distance_px=2.0))
        recorder.start((0, 0), (0, 0))
        self.assertTrue(recorder.add((1000, 1000), (3, 0)))

    def test_max_points_cap(self) -> None:
        """Recording stops at the configured cap."""
        recorder = StrokeRecorder(SamplingOptions(distance_px=0.0), max_points=2)
        recorder.start((0, 0), (0, 0))
        self.assertTrue(recorder.add((1, 1), (1, 1)))
        self.assertFalse(recorder.add((2, 2), (2, 2)))
        self.assertEqual(len(recorder), 2)

    def test_final_point_bypasses_threshold(self) -> None:
        """The release point is kept even when it is within the threshold."""
        recorder = StrokeRecorder(SamplingOptions(distance_px=2.0))
        recorder.start((0, 0), (0, 0))
        self.assertFalse(recorder.add((1, 1), (1, 1)))
        self.assertTrue(recorder.add_final((1, 1), (1, 1)))
        self.assertEqual(recorder.points, [(0.0, 0.0), (1.0, 1.0)])

    def test_final_point_rejects_exact_duplicate(self) -> None:
        """A final point identical to the last layer point is not duplicated."""
        recorder = StrokeRecorder()
        recorder.start((0, 0), (0, 0))
        self.assertFalse(recorder.add_final((0, 0), (0, 0)))
        self.assertEqual(len(recorder), 1)

    def test_final_point_respects_cap(self) -> None:
        """The final point cannot exceed the configured cap."""
        recorder = StrokeRecorder(SamplingOptions(distance_px=0.0), max_points=2)
        recorder.start((0, 0), (0, 0))
        recorder.add((1, 1), (1, 1))
        self.assertFalse(recorder.add_final((2, 2), (2, 2)))
        self.assertEqual(len(recorder), 2)

    def test_points_property_returns_copy(self) -> None:
        """Mutating the returned list does not change the recorder."""
        recorder = StrokeRecorder()
        recorder.start((0, 0), (0, 0))
        points = recorder.points
        points.append((9, 9))
        self.assertEqual(len(recorder), 1)

    def test_reset(self) -> None:
        """Reset clears points and device state."""
        recorder = StrokeRecorder()
        recorder.start((0, 0), (0, 0))
        recorder.reset()
        self.assertTrue(recorder.is_empty)
        self.assertEqual(recorder.points, [])


if __name__ == "__main__":
    unittest.main()

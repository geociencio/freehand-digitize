"""Tests for the session lesson extractor."""

from __future__ import annotations

import lesson_extractor


def test_detect_signals_finds_error_and_i18n_patterns() -> None:
    diff = (
        "diff --git a/src/demo.py b/src/demo.py\n"
        "+Traceback (most recent call last):\n"
        "+ValueError: boom\n"
        "+self.tr('Hello')\n"
        "+# no-i18n\n"
    )
    signals = lesson_extractor.detect_signals(diff)
    categories = {signal["category"] for signal in signals}
    assert "error_resolution" in categories
    assert "code_patterns" in categories


def test_detect_metric_drift_signal() -> None:
    diff = "+Stale test count metric updated from 190 to 217\n"
    signals = lesson_extractor.detect_signals(diff)
    categories = {signal["category"] for signal in signals}
    assert "metric_changes" in categories

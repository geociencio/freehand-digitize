"""Persistence helpers for the plugin settings.

The backend is injected (``QgsSettings`` at runtime, a tiny fake in tests) and
only needs ``contains``, ``value`` and ``setValue``. Keeping the dependency out
of the module makes the storage logic unit-testable without Qt.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .constants import (
    DEFAULT_SAMPLE_LAYER,
    DEFAULT_SAMPLE_PX,
    DEFAULT_SAMPLING_UNIT,
    DEFAULT_TOLERANCE,
    DISABLE_FORM_KEY,
    GEOGRAPHIC_SAMPLE_LAYER,
    LEGACY_TOLERANCE_KEY,
    SAMPLE_LAYER_MAX,
    SAMPLE_LAYER_MIN,
    SAMPLE_PX_MAX,
    SAMPLE_PX_MIN,
    SAMPLE_UNIT_LAYER,
    SAMPLE_UNIT_PX,
    SAMPLING_LAYER_KEY,
    SAMPLING_PX_KEY,
    SAMPLING_UNIT_KEY,
    TOLERANCE_KEY,
)
from .geometry_rules import clamp_tolerance
from .stroke import SamplingOptions


@runtime_checkable
class SettingsBackend(Protocol):
    """Minimal settings interface shared by ``QgsSettings`` and test fakes."""

    def contains(self, key: str) -> bool:
        """Return whether *key* exists."""
        ...

    def value(self, key: str, default: Any = None, type: Any = None) -> Any:
        """Return the value stored at *key*."""
        ...

    def setValue(self, key: str, value: Any) -> None:
        """Store *value* at *key*."""
        ...


class ToleranceStore:
    """Read and write the simplification tolerance.

    Args:
        backend: Settings backend (``QgsSettings`` in production).
    """

    def __init__(self, backend: SettingsBackend) -> None:
        self._backend = backend

    def load(self) -> float:
        """Return the stored tolerance, migrating the legacy key if needed.

        The original ``freehandEditing`` plugin stored the value under
        ``/freehandEdit/tolerance``. When this plugin has no value of its own,
        the legacy value is reused and copied to the new key.

        Returns:
            A clamped tolerance value.
        """
        for index, key in enumerate((TOLERANCE_KEY, LEGACY_TOLERANCE_KEY)):
            try:
                if not self._backend.contains(key):
                    continue
                raw = self._backend.value(key, DEFAULT_TOLERANCE, type=float)
            except (AttributeError, TypeError, ValueError, RuntimeError):
                continue
            tolerance = clamp_tolerance(raw)
            if index == 1:
                self.save(tolerance)
            return tolerance
        return DEFAULT_TOLERANCE

    def save(self, value: Any) -> float:
        """Clamp and persist *value*.

        Args:
            value: Raw tolerance from the spinbox.

        Returns:
            The clamped value that was stored.
        """
        tolerance = clamp_tolerance(value)
        try:
            self._backend.setValue(TOLERANCE_KEY, tolerance)
        except (AttributeError, TypeError, RuntimeError):
            pass
        return tolerance


def show_attribute_form(backend: SettingsBackend) -> bool:
    """Return whether QGIS is configured to show the feature form.

    Args:
        backend: Settings backend (``QgsSettings`` in production).

    Returns:
        ``False`` when the user disabled ``Enter attribute values`` in the
        QGIS digitizing options, ``True`` otherwise.
    """
    try:
        if backend.contains(DISABLE_FORM_KEY):
            disabled = backend.value(DISABLE_FORM_KEY, False, type=bool)
            return not bool(disabled)
    except (AttributeError, TypeError, ValueError, RuntimeError):
        pass
    return True


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp *value* to the inclusive range."""
    return max(minimum, min(maximum, value))


class SamplingStore:
    """Read and write the vertex-sampling options.

    Args:
        backend: Settings backend (``QgsSettings`` in production).
    """

    def __init__(self, backend: SettingsBackend) -> None:
        self._backend = backend

    def load(self) -> SamplingOptions:
        """Return the persisted sampling options with safe defaults."""
        unit = self._unit()
        distance_px = _clamp(
            self._read_float(SAMPLING_PX_KEY, DEFAULT_SAMPLE_PX),
            SAMPLE_PX_MIN,
            SAMPLE_PX_MAX,
        )
        distance_layer = _clamp(
            self._read_float(SAMPLING_LAYER_KEY, DEFAULT_SAMPLE_LAYER),
            SAMPLE_LAYER_MIN,
            SAMPLE_LAYER_MAX,
        )
        return SamplingOptions(
            unit=unit,
            distance_px=distance_px,
            distance_layer=distance_layer,
        )

    def save(self, unit: str, distance: Any) -> SamplingOptions:
        """Persist the selected unit and its distance, keeping the other one.

        Args:
            unit: ``px`` or ``layer``.
            distance: Minimum distance for the selected unit.

        Returns:
            The normalized options that were stored.
        """
        current = self.load()
        if unit == SAMPLE_UNIT_LAYER:
            options = SamplingOptions(
                unit=SAMPLE_UNIT_LAYER,
                distance_px=current.distance_px,
                distance_layer=_clamp(float(distance), SAMPLE_LAYER_MIN, SAMPLE_LAYER_MAX),
            )
        else:
            options = SamplingOptions(
                unit=SAMPLE_UNIT_PX,
                distance_px=_clamp(float(distance), SAMPLE_PX_MIN, SAMPLE_PX_MAX),
                distance_layer=current.distance_layer,
            )
        return self.save_options(options)

    def save_options(self, options: SamplingOptions) -> SamplingOptions:
        """Persist both distances and the selected unit.

        Args:
            options: Options to normalize and store.

        Returns:
            The normalized options that were stored.
        """
        unit = (
            options.unit if options.unit in (SAMPLE_UNIT_PX, SAMPLE_UNIT_LAYER) else SAMPLE_UNIT_PX
        )
        normalized = SamplingOptions(
            unit=unit,
            distance_px=_clamp(float(options.distance_px), SAMPLE_PX_MIN, SAMPLE_PX_MAX),
            distance_layer=_clamp(
                float(options.distance_layer),
                SAMPLE_LAYER_MIN,
                SAMPLE_LAYER_MAX,
            ),
        )
        for key, value in (
            (SAMPLING_UNIT_KEY, normalized.unit),
            (SAMPLING_PX_KEY, normalized.distance_px),
            (SAMPLING_LAYER_KEY, normalized.distance_layer),
        ):
            try:
                self._backend.setValue(key, value)
            except (AttributeError, TypeError, RuntimeError):
                pass
        return normalized

    @staticmethod
    def layer_default(is_geographic: bool) -> float:
        """Return the first-use layer distance for the CRS type."""
        return GEOGRAPHIC_SAMPLE_LAYER if is_geographic else DEFAULT_SAMPLE_LAYER

    def _unit(self) -> str:
        """Return a valid sampling unit."""
        try:
            unit = self._backend.value(SAMPLING_UNIT_KEY, DEFAULT_SAMPLING_UNIT, type=str)
        except (AttributeError, TypeError, ValueError, RuntimeError):
            return DEFAULT_SAMPLING_UNIT
        return unit if unit in (SAMPLE_UNIT_PX, SAMPLE_UNIT_LAYER) else DEFAULT_SAMPLING_UNIT

    def _read_float(self, key: str, default: float) -> float:
        """Read a float from the backend, falling back to *default*."""
        try:
            raw = self._backend.value(key, default, type=float)
            return float(raw)
        except (AttributeError, TypeError, ValueError, RuntimeError):
            return default

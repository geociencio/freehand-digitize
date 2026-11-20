"""Persistence helpers for the plugin settings.

The backend is injected (``QgsSettings`` at runtime, a tiny fake in tests) and
only needs ``contains``, ``value`` and ``setValue``. Keeping the dependency out
of the module makes the storage logic unit-testable without Qt.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .constants import (
    DEFAULT_TOLERANCE,
    DISABLE_FORM_KEY,
    LEGACY_TOLERANCE_KEY,
    TOLERANCE_KEY,
)
from .geometry_rules import clamp_tolerance


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

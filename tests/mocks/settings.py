"""In-memory settings backend used by the unit tests."""

from __future__ import annotations

from typing import Any


class FakeSettings:
    """Minimal ``QSettings``-compatible store.

    Args:
        values: Initial mapping of settings keys to values.
    """

    def __init__(self, values: dict[str, Any] | None = None) -> None:
        self._values: dict[str, Any] = dict(values or {})

    @property
    def values(self) -> dict[str, Any]:
        """Return a copy of the stored values."""
        return dict(self._values)

    def contains(self, key: str) -> bool:
        """Return whether *key* exists."""
        return key in self._values

    def value(self, key: str, default: Any = None, type: Any = None) -> Any:
        """Return the stored value, coercing it to *type* when possible."""
        if key not in self._values:
            return default
        raw = self._values[key]
        if type is None:
            return raw
        if type is bool:
            return bool(raw)
        if type is float:
            return float(raw)
        return type(raw)

    def setValue(self, key: str, value: Any) -> None:  # noqa: N802 - QSettings API
        """Store *value* at *key*."""
        self._values[key] = value

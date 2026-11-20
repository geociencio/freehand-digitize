"""Stroke sampling shared by the map tool and the unit tests.

The recorder keeps the stroke in **layer coordinates** (so on-the-fly
reprojection is handled by the caller) while distance thinning uses **device
pixel** coordinates. Pixel-based thinning is CRS-independent and avoids the bug
in the original implementation, which compared layer distances against
``mapUnitsPerPixel``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import (
    DEFAULT_SAMPLE_LAYER,
    MAX_STROKE_POINTS,
    MIN_SAMPLE_PIXELS,
    SAMPLE_UNIT_LAYER,
    SAMPLE_UNIT_PX,
)


@dataclass(frozen=True)
class SamplingOptions:
    """Vertex thinning options.

    Attributes:
        unit: ``px`` for device pixels or ``layer`` for layer CRS units.
        distance_px: Minimum distance in device pixels.
        distance_layer: Minimum distance in layer units (metres/degrees).
    """

    unit: str = SAMPLE_UNIT_PX
    distance_px: float = MIN_SAMPLE_PIXELS
    distance_layer: float = DEFAULT_SAMPLE_LAYER


@dataclass
class StrokeRecorder:
    """Accumulate the vertices of one freehand stroke.

    Attributes:
        options: Pixel or layer-unit thinning options.
        max_points: Hard cap on the number of recorded vertices.
    """

    options: SamplingOptions = field(default_factory=SamplingOptions)
    max_points: int = MAX_STROKE_POINTS
    _points: list[tuple[float, float]] = field(default_factory=list)
    _last_device: tuple[float, float] | None = None
    _last_layer: tuple[float, float] | None = None

    def reset(self) -> None:
        """Forget the current stroke."""
        self._points.clear()
        self._last_device = None
        self._last_layer = None

    def start(
        self,
        layer_point: tuple[float, float],
        device_point: tuple[float, float],
    ) -> None:
        """Begin a new stroke with its first vertex.

        Args:
            layer_point: First vertex in layer coordinates.
            device_point: First vertex in device (pixel) coordinates.
        """
        self.reset()
        layer = (float(layer_point[0]), float(layer_point[1]))
        self._points.append(layer)
        self._last_layer = layer
        self._last_device = (float(device_point[0]), float(device_point[1]))

    def add(
        self,
        layer_point: tuple[float, float],
        device_point: tuple[float, float],
    ) -> bool:
        """Append a vertex when it is far enough from the previous one.

        Args:
            layer_point: Candidate vertex in layer coordinates.
            device_point: Candidate vertex in device (pixel) coordinates.

        Returns:
            ``True`` when the vertex was recorded.
        """
        device = (float(device_point[0]), float(device_point[1]))
        layer = (float(layer_point[0]), float(layer_point[1]))
        if self.options.unit == SAMPLE_UNIT_LAYER:
            if self._last_layer is not None:
                dx = layer[0] - self._last_layer[0]
                dy = layer[1] - self._last_layer[1]
                distance = self.options.distance_layer
                if dx * dx + dy * dy < distance * distance:
                    return False
        elif self._last_device is not None:
            dx = device[0] - self._last_device[0]
            dy = device[1] - self._last_device[1]
            distance = self.options.distance_px
            if dx * dx + dy * dy < distance * distance:
                return False
        if len(self._points) >= self.max_points:
            return False
        self._points.append(layer)
        self._last_device = device
        self._last_layer = layer
        return True

    @property
    def points(self) -> list[tuple[float, float]]:
        """Return a copy of the recorded layer-space vertices."""
        return list(self._points)

    def __len__(self) -> int:
        """Return the number of recorded vertices."""
        return len(self._points)

    @property
    def is_empty(self) -> bool:
        """Return whether no vertex has been recorded."""
        return not self._points

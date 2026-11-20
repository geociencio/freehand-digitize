"""Plugin-wide constants shared by the core and GUI layers.

This module must stay dependency-free (no QGIS, no Qt) so it can be imported by
the mock-free unit tests and by the tooling.
"""

from __future__ import annotations

PLUGIN_NAME = "Freehand Digitize"
PLUGIN_ID = "freehand_digitize"
LOG_TAG = PLUGIN_NAME

#: QSettings key used by this plugin for the simplification tolerance.
TOLERANCE_KEY = f"{PLUGIN_ID}/tolerance"
#: Legacy key written by the original freehandEditing plugin (migrated on first load).
LEGACY_TOLERANCE_KEY = "freehandEdit/tolerance"
#: QGIS global setting that disables the attribute form after digitizing.
DISABLE_FORM_KEY = "qgis/digitizing/disable_enter_attribute_values_dialog"

TOLERANCE_MIN = 0.0
TOLERANCE_MAX = 5.0
TOLERANCE_DECIMALS = 3
TOLERANCE_STEP = 0.1
DEFAULT_TOLERANCE = 0.0

#: Minimum distance, in device pixels, between two recorded stroke vertices.
MIN_SAMPLE_PIXELS = 1.5
#: Safety cap so a stuck pointer cannot grow the stroke without bound.
MAX_STROKE_POINTS = 20000

#: Sampling units: device pixels or layer CRS units (metres/degrees).
SAMPLE_UNIT_PX = "px"
SAMPLE_UNIT_LAYER = "layer"
SAMPLING_UNIT_KEY = f"{PLUGIN_ID}/sampling_unit"
SAMPLING_PX_KEY = f"{PLUGIN_ID}/sampling_distance_px"
SAMPLING_LAYER_KEY = f"{PLUGIN_ID}/sampling_distance_layer"
DEFAULT_SAMPLING_UNIT = SAMPLE_UNIT_PX
DEFAULT_SAMPLE_PX = MIN_SAMPLE_PIXELS
DEFAULT_SAMPLE_LAYER = 0.5
#: First-use layer distance for geographic CRS (degrees; ~11 m at the equator).
GEOGRAPHIC_SAMPLE_LAYER = 0.0001
SAMPLE_PX_MIN = 0.5
SAMPLE_PX_MAX = 50.0
SAMPLE_PX_DECIMALS = 1
SAMPLE_PX_STEP = 0.5
SAMPLE_LAYER_MIN = 0.000001
SAMPLE_LAYER_MAX = 100000.0
SAMPLE_LAYER_DECIMALS = 6
SAMPLE_LAYER_STEP = 0.1

MIN_LINE_POINTS = 2
MIN_POLYGON_POINTS = 3
#: A closed ring needs the three vertices plus the repeated first point.
MIN_POLYGON_RING_POINTS = 4

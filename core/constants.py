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

MIN_LINE_POINTS = 2
MIN_POLYGON_POINTS = 3
#: A closed ring needs the three vertices plus the repeated first point.
MIN_POLYGON_RING_POINTS = 4

EDIT_COMMAND_TEXT = "Freehand Digitize: añadir entidad"

ACTION_TEXT = "Dibujo a mano alzada"
ACTION_TOOLTIP = (
    "Arrastra con el botón izquierdo para dibujar una línea o un polígono en la "
    "capa activa.\nMantén Ctrl para ajustar el primer y el último vértice; "
    "Esc cancela el trazo."
)
TOLERANCE_TOOLTIP = (
    "Tolerancia de simplificación en unidades de la capa (0 = sin simplificación).\n"
    "Se desactiva con CRS geográficos, donde la simplificación siempre usa 0."
)
TOLERANCE_TOOLTIP_GEOGRAPHIC = (
    "La capa activa usa un CRS geográfico: la tolerancia se ignora y la simplificación usa 0."
)

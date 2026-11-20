"""Translatable user-facing strings for the plugin.

All strings use the ``FreehandDigitize`` translation context so a single
catalog covers the toolbar, map tool, feature creator and warnings. The source
language is Spanish; English is provided by ``i18n/freehand_digitize_en.ts``.

The literals stay inside ``QCoreApplication.translate`` calls so ``pylupdate6``
can extract them; do not replace them with variables.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import QCoreApplication


def action_text() -> str:
    """Return the toolbar/menu action text."""
    return QCoreApplication.translate("FreehandDigitize", "Dibujo a mano alzada")


def action_tooltip() -> str:
    """Return the action tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Arrastra con el botón izquierdo para dibujar una línea o un polígono en la "
        "capa activa.\nMantén Ctrl para ajustar el primer y el último vértice; "
        "Esc cancela el trazo.",
    )


def tolerance_tooltip() -> str:
    """Return the projection-aware tolerance tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Tolerancia de simplificación en unidades de la capa (0 = sin simplificación).\n"
        "Se desactiva con CRS geográficos, donde la simplificación siempre usa 0.",
    )


def tolerance_tooltip_geographic() -> str:
    """Return the tooltip shown for geographic layers."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "La capa activa usa un CRS geográfico: la tolerancia se ignora y la simplificación usa 0.",
    )


def edit_command_text() -> str:
    """Return the undo-stack label for a created feature."""
    return QCoreApplication.translate("FreehandDigitize", "Freehand Digitize: añadir entidad")

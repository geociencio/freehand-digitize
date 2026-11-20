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


def reshape_action_text() -> str:
    """Return the reshape action text."""
    return QCoreApplication.translate("FreehandDigitize", "Reformar geometría")


def reshape_action_tooltip() -> str:
    """Return the reshape action tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Dibuja un trazo que cruce la geometría que quieras reformar. Si hay una "
        "selección, solo se reformarán las entidades seleccionadas.",
    )


def reshape_edit_command_text() -> str:
    """Return the undo-stack label for a reshape operation."""
    return QCoreApplication.translate("FreehandDigitize", "Freehand Digitize: reformar entidad(es)")


def no_feature_under_stroke_text() -> str:
    """Return the warning shown when the stroke crosses no feature."""
    return QCoreApplication.translate("FreehandDigitize", "El trazo no cruza ninguna entidad.")


def no_reshape_happened_text() -> str:
    """Return the warning shown when candidates could not be reshaped."""
    return QCoreApplication.translate("FreehandDigitize", "El trazo no reformó ninguna entidad.")


def invalid_reshaped_geometry_text() -> str:
    """Return the warning shown when the reshaped geometry is invalid."""
    return QCoreApplication.translate(
        "FreehandDigitize", "La geometría reformada no es válida; no se modificó nada."
    )


def reshape_rejected_text(name: str) -> str:
    """Return the warning shown when the provider rejects a reshape."""
    return QCoreApplication.translate(
        "FreehandDigitize", "La capa «{name}» rechazó la reforma."
    ).format(name=name)


def reshaped_count_text(count: int) -> str:
    """Return the information message shown after a successful reshape."""
    return QCoreApplication.translate(
        "FreehandDigitize", "{count} entidad(es) reformada(s)."
    ).format(count=count)

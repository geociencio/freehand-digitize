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


def edit_mode_required_text(name: str) -> str:
    """Return the warning shown when the layer is not in edit mode."""
    return QCoreApplication.translate(
        "FreehandDigitize", "Activa la edición de la capa «{name}» antes de dibujar."
    ).format(name=name)


def sampling_action_text() -> str:
    """Return the sampling-settings action text."""
    return QCoreApplication.translate("FreehandDigitize", "Configuración de muestreo")


def sampling_action_tooltip() -> str:
    """Return the sampling-settings action tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Elige la unidad y la distancia mínima entre vértices del trazo.",
    )


def sampling_dialog_title() -> str:
    """Return the sampling dialog title."""
    return QCoreApplication.translate("FreehandDigitize", "Configuración de muestreo")


def sampling_unit_label() -> str:
    """Return the sampling-unit field label."""
    return QCoreApplication.translate("FreehandDigitize", "Unidad de muestreo:")


def sampling_pixels_text() -> str:
    """Return the pixels unit label."""
    return QCoreApplication.translate("FreehandDigitize", "Píxeles")


def sampling_layer_units_text() -> str:
    """Return the layer-units unit label."""
    return QCoreApplication.translate("FreehandDigitize", "Unidades de la capa")


def sampling_distance_label() -> str:
    """Return the minimum-distance field label."""
    return QCoreApplication.translate("FreehandDigitize", "Distancia mínima:")


def sampling_distance_tooltip() -> str:
    """Return the minimum-distance tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize", "Distancia mínima entre vértices del trazo."
    )


def sampling_help_text() -> str:
    """Return the general sampling explanation."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Píxeles: independiente del CRS y del zoom. Unidades de capa: depende del CRS.",
    )


def sampling_geographic_warning_text() -> str:
    """Return the geographic-CRS warning."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "La capa activa usa un CRS geográfico. En unidades de capa la distancia se "
        "mide en grados; un grado de longitud no tiene una longitud constante "
        "(depende de la latitud). Usa píxeles si quieres una densidad uniforme en "
        "pantalla.",
    )


def sampling_ok_text() -> str:
    """Return the dialog OK button text."""
    return QCoreApplication.translate("FreehandDigitize", "Aceptar")


def sampling_cancel_text() -> str:
    """Return the dialog Cancel button text."""
    return QCoreApplication.translate("FreehandDigitize", "Cancelar")


def sampling_reset_text() -> str:
    """Return the dialog Reset button text."""
    return QCoreApplication.translate("FreehandDigitize", "Restablecer")


def difference_action_text() -> str:
    """Return the feature-difference action text."""
    return QCoreApplication.translate("FreehandDigitize", "Diferencia de entidades")


def difference_action_tooltip() -> str:
    """Return the feature-difference action tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Resta una entidad de otra. Con dos entidades seleccionadas abre el "
        "diálogo; si no, haz clic en la objetivo y luego en la de corte.",
    )


def difference_dialog_title() -> str:
    """Return the difference dialog title."""
    return QCoreApplication.translate("FreehandDigitize", "Diferencia de entidades")


def difference_target_label() -> str:
    """Return the target-feature field label."""
    return QCoreApplication.translate("FreehandDigitize", "Entidad objetivo:")


def difference_cutter_label() -> str:
    """Return the cutter-feature field label."""
    return QCoreApplication.translate("FreehandDigitize", "Entidad de corte:")


def difference_help_text() -> str:
    """Return the difference dialog explanation."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "La entidad objetivo se actualiza; la de corte no se modifica.",
    )


def difference_pick_target_text() -> str:
    """Return the first pick-tool instruction."""
    return QCoreApplication.translate("FreehandDigitize", "Haz clic en la entidad objetivo.")


def difference_pick_cutter_text() -> str:
    """Return the second pick-tool instruction."""
    return QCoreApplication.translate("FreehandDigitize", "Haz clic en la entidad de corte.")


def difference_same_feature_text() -> str:
    """Return the warning for picking the same feature twice."""
    return QCoreApplication.translate(
        "FreehandDigitize", "La entidad de corte debe ser distinta de la objetivo."
    )


def difference_empty_text() -> str:
    """Return the warning for an empty difference."""
    return QCoreApplication.translate(
        "FreehandDigitize", "La diferencia está vacía; no se modificó la entidad."
    )


def difference_invalid_text() -> str:
    """Return the warning for an invalid difference."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "La geometría resultante no es válida; no se modificó la entidad.",
    )


def difference_rejected_text(name: str) -> str:
    """Return the warning for a provider-rejected difference."""
    return QCoreApplication.translate(
        "FreehandDigitize", "La capa «{name}» rechazó la diferencia."
    ).format(name=name)


def difference_edit_command_text() -> str:
    """Return the undo-stack label for a difference operation."""
    return QCoreApplication.translate(
        "FreehandDigitize", "Freehand Digitize: diferencia de entidades"
    )


def difference_apply_text() -> str:
    """Return the difference dialog Apply button text."""
    return QCoreApplication.translate("FreehandDigitize", "Aplicar")


def difference_applied_text() -> str:
    """Return the information message after a successful difference."""
    return QCoreApplication.translate("FreehandDigitize", "Diferencia aplicada.")

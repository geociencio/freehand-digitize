"""Translatable user-facing strings for the plugin.

All strings use the ``FreehandDigitize`` translation context so a single
catalog covers the toolbar, map tool, feature creator and warnings. The source
language is English; Spanish and the other locales are provided by the catalogs
in ``i18n/``.

The literals stay inside ``QCoreApplication.translate`` calls so ``pylupdate6``
can extract them; do not replace them with variables.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import QCoreApplication


def action_text() -> str:
    """Return the toolbar/menu action text."""
    return QCoreApplication.translate("FreehandDigitize", "Freehand digitize")


def action_tooltip() -> str:
    """Return the action tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Drag with the left mouse button to draw a line or polygon on the active "
        "layer.\nHold Ctrl to snap the first and last vertex; Esc cancels the "
        "stroke.",
    )


def tolerance_tooltip() -> str:
    """Return the projection-aware tolerance tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Simplification tolerance in layer units (0 = no simplification).\n"
        "Disabled for geographic CRS, where simplification always uses 0.",
    )


def tolerance_tooltip_geographic() -> str:
    """Return the tooltip shown for geographic layers."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "The active layer uses a geographic CRS: the tolerance is ignored and "
        "simplification uses 0.",
    )


def edit_command_text() -> str:
    """Return the undo-stack label for a created feature."""
    return QCoreApplication.translate("FreehandDigitize", "Freehand Digitize: add feature")


def reshape_action_text() -> str:
    """Return the reshape action text."""
    return QCoreApplication.translate("FreehandDigitize", "Reshape feature")


def reshape_action_tooltip() -> str:
    """Return the reshape action tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Draw a stroke crossing the geometry you want to reshape. If there is a "
        "selection, only the selected features are reshaped.",
    )


def reshape_edit_command_text() -> str:
    """Return the undo-stack label for a reshape operation."""
    return QCoreApplication.translate("FreehandDigitize", "Freehand Digitize: reshape feature(s)")


def no_feature_under_stroke_text() -> str:
    """Return the warning shown when the stroke crosses no feature."""
    return QCoreApplication.translate("FreehandDigitize", "The stroke does not cross any feature.")


def no_reshape_happened_text() -> str:
    """Return the warning shown when candidates could not be reshaped."""
    return QCoreApplication.translate("FreehandDigitize", "The stroke did not reshape any feature.")


def invalid_reshaped_geometry_text() -> str:
    """Return the warning shown when the reshaped geometry is invalid."""
    return QCoreApplication.translate(
        "FreehandDigitize", "The reshaped geometry is not valid; nothing was changed."
    )


def reshape_rejected_text(name: str) -> str:
    """Return the warning shown when the provider rejects a reshape."""
    return QCoreApplication.translate(
        "FreehandDigitize", "Layer “{name}” rejected the reshape."
    ).format(name=name)


def reshaped_count_text(count: int) -> str:
    """Return the information message shown after a successful reshape."""
    return QCoreApplication.translate("FreehandDigitize", "{count} feature(s) reshaped.").format(
        count=count
    )


def edit_mode_required_text(name: str) -> str:
    """Return the warning shown when the layer is not in edit mode."""
    return QCoreApplication.translate(
        "FreehandDigitize", "Start editing layer “{name}” before drawing."
    ).format(name=name)


def sampling_action_text() -> str:
    """Return the sampling-settings action text."""
    return QCoreApplication.translate("FreehandDigitize", "Sampling settings")


def sampling_action_tooltip() -> str:
    """Return the sampling-settings action tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Choose the unit and the minimum distance between stroke vertices.",
    )


def sampling_dialog_title() -> str:
    """Return the sampling dialog title."""
    return QCoreApplication.translate("FreehandDigitize", "Sampling settings")


def sampling_unit_label() -> str:
    """Return the sampling-unit field label."""
    return QCoreApplication.translate("FreehandDigitize", "Sampling unit:")


def sampling_pixels_text() -> str:
    """Return the pixels unit label."""
    return QCoreApplication.translate("FreehandDigitize", "Pixels")


def sampling_layer_units_text() -> str:
    """Return the layer-units unit label."""
    return QCoreApplication.translate("FreehandDigitize", "Layer units")


def sampling_distance_label() -> str:
    """Return the minimum-distance field label."""
    return QCoreApplication.translate("FreehandDigitize", "Minimum distance:")


def sampling_distance_tooltip() -> str:
    """Return the minimum-distance tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize", "Minimum distance between stroke vertices."
    )


def sampling_help_text() -> str:
    """Return the general sampling explanation."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Pixels: independent of CRS and zoom. Layer units: depends on the CRS.",
    )


def sampling_geographic_warning_text() -> str:
    """Return the geographic-CRS warning."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "The active layer uses a geographic CRS. In layer units the distance is "
        "measured in degrees; one degree of longitude is not a constant length "
        "(it depends on latitude). Use pixels for a uniform on-screen density.",
    )


def sampling_ok_text() -> str:
    """Return the dialog OK button text."""
    return QCoreApplication.translate("FreehandDigitize", "OK")


def sampling_cancel_text() -> str:
    """Return the dialog Cancel button text."""
    return QCoreApplication.translate("FreehandDigitize", "Cancel")


def sampling_reset_text() -> str:
    """Return the dialog Reset button text."""
    return QCoreApplication.translate("FreehandDigitize", "Reset")


def difference_action_text() -> str:
    """Return the feature-difference action text."""
    return QCoreApplication.translate("FreehandDigitize", "Feature difference")


def difference_action_tooltip() -> str:
    """Return the feature-difference action tooltip."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "Subtract one feature from another. With two selected features the dialog "
        "opens; otherwise click the target and then the cutter.",
    )


def difference_dialog_title() -> str:
    """Return the difference dialog title."""
    return QCoreApplication.translate("FreehandDigitize", "Feature difference")


def difference_target_label() -> str:
    """Return the target-feature field label."""
    return QCoreApplication.translate("FreehandDigitize", "Target feature:")


def difference_cutter_label() -> str:
    """Return the cutter-feature field label."""
    return QCoreApplication.translate("FreehandDigitize", "Cutter feature:")


def difference_help_text() -> str:
    """Return the difference dialog explanation."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "The target feature is updated; the cutter is not modified.",
    )


def difference_pick_target_text() -> str:
    """Return the first pick-tool instruction."""
    return QCoreApplication.translate("FreehandDigitize", "Click the target feature.")


def difference_pick_cutter_text() -> str:
    """Return the second pick-tool instruction."""
    return QCoreApplication.translate("FreehandDigitize", "Click the cutter feature.")


def difference_same_feature_text() -> str:
    """Return the warning for picking the same feature twice."""
    return QCoreApplication.translate(
        "FreehandDigitize", "The cutter feature must be different from the target."
    )


def difference_empty_text() -> str:
    """Return the warning for an empty difference."""
    return QCoreApplication.translate(
        "FreehandDigitize", "The difference is empty; the feature was not changed."
    )


def difference_invalid_text() -> str:
    """Return the warning for an invalid difference."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "The resulting geometry is not valid; the feature was not changed.",
    )


def difference_rejected_text(name: str) -> str:
    """Return the warning for a provider-rejected difference."""
    return QCoreApplication.translate(
        "FreehandDigitize", "Layer “{name}” rejected the difference."
    ).format(name=name)


def difference_edit_command_text() -> str:
    """Return the undo-stack label for a difference operation."""
    return QCoreApplication.translate("FreehandDigitize", "Freehand Digitize: feature difference")


def difference_apply_text() -> str:
    """Return the difference dialog Apply button text."""
    return QCoreApplication.translate("FreehandDigitize", "Apply")


def difference_applied_text() -> str:
    """Return the information message after a successful difference."""
    return QCoreApplication.translate("FreehandDigitize", "Difference applied.")


def layer_gone_text() -> str:
    """Return the warning used when the layer was deleted."""
    return QCoreApplication.translate(
        "FreehandDigitize",
        "The layer is no longer available; the operation was cancelled.",
    )

"""Load the Qt translation catalog that matches the QGIS user locale.

Adapted from the SecInterp loader: read ``locale/userLocale`` from QGIS
settings, try the full locale and then the two-letter language, load the first
``.qm`` found and install it on the QCoreApplication. The caller must keep the
returned ``QTranslator`` alive and remove it on unload.

The plugin source language is English; if no catalog matches (for example an
unknown locale or an ``en_US`` user) the English source strings are shown.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator

PLUGIN_ID = "freehand_digitize"


def locale_candidates(locale: str) -> list[str]:
    """Return the catalog codes to try for *locale*, most specific first.

    Args:
        locale: Locale name such as ``en_US``, ``pt_BR`` or ``fr``.

    Returns:
        A de-duplicated list, e.g. ``["pt_BR", "pt"]``.
    """
    normalized = (locale or "").replace("-", "_").strip()
    if not normalized:
        return []
    candidates = [normalized]
    language = normalized.split("_", 1)[0]
    if language and language not in candidates:
        candidates.append(language)
    return candidates


def install_translations(
    settings: Any = None,
    plugin_dir: Path | None = None,
) -> QTranslator | None:
    """Install the catalog matching the QGIS user locale.

    Args:
        settings: Settings backend exposing ``value`` (``QgsSettings`` by default).
        plugin_dir: Plugin root; defaults to the parent of ``gui/``.

    Returns:
        The installed translator, or ``None`` when no catalog matches.
    """
    from qgis.core import QgsSettings

    backend = settings if settings is not None else QgsSettings()
    try:
        user_locale = str(backend.value("locale/userLocale", "") or "")
    except (AttributeError, TypeError, RuntimeError):
        user_locale = ""
    if not user_locale:
        user_locale = QLocale.system().name()

    root = plugin_dir or Path(__file__).resolve().parent.parent
    for code in locale_candidates(user_locale):
        catalog = root / "i18n" / f"{PLUGIN_ID}_{code}.qm"
        if not catalog.is_file():
            continue
        translator = QTranslator()
        if not translator.load(str(catalog)):
            continue
        app = QCoreApplication.instance()
        if app is None:
            return None
        app.installTranslator(translator)
        return translator
    return None


def remove_translations(translator: QTranslator | None) -> None:
    """Remove *translator* from the application, if it is installed.

    Args:
        translator: Translator returned by :func:`install_translations`.
    """
    if translator is None:
        return
    app = QCoreApplication.instance()
    if app is not None:
        app.removeTranslator(translator)

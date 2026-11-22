#!/usr/bin/env python3
"""Update ``metadata.txt`` with the languages that have a catalog.

The base language is English; each ``i18n/freehand_digitize_<code>.ts`` adds a
translated language to the ``general_description`` line.

Usage:
    python scripts/i18n/update_metadata_languages.py
"""

from __future__ import annotations

from pathlib import Path

BASE_LANGUAGE = "English"
PLUGIN_PREFIX = "freehand_digitize_"
I18N_DIR = Path("i18n")
METADATA_FILE = Path("metadata.txt")

ISO_MAP = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt_BR": "Portuguese (Brazil)",
    "nl": "Dutch",
    "ja": "Japanese",
    "ko": "Korean",
    "sv": "Swedish",
    "zh_CN": "Chinese (Simplified)",
    "ru": "Russian",
    "pl": "Polish",
    "es": "Spanish",
    "fi": "Finnish",
    "hi": "Hindi",
    "id": "Indonesian",
    "tr": "Turkish",
}


LOCALE_ORDER = ("es", "pt_BR", "fr", "de", "it", "id")


def supported_languages() -> list[str]:
    """Return the source language plus every catalog found in ``i18n/``.

    Returns:
        Language names in deterministic order, base language first and the
        release locales in priority order.
    """
    discovered = {
        path.stem.removeprefix(PLUGIN_PREFIX) for path in I18N_DIR.glob(f"{PLUGIN_PREFIX}*.ts")
    }
    codes = [code for code in LOCALE_ORDER if code in discovered]
    codes += sorted(discovered - set(codes))
    languages = [BASE_LANGUAGE]
    for code in codes:
        name = ISO_MAP.get(code, code)
        if name not in languages:
            languages.append(name)
    return languages


def _escape_percent(text: str) -> str:
    """Escape ``%`` for configparser-compatible metadata.txt values."""
    return text.replace("%", "%%")


def update_metadata() -> int:
    """Insert or replace the ``general_description`` language line.

    Returns:
        Process exit code.
    """
    if not METADATA_FILE.is_file():
        print("metadata.txt not found")
        return 1

    languages = supported_languages()
    line = (
        f"general_description={_escape_percent('Supported languages: ' + ', '.join(languages))}\n"
    )
    lines = METADATA_FILE.read_text(encoding="utf-8").splitlines(keepends=True)

    for index, current in enumerate(lines):
        if current.startswith("general_description="):
            lines[index] = line
            break
    else:
        for index, current in enumerate(lines):
            if current.startswith("description="):
                lines.insert(index + 1, line)
                break
        else:
            lines.insert(0, line)

    METADATA_FILE.write_text("".join(lines), encoding="utf-8")
    print(f"Updated metadata.txt languages: {', '.join(languages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(update_metadata())

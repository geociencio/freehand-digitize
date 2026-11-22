#!/usr/bin/env python3
"""Inject master-data translations into a Qt ``.ts`` catalog.

Adapted from the SecInterp ``apply_full.py`` workflow: translations live in
``scripts/i18n/master_data/<lang>.json`` (source text -> translated text) and
are injected with ElementTree, never by editing the XML by hand.

Usage:
    python scripts/i18n/apply_full.py es scripts/i18n/master_data/es.json
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PLUGIN_PREFIX = "freehand_digitize_"
I18N_DIR = Path("i18n")


def apply_translations(ts_path: Path, translations: dict[str, str]) -> int:
    """Apply *translations* to *ts_path* and return how many were set.

    Args:
        ts_path: Qt ``.ts`` catalog to update.
        translations: Mapping of source text to translated text.

    Returns:
        Number of messages that received a translation.
    """
    tree = ET.parse(ts_path)
    root = tree.getroot()
    count = 0
    for context in root.findall("context"):
        for message in context.findall("message"):
            source = message.findtext("source")
            if not source:
                continue
            translated = translations.get(source) or translations.get(source.strip())
            if not translated:
                continue
            node = message.find("translation")
            if node is None:
                continue
            node.text = translated
            node.attrib.pop("type", None)
            count += 1

    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ")
    tree.write(ts_path, encoding="utf-8", xml_declaration=True)
    return count


def main() -> int:
    """Run the injector from the repository root.

    Returns:
        Process exit code.
    """
    if len(sys.argv) != 3:
        print("Usage: python scripts/i18n/apply_full.py <lang> <master_json>")
        return 2

    lang = sys.argv[1]
    json_path = Path(sys.argv[2])
    ts_path = I18N_DIR / f"{PLUGIN_PREFIX}{lang}.ts"

    if not ts_path.is_file():
        print(f"Catalog not found: {ts_path}")
        return 1
    if not json_path.is_file():
        print(f"Master data not found: {json_path}")
        return 1

    translations = json.loads(json_path.read_text(encoding="utf-8"))
    count = apply_translations(ts_path, translations)
    print(f"Applied {count} translations to {ts_path} ({lang})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

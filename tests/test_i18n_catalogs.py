"""Quality gates for the shipped Qt translation catalogs."""

from __future__ import annotations

import configparser
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
LOCALES = ["en"]
PLACEHOLDER = re.compile(r"(\{[^}]*\})")


def messages(locale: str):
    """Yield every ``message`` element of a locale catalog."""
    root = ET.parse(I18N / f"freehand_digitize_{locale}.ts").getroot()
    for context in root.findall("context"):
        yield from context.findall("message")


class TestTranslationCatalogs(unittest.TestCase):
    """The English catalog must be complete, safe and packaged."""

    def test_catalogs_exist(self) -> None:
        """Every configured locale has a source catalog."""
        for locale in LOCALES:
            self.assertTrue(
                (I18N / f"freehand_digitize_{locale}.ts").is_file(),
                f"missing .ts for {locale}",
            )

    def test_no_unfinished_messages(self) -> None:
        """Untranslated entries are rejected before release."""
        offenders = {}
        for locale in LOCALES:
            unfinished = [
                message.findtext("source")
                for message in messages(locale)
                if message.find("translation") is not None
                and message.find("translation").get("type") == "unfinished"
            ]
            if unfinished:
                offenders[locale] = unfinished
        self.assertEqual(offenders, {}, f"Unfinished translations: {offenders}")

    def test_all_messages_have_translation_text(self) -> None:
        """Empty translations are rejected."""
        offenders = {}
        for locale in LOCALES:
            missing = [
                message.findtext("source")
                for message in messages(locale)
                if not (message.findtext("translation") or "").strip()
            ]
            if missing:
                offenders[locale] = missing
        self.assertEqual(offenders, {}, f"Empty translations: {offenders}")

    def test_placeholders_are_preserved(self) -> None:
        """``{name}``/``{error}`` placeholders must survive translation."""
        offenders = []
        for locale in LOCALES:
            for message in messages(locale):
                source = message.findtext("source") or ""
                translation = message.findtext("translation") or ""
                if set(PLACEHOLDER.findall(source)) != set(PLACEHOLDER.findall(translation)):
                    offenders.append(f"{locale}: {source!r} -> {translation!r}")
        self.assertEqual(offenders, [], f"Placeholder mismatch: {offenders}")

    def test_key_ui_strings_are_translated(self) -> None:
        """The strings a user sees first must be translated, not copied."""
        required = {
            "Dibujo a mano alzada": "Freehand digitize",
            "Entidad no válida": "Invalid feature",
            "Selecciona una capa vectorial de línea o polígono editable antes de dibujar.": (
                "Select an editable line or polygon vector layer before drawing."
            ),
        }
        for locale in LOCALES:
            pairs = {
                message.findtext("source"): message.findtext("translation")
                for message in messages(locale)
            }
            for source, expected in required.items():
                self.assertEqual(pairs.get(source), expected, f"{locale}: {source!r}")

    def test_compiled_catalogs_exist(self) -> None:
        """The ZIP must ship non-empty ``.qm`` files."""
        missing = [
            locale
            for locale in LOCALES
            if not (I18N / f"freehand_digitize_{locale}.qm").is_file()
            or (I18N / f"freehand_digitize_{locale}.qm").stat().st_size == 0
        ]
        self.assertEqual(missing, [], f"Missing/empty .qm catalogs: {missing}")

    def test_metadata_lists_languages(self) -> None:
        """``metadata.txt`` advertises the source and translated languages."""
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(ROOT / "metadata.txt", encoding="utf-8")
        description = parser["general"].get("general_description", "")
        self.assertIn("Spanish", description)
        self.assertIn("English", description)


if __name__ == "__main__":
    unittest.main()

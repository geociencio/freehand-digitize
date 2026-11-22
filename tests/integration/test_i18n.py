"""Integration tests for English-source translation loading."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.integration.qgis_env import ensure_qgis_app, requires_qgis

ROOT = Path(__file__).resolve().parents[2]


@requires_qgis
class TestTranslationLoading(unittest.TestCase):
    """The six catalogs must load from the English source."""

    @classmethod
    def setUpClass(cls) -> None:
        """Bootstrap QGIS and import the modules under test."""
        ensure_qgis_app()
        from qgis.PyQt.QtCore import QCoreApplication, QTranslator

        from freehand_digitize.gui.i18n import (
            install_translations,
            locale_candidates,
            remove_translations,
        )
        from tests.mocks.settings import FakeSettings

        cls.QCoreApplication = QCoreApplication
        cls.QTranslator = QTranslator
        cls.install_translations = staticmethod(install_translations)
        cls.remove_translations = staticmethod(remove_translations)
        cls.locale_candidates = staticmethod(locale_candidates)
        cls.FakeSettings = FakeSettings

    def setUp(self) -> None:
        """Track an installed translator for cleanup."""
        self.translator = None

    def tearDown(self) -> None:
        """Remove the translator installed by the test."""
        self.remove_translations(self.translator)

    def test_locale_candidates(self) -> None:
        """Full locale first, then the two-letter language."""
        self.assertEqual(self.locale_candidates("pt_BR"), ["pt_BR", "pt"])
        self.assertEqual(self.locale_candidates("en_US"), ["en_US", "en"])
        self.assertEqual(self.locale_candidates("fr"), ["fr"])
        self.assertEqual(self.locale_candidates(""), [])

    def test_catalog_translates_ui_string(self) -> None:
        """The compiled Spanish catalog maps the English source."""
        catalog = ROOT / "i18n" / "freehand_digitize_es.qm"
        self.assertTrue(catalog.is_file())
        translator = self.QTranslator()
        self.assertTrue(translator.load(str(catalog)))
        self.QCoreApplication.installTranslator(translator)
        self.translator = translator
        translated = self.QCoreApplication.translate("FreehandDigitize", "Freehand digitize")
        self.assertEqual(translated, "Dibujo a mano alzada")

    def test_all_catalogs_load(self) -> None:
        """Every shipped catalog maps a key English source."""
        for locale in ("es", "pt_BR", "fr", "de", "it", "id"):
            with self.subTest(locale=locale):
                catalog = ROOT / "i18n" / f"freehand_digitize_{locale}.qm"
                self.assertTrue(catalog.is_file())
                translator = self.QTranslator()
                self.assertTrue(translator.load(str(catalog)))
                translated = translator.translate("FreehandDigitize", "Freehand digitize")
                self.assertNotEqual(translated, "Freehand digitize")

    def test_install_translations_for_spanish_locale(self) -> None:
        """The loader picks the Spanish catalog for es_ES."""
        settings = self.FakeSettings({"locale/userLocale": "es_ES"})
        translator = self.install_translations(settings, plugin_dir=ROOT)
        self.assertIsNotNone(translator)
        self.translator = translator
        self.assertEqual(
            self.QCoreApplication.translate("FreehandDigitize", "Freehand Digitize: add feature"),
            "Freehand Digitize: añadir entidad",
        )

    def test_english_locale_uses_source_strings(self) -> None:
        """No catalog is installed for en_US; the source is English."""
        settings = self.FakeSettings({"locale/userLocale": "en_US"})
        self.assertIsNone(self.install_translations(settings, plugin_dir=ROOT))
        self.assertEqual(
            self.QCoreApplication.translate("FreehandDigitize", "Freehand digitize"),
            "Freehand digitize",
        )


if __name__ == "__main__":
    unittest.main()

"""Structural tests for the QGIS plugin metadata."""

from __future__ import annotations

import configparser
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METADATA = ROOT / "metadata.txt"


class TestMetadata(unittest.TestCase):
    """Required fields and packaging values."""

    @classmethod
    def setUpClass(cls) -> None:
        """Parse the metadata file once."""
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(METADATA, encoding="utf-8")
        cls.meta = parser["general"]

    def test_required_fields(self) -> None:
        """The QGIS plugin repository requires these keys."""
        for key in ("name", "description", "version", "author", "email"):
            self.assertTrue(self.meta.get(key), f"missing metadata field: {key}")

    def test_qgis_versions(self) -> None:
        """The plugin targets QGIS 3.28 through 4.x."""
        self.assertEqual(self.meta["qgisMinimumVersion"], "3.28")
        self.assertEqual(self.meta["qgisMaximumVersion"], "4.99")
        # QGIS 4 Ready is marked by qgisMaximumVersion >= 4.0; supportsQt6 is
        # deprecated by qgis-manage 0.17 and must not be required.
        self.assertNotIn("supportsQt6", self.meta)

    def test_version_matches_release(self) -> None:
        """The metadata version is the 2.0.1 release."""
        self.assertEqual(self.meta["version"], "2.0.1")
        self.assertIn("2.0.1", self.meta["changelog"])

    def test_source_links(self) -> None:
        """The portal needs a repository and a tracker/homepage."""
        self.assertTrue(self.meta.get("repository"))
        self.assertTrue(self.meta.get("homepage"))
        self.assertTrue(self.meta.get("tracker"))

    def test_icon_is_a_png(self) -> None:
        """The metadata icon exists and is a real PNG."""
        icon = ROOT / self.meta["icon"]
        self.assertTrue(icon.is_file(), f"icon not found: {icon}")
        self.assertEqual(icon.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

"""Fail make test-qgis when QGIS is unavailable."""

from __future__ import annotations

import importlib
import os
import unittest


@unittest.skipUnless(
    os.environ.get("REQUIRE_QGIS") == "1",
    "integration gate only under make test-qgis",
)
class TestQGISGate(unittest.TestCase):
    """The integration target must never pass with every test skipped."""

    def test_qgis_is_importable(self) -> None:
        """Fail instead of silently skipping the whole integration suite."""
        try:
            importlib.import_module("qgis")
        except ImportError as exc:
            self.fail(
                "QGIS is not importable in this interpreter; set QGIS_PYTHON "
                f"to a Python with QGIS (error: {exc})"
            )


if __name__ == "__main__":
    unittest.main()

"""Shared test base class.

The suite is split into two layers:

* ``tests/core`` are pure unit tests (no QGIS, no Qt) and run in the uv
  environment;
* ``tests/integration`` require a real QGIS and are skipped automatically when
  ``qgis`` cannot be imported.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path


class BaseTestCase(unittest.TestCase):
    """Provide a temporary directory and small assertion helpers."""

    def setUp(self) -> None:
        """Create a temporary working directory."""
        super().setUp()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="freehand_digitize_"))

    def tearDown(self) -> None:
        """Remove the temporary working directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        super().tearDown()

    def assert_close(
        self,
        first: float,
        second: float,
        places: int = 7,
        message: str | None = None,
    ) -> None:
        """Assert that two floats are equal within *places* decimals."""
        self.assertAlmostEqual(first, second, places=places, msg=message)

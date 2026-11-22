#!/usr/bin/env python3
"""Run QGIS integration tests and flush Qt deferred deletes before exit."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.integration.qgis_env import ensure_qgis_app  # noqa: E402


def flush_qt() -> None:
    """Process deferred Qt deletions before the interpreter exits."""
    try:
        ensure_qgis_app()
        from qgis.PyQt.QtCore import QCoreApplication, QEvent

        app = QCoreApplication.instance()
        if app is None:
            return
        app.processEvents()
        app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
    except unittest.SkipTest:
        return


def main() -> int:
    """Run the integration suite, flush Qt and return the test status."""
    suite = unittest.defaultTestLoader.discover("tests/integration", top_level_dir=".")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    flush_qt()
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

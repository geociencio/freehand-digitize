"""QGIS availability detection and application bootstrap for integration tests."""

from __future__ import annotations

import importlib.util
import os
import unittest

# Must be set before QgsApplication/Qt widgets are created.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QGIS_AVAILABLE = importlib.util.find_spec("qgis") is not None
requires_qgis = unittest.skipUnless(QGIS_AVAILABLE, "QGIS is not installed")

_APP = None


def ensure_qgis_app():
    """Create (once) and return the QGIS application instance.

    Returns:
        The global ``QgsApplication``.

    Raises:
        unittest.SkipTest: When QGIS is not importable.
    """
    global _APP
    if not QGIS_AVAILABLE:
        raise unittest.SkipTest("QGIS is not installed")
    if _APP is None:
        from qgis.core import QgsApplication

        _APP = QgsApplication.instance()
        if _APP is None:
            _APP = QgsApplication([], False)
            _APP.initQgis()
    return _APP

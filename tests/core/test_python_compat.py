"""Guard the plugin's Python 3.9 runtime compatibility.

The development environment uses Python 3.12, but QGIS 3.28 ships Python 3.9.
The plugin code must therefore parse with the 3.9 grammar; newer syntax would
break older QGIS installations even though the local test suite is green.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SOURCES = [
    ROOT / "__init__.py",
    ROOT / "freehand_plugin.py",
    *sorted((ROOT / "core").glob("*.py")),
    *sorted((ROOT / "gui").glob("*.py")),
]


class TestPython39Syntax(unittest.TestCase):
    """Every shipped module parses with ``feature_version=(3, 9)``."""

    def test_sources_parse_as_python_39(self) -> None:
        """Reject syntax that QGIS 3.28's Python 3.9 cannot parse."""
        for path in PLUGIN_SOURCES:
            source = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(ROOT))):
                ast.parse(source, filename=str(path), feature_version=(3, 9))


if __name__ == "__main__":
    unittest.main()

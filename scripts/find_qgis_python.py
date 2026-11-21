#!/usr/bin/env python3
"""Print a Python interpreter that can import QGIS.

The Makefile uses this to avoid running the integration suite with a virtualenv
interpreter that has no QGIS (which would silently skip every test).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

CANDIDATES = (
    "python3",
    "/usr/bin/python3",
    "/usr/local/bin/python3",
    "python",
    "python3.12",
    "python3.11",
    "python3.10",
    "python-qgis",
)


def _candidates() -> list[str]:
    """Return the explicit override or the built-in search list."""
    override = os.environ.get("QGIS_PYTHON")
    if override:
        return [override]
    return list(CANDIDATES)


def _works(candidate: str) -> str | None:
    """Return the resolved path when *candidate* can import QGIS."""
    path = shutil.which(candidate) or candidate
    if not Path(path).exists():
        return None
    try:
        result = subprocess.run(
            [path, "-c", "import qgis"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return path if result.returncode == 0 else None


def main() -> int:
    """Print the first interpreter that imports QGIS."""
    for candidate in _candidates():
        path = _works(candidate)
        if path is not None:
            print(path)
            return 0
    print(
        "No Python interpreter with QGIS found; set QGIS_PYTHON=/path/to/python3.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

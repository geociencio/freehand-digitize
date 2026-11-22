"""Unit tests for the release-note validator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_release_notes.py"


class TestReleaseNoteValidator(unittest.TestCase):
    """The validator catches missing, placeholder and mismatched notes."""

    def setUp(self) -> None:
        """Create a temporary notes directory."""
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.notes = Path(self._tmp.name)

    def _run(self, version: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--version",
                version,
                "--notes-dir",
                str(self.notes),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def _write(self, version: str, body: str) -> None:
        (self.notes / f"v{version}.md").write_text(body, encoding="utf-8")

    def _valid(self, version: str) -> str:
        return (
            f"# Freehand Digitize v{version} — Test release\n\n"
            "**Compatibility:** QGIS 3.28–4.x\n\n"
            "## Highlights\n\n- Test.\n\n"
            "## Verification\n\n- Tests: 1.\n"
        )

    def test_valid_note_passes(self) -> None:
        """A complete note exits zero."""
        self._write("1.2.3", self._valid("1.2.3"))
        self.assertEqual(self._run("1.2.3").returncode, 0)

    def test_missing_note_fails(self) -> None:
        """A missing note is rejected."""
        self.assertEqual(self._run("1.2.3").returncode, 1)

    def test_placeholder_fails(self) -> None:
        """An unresolved placeholder is rejected."""
        self._write("1.2.3", self._valid("1.2.3").replace("- Test.", "- TODO."))
        self.assertIn("placeholder", self._run("1.2.3").stdout.lower())

    def test_version_mismatch_fails(self) -> None:
        """A heading with another version is rejected."""
        self._write("1.2.3", self._valid("9.9.9"))
        self.assertIn("heading version", self._run("1.2.3").stdout)


if __name__ == "__main__":
    unittest.main()

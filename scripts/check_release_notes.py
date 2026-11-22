#!/usr/bin/env python3
"""Validate a versioned Freehand Digitize release note."""

from __future__ import annotations

import argparse
import configparser
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NOTES_DIR = ROOT / "docs" / "releases" / "notes"
VERSION_RE = re.compile(r"^# Freehand Digitize v(\d+\.\d+\.\d+)\b", re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"\bTODO\b|\bTBD\b|\{version\}|YYYY-MM-DD|\bpendiente\b", re.IGNORECASE)
REQUIRED_HEADINGS = ("## Highlights", "## Verification")


def metadata_version(path: Path = ROOT / "metadata.txt") -> str:
    """Return the version declared in ``metadata.txt``."""
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(path, encoding="utf-8")
    return parser["general"]["version"]


def validate_note(text: str, version: str) -> list[str]:
    """Return validation errors for *text* and *version*."""
    errors: list[str] = []
    match = VERSION_RE.search(text)
    if match is None:
        errors.append("missing '# Freehand Digitize vX.Y.Z' heading")
    elif match.group(1) != version:
        errors.append(f"heading version {match.group(1)} != {version}")
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading {heading!r}")
    if "QGIS" not in text:
        errors.append("missing QGIS compatibility information")
    placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
    if placeholders:
        errors.append(f"unresolved placeholders: {', '.join(placeholders)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    """Validate the release note for a version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=None, help="release version (default: metadata.txt)")
    parser.add_argument(
        "--notes-dir",
        type=Path,
        default=DEFAULT_NOTES_DIR,
        help="directory containing vX.Y.Z.md notes",
    )
    args = parser.parse_args(argv)
    version = args.version or metadata_version()
    note = args.notes_dir / f"v{version}.md"
    if not note.is_file():
        print(f"❌ Release note not found: {note}")
        return 1
    errors = validate_note(note.read_text(encoding="utf-8"), version)
    if errors:
        print(f"❌ Invalid release note: {note}")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"✅ Release note valid: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

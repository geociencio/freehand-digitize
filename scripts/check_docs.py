#!/usr/bin/env python3
"""Validate relative Markdown links in the project documentation.

Scans the root documentation and every Markdown file under ``docs/``. External
URLs, anchors and placeholders are ignored; code fences are skipped so examples
do not produce false positives.

Exit code 1 lists every broken link; 0 means the tree is consistent.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_SKIP_PREFIXES = ("#", "http://", "https://", "mailto:", "tel:")
_PLACEHOLDERS = ("YYYY", "relative/path", "{", "}", "<", ">")

DOC_FILES = [
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "AGENTS.md",
    ROOT / "AI_CONTEXT.md",
    *sorted((ROOT / "docs").rglob("*.md")),
]


def check_file(path: Path) -> list[tuple[Path, str]]:
    """Return the broken links found in *path*.

    Args:
        path: Markdown file to inspect.

    Returns:
        A list of ``(file, target)`` pairs for links whose target does not exist.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []
    content = FENCE_RE.sub("", content)

    issues: list[tuple[Path, str]] = []
    for match in LINK_RE.finditer(content):
        target = match.group(1).strip()
        if not target or target.startswith(_SKIP_PREFIXES):
            continue
        if any(marker in target for marker in _PLACEHOLDERS):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        if not resolved.exists():
            issues.append((path, target))
    return issues


def main() -> int:
    """Run the documentation link check.

    Returns:
        Process exit code (0 when every link resolves, 1 otherwise).
    """
    issues: list[tuple[Path, str]] = []
    checked = 0
    for path in DOC_FILES:
        if path.is_file():
            checked += 1
            issues.extend(check_file(path))

    if issues:
        for path, target in issues:
            print(f"❌ {path.relative_to(ROOT)}: broken link '{target}'")
        print(f"\n{len(issues)} broken link(s) in {checked} documentation file(s).")
        return 1

    print(f"✅ {checked} documentation files: relative links OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

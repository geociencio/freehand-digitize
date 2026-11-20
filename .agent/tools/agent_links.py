#!/usr/bin/env python3
"""Markdown link validation for the agentic system."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import forge_paths

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_FENCED_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_PLACEHOLDERS = ("YYYY", "relative/path", "{", "}", "<", ">")


@dataclass
class LinkIssue:
    """A broken or non-portable Markdown link."""

    file: Path
    target: str
    reason: str

    def __str__(self) -> str:
        """Render the issue for CLI output."""
        return f"  [{self.file}] {self.target}: {self.reason}"


def markdown_files() -> list[Path]:
    """Return the Markdown files that make up the agentic documentation."""
    files: list[Path] = []
    for root in (forge_paths.FRAMEWORK_DIR, forge_paths.STATE_DIR):
        if root.is_dir():
            files.extend(sorted(root.rglob("*.md")))
    for path in (
        forge_paths.AGENTS_FILE,
        forge_paths.QUICK_REFERENCE_FILE,
    ):
        if path.is_file():
            files.append(path)
    if forge_paths.PROJECT_SCAFFOLD_DIR.is_dir():
        files.extend(sorted(forge_paths.PROJECT_SCAFFOLD_DIR.rglob("*.md")))
    # Keep the order deterministic while dropping duplicates.
    return list(dict.fromkeys(files))


def check_links() -> list[LinkIssue]:
    """Return broken relative links, ignoring external and placeholder URLs."""
    issues: list[LinkIssue] = []
    for path in markdown_files():
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        content = _FENCED_BLOCK_RE.sub("", content)

        for match in _LINK_RE.finditer(content):
            target = match.group(1).strip()
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            if any(marker in target for marker in _PLACEHOLDERS):
                continue
            if target.startswith("file://"):
                issues.append(LinkIssue(path, target, "absolute file:// URL"))
                continue

            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                issues.append(LinkIssue(path, target, "target does not exist"))
    return issues

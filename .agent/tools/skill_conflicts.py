#!/usr/bin/env python3
"""Cross-skill conflict detector."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import forge_paths
from frontmatter import parse_frontmatter

PROJECT_ROOT = forge_paths.PROJECT_ROOT


def load_skills(skills_dir: Path) -> list[dict[str, Any]]:
    """Load every skill under ``skills_dir`` with its frontmatter metadata."""
    skills: list[dict[str, Any]] = []
    for path in sorted(skills_dir.glob("*/SKILL.md")):
        metadata = parse_frontmatter(path.read_text(encoding="utf-8"))
        metadata["path"] = str(path.relative_to(PROJECT_ROOT))
        metadata["dir"] = path.parent.name
        skills.append(metadata)
    return skills


def check_completeness(skills: list[dict[str, Any]]) -> list[str]:
    """Report skills missing required frontmatter fields."""
    issues: list[str] = []
    for skill in skills:
        for required in ("name", "description"):
            if not skill.get(required):
                issues.append(f"{skill.get('dir', '?')}: missing '{required}' field in SKILL.md")
    return issues


def check_duplicates(skills: list[dict[str, Any]]) -> list[str]:
    """Report duplicate skill names or copy-pasted descriptions/triggers."""
    issues: list[str] = []
    names = Counter(str(skill.get("name")) for skill in skills if skill.get("name"))
    for name, count in names.items():
        if count > 1:
            issues.append(f"duplicate skill name '{name}' ({count} times)")

    descriptions = Counter(
        str(skill.get("description")) for skill in skills if skill.get("description")
    )
    for description, count in descriptions.items():
        if count > 1:
            issues.append(f"duplicate description shared by {count} skills: {description[:60]}...")

    triggers = Counter(
        _normalize_trigger(str(skill.get("trigger"))) for skill in skills if skill.get("trigger")
    )
    for trigger, count in triggers.items():
        if trigger and count > 1:
            issues.append(f"duplicate trigger shared by {count} skills: {trigger[:60]}")
    return issues


def _normalize_trigger(value: str) -> str:
    """Normalize a trigger for duplicate detection."""
    return re.sub(r"\s+", " ", value.strip().lower())


def find_conflicts(skills: list[dict[str, Any]]) -> list[str]:
    """Aggregate all conflict detections into a single issue list."""
    issues: list[str] = []
    issues.extend(check_completeness(skills))
    issues.extend(check_duplicates(skills))
    return issues


def conflicts_main() -> None:
    """CLI entry point for cross-skill conflict detection."""
    quiet = "--quiet" in sys.argv
    skill_roots = forge_paths.skill_dirs()
    if not skill_roots:
        print("❌ No skills directory found", file=sys.stderr)
        sys.exit(1)

    skills = [skill for root in skill_roots for skill in load_skills(root)]
    if not quiet:
        print(f"🔍 Scanned {len(skills)} active skills for conflicts")

    issues = find_conflicts(skills)
    if not issues:
        if not quiet:
            print("✅ No skill conflicts or overlaps detected.")
        sys.exit(0)

    print(f"⚠️  Found {len(issues)} potential skill conflict(s):")
    for issue in issues:
        print(f"  - {issue}")
    sys.exit(1)


if __name__ == "__main__":
    conflicts_main()

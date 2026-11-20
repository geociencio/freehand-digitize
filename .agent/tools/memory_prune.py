#!/usr/bin/env python3
"""Memory pruning utility.

By default this command is a **dry-run**: it reports the consolidated lessons
and ``next_steps`` snapshots that would be removed. Pass ``--apply`` to actually
rewrite the lessons file and delete expired snapshots.

Lessons may be stored either as a fenced YAML block (legacy) or as Markdown
bullet entries. Retention rules:
* Lessons older than 90 days that have a ``consolidated_in`` target.
* ``next_steps`` snapshots older than 90 days.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import forge_paths

PROJECT_ROOT = forge_paths.PROJECT_ROOT
LESSONS_FILE = forge_paths.LESSONS_FILE
NEXT_STEPS_DIR = forge_paths.HISTORY_DIR / "next_steps"
PRUNE_DAYS = 90
NEXT_STEPS_RETENTION_DAYS = 90
MAX_ACTIVE_LINES = forge_paths.MAX_LESSON_LINES

_YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
_BULLET_DATE_RE = re.compile(r"^-\s+date:\s*(\S+)")
_BULLET_FIELD_RE = re.compile(r"^\s+([A-Za-z_]+):\s*(.*)$")
_PRUNED_RE = re.compile(r"  # \[PRUNED\] .*|^- \[PRUNED\] .*")
_SNAPSHOT_RE = re.compile(r"next_steps_(\d{4}-\d{2}-\d{2})")
_LESSON_HEADER = "  # ─── ACTIVE LESSONS (< 90 days or not yet in a SKILL.md) ───────────────────\n"
_PRUNED_HEADER = (
    "\n  # ─── PRUNED LESSONS (already in SKILL.md — kept as index only) ─────────────\n"
)
_PRUNED_FOOTER = (
    "  # The following entries have been fully absorbed into specialized skills.\n"
    "  # They are retained here as a consolidated index only.\n"
    "  #\n"
)


def _yaml_module() -> Any:
    """Import PyYAML lazily so bullet-style lessons need no extra dependency."""
    try:
        import yaml
    except ImportError:  # pragma: no cover - depends on the environment
        return None
    return yaml


def _parse_date(value: Any) -> datetime:
    """Coerce a lesson date value into a datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return datetime.strptime(str(value), "%Y-%m-%d")


def _is_prunable(lesson: dict[str, Any], threshold: datetime) -> tuple[bool, datetime | None, str]:
    """Return whether a lesson is old and consolidated."""
    if not isinstance(lesson, dict):
        return False, None, ""
    try:
        lesson_date = _parse_date(lesson.get("date"))
    except (TypeError, ValueError):
        return False, None, ""
    consolidated = lesson.get("consolidated_in") or lesson.get("consolidated")
    return (
        bool(lesson_date < threshold and consolidated),
        lesson_date,
        str(consolidated),
    )


def _split_lessons(
    lessons: list[dict[str, Any]], threshold: datetime
) -> tuple[list[dict[str, Any]], list[tuple[datetime, str, str]]]:
    """Split lessons into active entries and prune candidates."""
    active: list[dict[str, Any]] = []
    pruned: list[tuple[datetime, str, str]] = []
    for lesson in lessons:
        if not lesson:
            continue
        prunable, lesson_date, consolidated = _is_prunable(lesson, threshold)
        if prunable and lesson_date is not None:
            category = str(lesson.get("category", "GENERAL"))
            topic = str(lesson.get("topic", "Unknown"))
            pruned.append((lesson_date, f"{category}/{topic}", consolidated))
        else:
            active.append(lesson)
    return active, pruned


def _render_lessons(
    active: list[dict[str, Any]], pruned: list[tuple[datetime, str, str]], raw_yaml: str
) -> str:
    """Render the updated lessons YAML block."""
    yaml = _yaml_module()
    if yaml is None:  # pragma: no cover - guarded by the caller
        raise RuntimeError("PyYAML is required to rewrite a YAML lessons block")

    final_yaml = "lessons:\n\n" + _LESSON_HEADER
    for lesson in active:
        if isinstance(lesson.get("date"), (datetime, date)):
            lesson["date"] = lesson["date"].strftime("%Y-%m-%d")
        lesson_yaml = yaml.dump(
            [lesson],
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            indent=2,
        )
        final_yaml += "".join(f"  {line}\n" for line in lesson_yaml.splitlines())

    final_yaml += _PRUNED_HEADER + _PRUNED_FOOTER
    entries = [
        f"  # [PRUNED] {pruned_date.strftime('%Y-%m-%d')} {label} → {target}"
        for pruned_date, label, target in pruned
    ]
    entries.extend(_PRUNED_RE.findall(raw_yaml))
    entries.sort(reverse=True)
    final_yaml += "\n".join(entries)
    return final_yaml


def _write_atomic(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically."""
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def _parse_bullet_lessons(content: str) -> list[dict[str, Any]]:
    """Parse Markdown bullet lessons into dicts with line ranges."""
    lines = content.splitlines()
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for index, line in enumerate(lines):
        match = _BULLET_DATE_RE.match(line)
        if match:
            if current is not None:
                current["end"] = index
                entries.append(current)
            current = {"date": match.group(1), "start": index, "end": len(lines)}
            continue
        if current is None:
            continue
        if line.startswith("#") or not line.strip():
            current["end"] = index
            entries.append(current)
            current = None
            continue
        field_match = _BULLET_FIELD_RE.match(line)
        if field_match:
            current[field_match.group(1)] = field_match.group(2).strip().strip('"')

    if current is not None:
        current["end"] = len(lines)
        entries.append(current)
    return entries


def _prune_bullet_lessons(content: str, apply: bool) -> tuple[int, str | None]:
    """Prune consolidated Markdown-bullet lessons."""
    threshold = datetime.now() - timedelta(days=PRUNE_DAYS)
    entries = _parse_bullet_lessons(content)
    if not entries:
        print("No lessons found in AGENT_LESSONS.md")
        return 0, None

    prunable: list[dict[str, Any]] = []
    for entry in entries:
        ok, lesson_date, _consolidated = _is_prunable(entry, threshold)
        if ok and lesson_date is not None:
            entry["_parsed_date"] = lesson_date
            prunable.append(entry)

    if not prunable:
        print("No lessons meet the pruning criteria (consolidated & > 90 days).")
        return 0, None

    for entry in prunable:
        print(
            f"  - {entry['_parsed_date'].strftime('%Y-%m-%d')} "
            f"{entry.get('category', 'GENERAL')}/{entry.get('topic', 'Unknown')}"
        )

    if not apply:
        print(f"Dry-run: {len(prunable)} lesson(s) would be pruned. Use --apply.")
        return len(prunable), None

    lines = content.splitlines()
    remove: set[int] = set()
    for entry in prunable:
        remove.update(range(entry["start"], entry["end"]))
    kept = [line for index, line in enumerate(lines) if index not in remove]

    pruned_lines = []
    for entry in prunable:
        consolidated = entry.get("consolidated_in") or entry.get("consolidated")
        pruned_lines.append(
            f"- [PRUNED] {entry['_parsed_date'].strftime('%Y-%m-%d')} "
            f"{entry.get('category', 'GENERAL')}/{entry.get('topic', 'Unknown')} "
            f"→ {consolidated}"
        )

    new_content = "\n".join(kept).rstrip() + "\n"
    if "## Pruned Lessons" not in new_content:
        new_content += "\n## Pruned Lessons\n"
    new_content = new_content.rstrip() + "\n\n" + "\n".join(pruned_lines) + "\n"
    print(f"Successfully pruned {len(prunable)} lessons.")
    return len(prunable), new_content


def prune_lessons(apply: bool = False, lessons_file: Path = LESSONS_FILE) -> int:
    """Prune consolidated lessons older than 90 days.

    Args:
        apply: When False (default), only report what would be pruned.
        lessons_file: Lessons file to inspect (overridable for tests).

    Returns:
        Number of lessons that were (or would be) pruned.
    """
    if not lessons_file.exists():
        print(f"Error: {lessons_file} not found.")
        return 0

    content = lessons_file.read_text(encoding="utf-8")
    yaml_match = _YAML_BLOCK_RE.search(content)
    if yaml_match:
        yaml = _yaml_module()
        if yaml is None:
            print("Error: YAML lessons require PyYAML (pip install PyYAML).")
            return 0
        raw_yaml = yaml_match.group(1)
        try:
            data = yaml.safe_load(raw_yaml)
        except yaml.YAMLError as exc:  # pragma: no cover - defensive parser guard
            print(f"Error parsing YAML: {exc}")
            return 0
        lessons = data.get("lessons", []) if isinstance(data, dict) else []
        if not isinstance(lessons, list):
            print("Error: 'lessons' must be a list")
            return 0
        if not lessons:
            print("No lessons found in AGENT_LESSONS.md")
            return 0

        threshold = datetime.now() - timedelta(days=PRUNE_DAYS)
        active, pruned = _split_lessons(lessons, threshold)
        if not pruned:
            print("No lessons meet the pruning criteria (consolidated & > 90 days).")
            return 0
        for lesson_date, label, target in pruned:
            print(f"  - {lesson_date.strftime('%Y-%m-%d')} {label} → {target}")
        if not apply:
            print(f"Dry-run: {len(pruned)} lesson(s) would be pruned. Use --apply.")
            return len(pruned)

        new_yaml = _render_lessons(active, pruned, raw_yaml)
        _write_atomic(lessons_file, content.replace(raw_yaml, new_yaml))
        print(f"Successfully pruned {len(pruned)} lessons. Updated {lessons_file}")
        return len(pruned)

    count, new_content = _prune_bullet_lessons(content, apply)
    if new_content is not None:
        _write_atomic(lessons_file, new_content)
    return count


def prune_next_steps_snapshots(directory: Path = NEXT_STEPS_DIR, apply: bool = False) -> int:
    """Prune next_steps snapshots older than the retention window.

    Args:
        directory: Snapshot directory (overridable for tests).
        apply: When False (default), only report what would be removed.

    Returns:
        Number of snapshots that were (or would be) removed.
    """
    if not directory.exists():
        print(f"Info: {directory} not found. Nothing to prune.")
        return 0

    threshold = datetime.now() - timedelta(days=NEXT_STEPS_RETENTION_DAYS)
    candidates: list[Path] = []
    for path in sorted(directory.glob("next_steps_*.md")):
        match = _SNAPSHOT_RE.search(path.name)
        if match:
            try:
                file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
            except ValueError:
                file_date = datetime.fromtimestamp(path.stat().st_mtime)
        else:
            file_date = datetime.fromtimestamp(path.stat().st_mtime)
        if file_date < threshold:
            candidates.append(path)

    if not candidates:
        print("No next_steps snapshots meet the pruning criteria (> 90 days).")
        return 0

    for path in candidates:
        print(f"  - {path.name}")

    if not apply:
        print(f"Dry-run: {len(candidates)} snapshot(s) would be removed. Use --apply.")
        return len(candidates)

    for path in candidates:
        path.unlink()
    print(f"Successfully pruned {len(candidates)} next_steps snapshots.")
    return len(candidates)


def count_active_lines(lessons_file: Path | None = None) -> int:
    """Return the number of lines in the active lesson log."""
    path = lessons_file or LESSONS_FILE
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


def check_line_limit(lessons_file: Path | None = None) -> tuple[bool, int]:
    """Check the lesson log against the configured line budget."""
    lines = count_active_lines(lessons_file)
    return lines <= MAX_ACTIVE_LINES, lines


def check_main() -> None:
    """Exit non-zero when AGENT_LESSONS.md exceeds the line budget."""
    within_limit, lines = check_line_limit()
    if not within_limit:
        print(
            f"❌ AGENT_LESSONS.md has {lines} lines (limit {MAX_ACTIVE_LINES}). "
            "Run `forge.py memory prune --apply`, consolidate into a SKILL.md and "
            "archive the full text under .agent-state/history/memory/.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"✅ AGENT_LESSONS.md has {lines} lines (limit {MAX_ACTIVE_LINES}).")


def main() -> None:
    """CLI entry point: dry-run by default, ``--apply`` to mutate files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rewrite lessons and delete expired snapshots",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify the lesson line budget",
    )
    args = parser.parse_args()
    if args.check:
        check_main()
        return
    lessons = prune_lessons(apply=args.apply)
    snapshots = prune_next_steps_snapshots(apply=args.apply)
    if not args.apply and (lessons or snapshots):
        print("Re-run with --apply to make these changes.")


if __name__ == "__main__":
    main()

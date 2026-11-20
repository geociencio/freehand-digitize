"""Tests for the safe memory-pruning tooling."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import memory_prune


def _lessons_file(tmp_path: Path) -> Path:
    old = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
    recent = datetime.now().strftime("%Y-%m-%d")
    path = tmp_path / "AGENT_LESSONS.md"
    path.write_text(
        "# Lessons\n\n"
        "```yaml\n"
        "lessons:\n"
        f"  - date: {old}\n"
        "    category: TESTING\n"
        "    topic: old lesson\n"
        "    lesson: old lesson body\n"
        "    action: old action\n"
        "    consolidated_in: testing-standards\n"
        f"  - date: {recent}\n"
        "    category: TOOLING\n"
        "    topic: recent lesson\n"
        "    lesson: recent lesson body\n"
        "    action: recent action\n"
        "```\n",
        encoding="utf-8",
    )
    return path


def test_prune_lessons_is_dry_run_by_default(tmp_path: Path) -> None:
    path = _lessons_file(tmp_path)
    before = path.read_text(encoding="utf-8")

    pruned = memory_prune.prune_lessons(apply=False, lessons_file=path)

    assert pruned == 1
    assert path.read_text(encoding="utf-8") == before


def test_prune_lessons_applies_and_indexes(tmp_path: Path) -> None:
    path = _lessons_file(tmp_path)

    pruned = memory_prune.prune_lessons(apply=True, lessons_file=path)

    content = path.read_text(encoding="utf-8")
    assert pruned == 1
    assert "topic: recent lesson" in content
    assert "topic: old lesson" not in content
    assert "[PRUNED]" in content
    assert "testing-standards" in content


def test_prune_snapshots_is_dry_run_by_default(tmp_path: Path) -> None:
    old = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
    snapshot = tmp_path / f"next_steps_{old}.md"
    snapshot.write_text("old", encoding="utf-8")

    removed = memory_prune.prune_next_steps_snapshots(directory=tmp_path, apply=False)

    assert removed == 1
    assert snapshot.exists()


def test_prune_snapshots_applies(tmp_path: Path) -> None:
    old = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
    snapshot = tmp_path / f"next_steps_{old}.md"
    snapshot.write_text("old", encoding="utf-8")

    removed = memory_prune.prune_next_steps_snapshots(directory=tmp_path, apply=True)

    assert removed == 1
    assert not snapshot.exists()


def _bullet_lessons_file(tmp_path: Path) -> Path:
    old = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
    recent = datetime.now().strftime("%Y-%m-%d")
    path = tmp_path / "AGENT_LESSONS.md"
    path.write_text(
        "# Lessons\n\n"
        f"- date: {old}\n"
        "  category: TESTING\n"
        "  topic: old bullet\n"
        "  lesson: old\n"
        "  action: old\n"
        "  consolidated_in: testing-standards\n\n"
        f"- date: {recent}\n"
        "  category: TOOLING\n"
        "  topic: recent bullet\n"
        "  lesson: recent\n"
        "  action: recent\n",
        encoding="utf-8",
    )
    return path


def test_bullet_lessons_dry_run_by_default(tmp_path: Path) -> None:
    path = _bullet_lessons_file(tmp_path)
    before = path.read_text(encoding="utf-8")

    pruned = memory_prune.prune_lessons(apply=False, lessons_file=path)

    assert pruned == 1
    assert path.read_text(encoding="utf-8") == before


def test_bullet_lessons_apply_and_index(tmp_path: Path) -> None:
    path = _bullet_lessons_file(tmp_path)

    pruned = memory_prune.prune_lessons(apply=True, lessons_file=path)

    content = path.read_text(encoding="utf-8")
    assert pruned == 1
    assert "recent bullet" in content
    assert "topic: old bullet" not in content
    assert "[PRUNED]" in content


def test_line_limit_uses_configured_budget(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "AGENT_LESSONS.md"
    path.write_text("\n".join("line" for _ in range(20)), encoding="utf-8")
    monkeypatch.setattr(memory_prune, "MAX_ACTIVE_LINES", 10)

    within_limit, lines = memory_prune.check_line_limit(path)

    assert within_limit is False
    assert lines == 20

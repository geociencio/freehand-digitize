"""Regression tests for metric scanning and TOML configuration handling."""

from __future__ import annotations

from pathlib import Path

import forge_metrics_checks
import forge_paths


def test_should_skip_metrics_file(tmp_path: Path, monkeypatch) -> None:
    metrics = tmp_path / "agent_metrics.json"
    metrics.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(forge_metrics_checks, "METRICS_FILE", metrics)

    assert forge_metrics_checks.should_skip_file(metrics) is True


def test_should_skip_tool_caches(tmp_path: Path) -> None:
    for cache in (".mypy_cache", ".ruff_cache", ".pytest_cache", "__pycache__", ".git"):
        path = tmp_path / cache / "state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
        assert forge_metrics_checks.should_skip_file(path) is True


def test_should_not_skip_regular_documentation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(forge_metrics_checks, "METRICS_FILE", tmp_path / "agent_metrics.json")
    document = tmp_path / "notes.md"
    document.write_text("# Notes\n", encoding="utf-8")

    assert forge_metrics_checks.should_skip_file(document) is False


def test_invalid_toml_is_reported_and_ignored(tmp_path: Path, capsys) -> None:
    (tmp_path / "forge.toml").write_text("broken = [", encoding="utf-8")

    assert forge_paths._load_config(tmp_path) == {}
    assert "cannot read" in capsys.readouterr().err

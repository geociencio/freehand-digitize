"""Tests for the forge.toml project command runner."""

from __future__ import annotations

import sys

import project_commands
import pytest


def test_run_executes_configured_command(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(project_commands.forge_paths, "PROJECT_ROOT", tmp_path)
    command = f'"{sys.executable}" -c "import sys; sys.exit(0)"'

    with pytest.raises(SystemExit) as exc:
        project_commands._run(command, "test_command")

    assert exc.value.code == 0
    assert "$ " in capsys.readouterr().out


def test_run_reports_missing_command(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        project_commands._run(None, "test_command")

    assert exc.value.code == 2
    assert "No [project].test_command" in capsys.readouterr().err

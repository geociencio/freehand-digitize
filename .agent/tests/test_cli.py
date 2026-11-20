"""Tests for the framework CLI, versioning and packaging requirements."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import forge_paths
import pytest

FRAMEWORK = Path(__file__).resolve().parent.parent
TOOLS = FRAMEWORK / "tools"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOLS / "forge.py"), *args],
        cwd=FRAMEWORK,
        capture_output=True,
        text=True,
        check=False,
    )


def test_version_flag_reports_framework_version() -> None:
    result = _run("--version")

    assert result.returncode == 0
    assert result.stdout.startswith("agentic-forge ")
    assert (FRAMEWORK / "VERSION").read_text(encoding="utf-8").strip() in result.stdout


def test_version_file_is_semver_and_documented() -> None:
    version = (FRAMEWORK / "VERSION").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)

    for name in ("README.md", "QUICK_REFERENCE.md", "CHANGELOG.md"):
        text = (FRAMEWORK / name).read_text(encoding="utf-8")
        assert version in text, name


def test_requirements_declare_runtime_dependencies() -> None:
    requirements = (FRAMEWORK / "requirements.txt").read_text(encoding="utf-8")

    assert "PyYAML" in requirements
    assert "tomli" in requirements
    assert "3.11" in requirements


def test_help_lists_version_and_project_commands() -> None:
    result = _run("--help")

    assert result.returncode == 0
    assert "--version" in result.stdout
    assert "project" in result.stdout
    assert "memory" in result.stdout


def test_project_config_keys_are_loaded() -> None:
    """When mounted in a project, the tooling consumes its forge.toml keys."""
    if not (FRAMEWORK.parent / "forge.toml").is_file():
        pytest.skip("standalone framework checkout")

    assert forge_paths.TEST_COMMAND
    assert forge_paths.LINT_COMMAND
    assert forge_paths.MAX_LESSON_LINES == 350
    assert forge_paths.STRICT_AGENT_SYSTEM is True

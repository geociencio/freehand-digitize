#!/usr/bin/env python3
"""Run project commands declared in ``forge.toml``.

The shared workflows use this module so that projects can keep using pytest,
unittest, or another runner without forking the framework workflows. Commands
are read from the ``[project]`` table:

    test_command, test_command_full, lint_command, format_command, type_command

Commands are executed with the project root as working directory. They are
trusted configuration owned by the consuming repository.
"""

from __future__ import annotations

import subprocess
import sys

import forge_paths


def _run(command: str | None, label: str) -> None:
    """Run a configured command or explain how to configure it."""
    if not command:
        print(
            f"❌ No [project].{label} configured in forge.toml. "
            "Add it or run the project's command manually.",
            file=sys.stderr,
        )
        sys.exit(2)
    print(f"$ {command}")
    result = subprocess.run(
        command,
        cwd=forge_paths.PROJECT_ROOT,
        shell=True,
        check=False,
    )
    sys.exit(result.returncode)


def test_main() -> None:
    """Run ``[project].test_command``."""
    _run(forge_paths.TEST_COMMAND, "test_command")


def test_full_main() -> None:
    """Run ``[project].test_command_full`` (falls back to test_command)."""
    _run(forge_paths.TEST_COMMAND_FULL, "test_command_full")


def bump_main() -> None:
    """Run ``[project].version_bump_command``."""
    _run(forge_paths.VERSION_BUMP_COMMAND, "version_bump_command")


def lint_main() -> None:
    """Run ``[project].lint_command``."""
    _run(forge_paths.LINT_COMMAND, "lint_command")


def format_main() -> None:
    """Run ``[project].format_command``."""
    _run(forge_paths.FORMAT_COMMAND, "format_command")


def type_main() -> None:
    """Run ``[project].type_command``."""
    _run(forge_paths.TYPE_COMMAND, "type_command")


if __name__ == "__main__":
    test_main()

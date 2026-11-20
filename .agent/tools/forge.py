#!/usr/bin/env python3
"""Agentic Forge CLI — single entry point for the framework tooling.

Usage:
    python forge.py --version
    python forge.py validate [--graph] [--conflicts] [--quiet]
    python forge.py metrics <validate|report|close-session> [--topic NAME]
    python forge.py project <test|test-full|lint|format|type|bump>
    python forge.py memory <prune|check> [--apply]
    python forge.py lesson propose [--since REF]

Run it from the project root (or anywhere; paths are resolved from forge.toml).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

USAGE = __doc__
VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


def _version() -> str:
    """Return the framework version, or ``unknown`` when unavailable."""
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


SUBCOMMANDS: dict[str, dict[str, tuple[str, str]]] = {
    "project": {
        "test": ("project_commands", "test_main"),
        "test-full": ("project_commands", "test_full_main"),
        "lint": ("project_commands", "lint_main"),
        "format": ("project_commands", "format_main"),
        "type": ("project_commands", "type_main"),
        "bump": ("project_commands", "bump_main"),
    },
    "memory": {
        "prune": ("memory_prune", "main"),
        "check": ("memory_prune", "main"),
    },
    "lesson": {"propose": ("lesson_extractor", "main")},
    "metrics": {
        "validate": ("forge_metrics", "validate_main"),
        "report": ("forge_metrics", "report_main"),
        "close-session": ("forge_metrics", "close_session_main"),
    },
}


def _run(module_name: str, func_name: str, argv: list[str]) -> None:
    module = importlib.import_module(module_name)
    sys.argv = [module_name, *argv]
    getattr(module, func_name)()


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] in ("-V", "--version"):
        print(f"agentic-forge {_version()}")
        return
    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        return

    command, rest = args[0], args[1:]

    if command == "validate":
        _run("validate_agent_system", "main", rest)
        return

    if command in SUBCOMMANDS:
        if not rest or rest[0] not in SUBCOMMANDS[command]:
            options = "|".join(SUBCOMMANDS[command])
            print(f"Usage: forge.py {command} <{options}>", file=sys.stderr)
            sys.exit(2)
        sub, sub_rest = rest[0], rest[1:]
        module_name, func_name = SUBCOMMANDS[command][sub]
        if (command, sub) == ("lesson", "propose"):
            sub_rest = ["--propose", *sub_rest]
        if (command, sub) == ("memory", "check"):
            sub_rest = ["--check", *sub_rest]
        _run(module_name, func_name, sub_rest)
        return

    print(f"Unknown command: {command}\n\n{USAGE}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()

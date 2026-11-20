#!/usr/bin/env python3
"""Resolve Agentic Forge paths for the current project.

Loads ``forge.toml`` from the repository root and exposes the framework
content directory (``.agent``) and the project-state directory
(``.agent-state``). Centralising path resolution here lets the tooling run
against any project and prepares the extraction of the generic tooling into
the ``agentic-forge`` framework.

The config file is discovered by walking up from this module's location, so it
keeps working after the tooling is moved under ``.agent/tools/``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - exercised on Python 3.9/3.10
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

_CONFIG_NAME = "forge.toml"


def _find_project_root(start: Path) -> Path:
    """Return the nearest ancestor of ``start`` that contains ``forge.toml``."""
    for candidate in (start, *start.parents):
        if (candidate / _CONFIG_NAME).is_file():
            return candidate
    # Legacy fallback: this module lives in <root>/tools/ (or <root>/scripts/).
    return start.resolve().parent


def _load_config(root: Path) -> dict[str, Any]:
    """Load ``forge.toml``, returning an empty config when it is invalid."""
    config_path = root / _CONFIG_NAME
    if not config_path.is_file():
        return {}
    if tomllib is None:
        print(
            "Warning: TOML support requires Python 3.11+ or the 'tomli' package.",
            file=sys.stderr,
        )
        return {}
    try:
        with config_path.open("rb") as handle:
            return tomllib.load(handle)
    # TOMLDecodeError subclasses ValueError; catching ValueError also works
    # with the tomli fallback and keeps the except clause statically valid.
    except (OSError, ValueError) as exc:
        print(f"Warning: cannot read {config_path}: {exc}", file=sys.stderr)
        return {}


PROJECT_ROOT = _find_project_root(Path(__file__).resolve().parent)
_CONFIG_FILE = PROJECT_ROOT / _CONFIG_NAME
_HAS_PROJECT_CONFIG = _CONFIG_FILE.is_file()
_CONFIG = _load_config(PROJECT_ROOT)
_FORGE = _CONFIG.get("forge", {})
_PROJECT = _CONFIG.get("project", {})

# Project metadata / thresholds (overridable via forge.toml).
PROJECT_NAME = _PROJECT.get("name", "project")
MAX_CC = int(_PROJECT.get("max_cc", 10))
MODULE_SIZE_LIMIT = int(_PROJECT.get("module_size_limit", 400))
MAX_LESSON_LINES = int(_PROJECT.get("max_lesson_lines", 350))
STRICT_AGENT_SYSTEM = bool(_PROJECT.get("strict_agent_system", False))
TEST_COMMAND = _PROJECT.get("test_command")
TEST_COMMAND_FULL = _PROJECT.get("test_command_full") or TEST_COMMAND
LINT_COMMAND = _PROJECT.get("lint_command")
FORMAT_COMMAND = _PROJECT.get("format_command")
TYPE_COMMAND = _PROJECT.get("type_command")
VERSION_BUMP_COMMAND = _PROJECT.get("version_bump_command")

# Framework content (re-usable; may become a git submodule). A standalone
# checkout of agentic-forge has no forge.toml and acts as its own framework root.
FRAMEWORK_DIR = (
    PROJECT_ROOT / _FORGE.get("framework", ".agent") if _HAS_PROJECT_CONFIG else PROJECT_ROOT
)
SKILLS_DIR = FRAMEWORK_DIR / "skills"
WORKFLOW_DIR = FRAMEWORK_DIR / "workflows"
SCAFFOLD_DIR = FRAMEWORK_DIR / "scaffold"
PROJECT_SCAFFOLD_DIR = PROJECT_ROOT / "scaffold"
AGENTS_FILE = PROJECT_ROOT / "AGENTS.md"
QUICK_REFERENCE_FILE = FRAMEWORK_DIR / "QUICK_REFERENCE.md"
OPENCODE_FILE = PROJECT_ROOT / "opencode.json"

# Project-owned state (never shipped by the framework).
STATE_DIR = PROJECT_ROOT / _FORGE.get("state", ".agent-state")
MEMORY_DIR = STATE_DIR / "memory"
HISTORY_DIR = STATE_DIR / "history"
METRICS_FILE = MEMORY_DIR / "agent_metrics.json"
LESSONS_FILE = MEMORY_DIR / "AGENT_LESSONS.md"
MEMORY_POLICY_FILE = MEMORY_DIR / "memory_policy.md"
TASK_FILE = STATE_DIR / "task.md"
NEXT_STEPS_FILE = STATE_DIR / "next_steps.md"
AI_CONTEXT_FILE = PROJECT_ROOT / "AI_CONTEXT.md"

# Project-specific skills and workflows (overlay on top of the framework).
OVERLAY_SKILLS_DIR = STATE_DIR / "skills"
OVERLAY_WORKFLOW_DIR = STATE_DIR / "workflows"

# Optional project-provided scripts referenced by the shared workflows.
OPTIONAL_SCRIPTS = frozenset({"sync_metrics.py"})


def state_and_framework_dirs() -> list[Path]:
    """Return the directories that make up the agentic system (existing only)."""
    return [directory for directory in (FRAMEWORK_DIR, STATE_DIR) if directory.exists()]


def skill_dirs() -> list[Path]:
    """Return every active skill root (framework + project overlay)."""
    return [d for d in (SKILLS_DIR, OVERLAY_SKILLS_DIR) if d.is_dir()]


def scaffold_skill_dirs() -> list[Path]:
    """Return domain-pack skill roots (framework and project scaffolds)."""
    candidates = [
        *sorted(SCAFFOLD_DIR.glob("*/skills")),
        *sorted(PROJECT_SCAFFOLD_DIR.glob("*/skills")),
    ]
    return list(dict.fromkeys(d for d in candidates if d.is_dir()))


def all_skill_dirs() -> list[Path]:
    """Return every skill root, including domain packs."""
    return [*skill_dirs(), *scaffold_skill_dirs()]


def workflow_dirs() -> list[Path]:
    """Return active workflow roots (framework core + project overlay)."""
    return [d for d in (WORKFLOW_DIR, OVERLAY_WORKFLOW_DIR) if d.is_dir()]


def template_workflow_dirs() -> list[Path]:
    """Return domain-pack workflow roots (templates, not active workflows)."""
    candidates = [
        *sorted(SCAFFOLD_DIR.glob("*/workflows")),
        *sorted(PROJECT_SCAFFOLD_DIR.glob("*/workflows")),
    ]
    return list(dict.fromkeys(d for d in candidates if d.is_dir()))


def agent_roots() -> list[Path]:
    """Return the roots used to render agentic paths in reports."""
    return [d for d in (FRAMEWORK_DIR, STATE_DIR) if d.exists()]

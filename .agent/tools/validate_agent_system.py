#!/usr/bin/env python3
"""Agent System Validator.

Validates the integrity of the agentic system: YAML frontmatter, skill and
script references, canonical agent ids, Markdown links, project state files,
the workflow dependency graph (``--graph``), and skill conflicts (``--conflicts``).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import agent_links
import forge_paths
import skill_conflicts
import workflow_graph
from frontmatter import as_list, parse_frontmatter

PROJECT_ROOT = forge_paths.PROJECT_ROOT
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
REQUIRED_SKILL_FIELDS = ("name", "description")
REQUIRED_WORKFLOW_FIELDS = ("description", "agent", "skills")
CANONICAL_AGENTS = {"architect", "qa_engineer", "auditor"}


def valid_agents() -> set[str]:
    """Return canonical agents plus project-defined opencode agents."""
    agents = set(CANONICAL_AGENTS)
    if not forge_paths.OPENCODE_FILE.exists():
        return agents
    try:
        data = json.loads(forge_paths.OPENCODE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return agents
    configured = data.get("agent", {})
    if isinstance(configured, dict):
        agents.update(str(name) for name in configured)
    return agents


@dataclass
class ValidationIssue:
    """A single validation issue found in the agentic system."""

    file: str
    severity: str
    message: str

    def __str__(self) -> str:
        """Format the issue for CLI output."""
        return f"  [{self.severity}] {self.file}: {self.message}"


@dataclass
class SystemReport:
    """Aggregate validation report."""

    issues: list[ValidationIssue] = field(default_factory=list)
    skills_checked: int = 0
    workflows_checked: int = 0

    @property
    def has_errors(self) -> bool:
        """Return True when at least one blocking issue exists."""
        return any(issue.severity == "ERROR" for issue in self.issues)


def _agent_relpath(path: Path) -> str:
    """Render a path relative to the project root."""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _validate_skill_file(
    skill_file: Path, skill_dir: Path
) -> tuple[list[ValidationIssue], str | None]:
    """Validate one SKILL.md and return (issues, declared name)."""
    issues: list[ValidationIssue] = []
    content = skill_file.read_text(encoding="utf-8")
    metadata = parse_frontmatter(content)
    if not metadata:
        issues.append(
            ValidationIssue(
                _agent_relpath(skill_file),
                "ERROR",
                "Missing or invalid YAML frontmatter",
            )
        )
        return issues, None

    name = str(metadata.get("name", ""))
    if name and name != skill_dir.name:
        issues.append(
            ValidationIssue(
                _agent_relpath(skill_file),
                "WARNING",
                f"Skill name '{name}' does not match directory '{skill_dir.name}'",
            )
        )
    for required in REQUIRED_SKILL_FIELDS:
        if not metadata.get(required):
            issues.append(
                ValidationIssue(
                    _agent_relpath(skill_file),
                    "ERROR",
                    f"Missing '{required}' field",
                )
            )
    if len(content) < 100:
        issues.append(
            ValidationIssue(
                _agent_relpath(skill_file),
                "WARNING",
                f"Skill content is very short ({len(content)} chars)",
            )
        )
    return issues, name or None


def validate_skills() -> tuple[list[ValidationIssue], set[str]]:
    """Validate every SKILL.md in the framework, overlay and domain packs."""
    issues: list[ValidationIssue] = []
    available_skills: set[str] = set()

    for skills_root in forge_paths.all_skill_dirs():
        for skill_dir in sorted(skills_root.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                issues.append(
                    ValidationIssue(
                        _agent_relpath(skill_dir),
                        "ERROR",
                        f"Missing SKILL.md in {skill_dir.name}",
                    )
                )
                continue
            file_issues, name = _validate_skill_file(skill_file, skill_dir)
            issues.extend(file_issues)
            if name:
                available_skills.add(name)

    return issues, available_skills


def _validate_script_refs(filepath: Path, content: str, template: bool) -> list[ValidationIssue]:
    """Validate script references unless the workflow is a template."""
    if template:
        return []
    available = {path.name for path in SCRIPTS_DIR.glob("*.py")} if SCRIPTS_DIR.exists() else set()
    available |= set(forge_paths.OPTIONAL_SCRIPTS)
    issues: list[ValidationIssue] = []
    for script in workflow_graph.extract_scripts(content):
        if script not in available:
            issues.append(
                ValidationIssue(
                    _agent_relpath(filepath),
                    "ERROR",
                    f"References unknown script: 'scripts/{script}'",
                )
            )
    return issues


def validate_workflows(available_skills: set[str]) -> list[ValidationIssue]:
    """Validate frontmatter, agent ids and references for active workflows."""
    issues: list[ValidationIssue] = []
    agents = valid_agents()
    seen_names: dict[str, str] = {}

    for filepath in workflow_graph.workflow_files():
        content = filepath.read_text(encoding="utf-8")
        metadata = parse_frontmatter(content)
        rel_path = _agent_relpath(filepath)
        if not metadata:
            issues.append(ValidationIssue(rel_path, "ERROR", "Missing or invalid YAML frontmatter"))
            continue

        name = filepath.stem
        if name in seen_names:
            issues.append(
                ValidationIssue(
                    rel_path,
                    "ERROR",
                    f"Duplicate workflow name '{name}' (also in {seen_names[name]})",
                )
            )
        else:
            seen_names[name] = rel_path

        for required in REQUIRED_WORKFLOW_FIELDS:
            if not metadata.get(required):
                issues.append(ValidationIssue(rel_path, "ERROR", f"Missing '{required}' field"))

        agent = str(metadata.get("agent", ""))
        if agent and agent not in agents:
            severity = "ERROR" if forge_paths.STRICT_AGENT_SYSTEM else "WARNING"
            issues.append(
                ValidationIssue(
                    rel_path,
                    severity,
                    f"Unknown agent '{agent}'; add it to opencode.json or use "
                    f"{sorted(CANONICAL_AGENTS)}",
                )
            )

        for skill in as_list(metadata.get("skills")):
            if skill not in available_skills:
                issues.append(
                    ValidationIssue(
                        rel_path,
                        "ERROR",
                        f"References unknown skill: '{skill}'",
                    )
                )

        issues.extend(
            _validate_script_refs(filepath, content, template=bool(metadata.get("template", False)))
        )

    return issues


def validate_templates(available_skills: set[str]) -> list[ValidationIssue]:
    """Validate domain-pack workflows; project templates are warnings by default."""
    issues: list[ValidationIssue] = []
    agents = valid_agents()
    severity = "ERROR" if forge_paths.STRICT_AGENT_SYSTEM else "WARNING"

    for directory in forge_paths.template_workflow_dirs():
        for filepath in sorted(directory.glob("*.md")):
            if filepath.name == "index.md":
                continue
            metadata = parse_frontmatter(filepath.read_text(encoding="utf-8"))
            rel_path = _agent_relpath(filepath)
            if not metadata:
                issues.append(
                    ValidationIssue(rel_path, severity, "Missing or invalid YAML frontmatter")
                )
                continue
            for required in REQUIRED_WORKFLOW_FIELDS:
                if not metadata.get(required):
                    issues.append(
                        ValidationIssue(rel_path, severity, f"Missing '{required}' field")
                    )
            agent = str(metadata.get("agent", ""))
            if agent and agent not in agents:
                issues.append(
                    ValidationIssue(rel_path, severity, f"Unknown template agent '{agent}'")
                )
            for skill in as_list(metadata.get("skills")):
                if skill not in available_skills:
                    issues.append(
                        ValidationIssue(
                            rel_path,
                            severity,
                            f"References unknown skill: '{skill}'",
                        )
                    )
    return issues


def validate_links() -> list[ValidationIssue]:
    """Validate relative Markdown links across the agentic documentation."""
    severity = "ERROR" if forge_paths.STRICT_AGENT_SYSTEM else "WARNING"
    return [
        ValidationIssue(
            _agent_relpath(issue.file),
            severity,
            f"Broken link '{issue.target}': {issue.reason}",
        )
        for issue in agent_links.check_links()
    ]


def validate_state() -> list[ValidationIssue]:
    """Validate the required project-owned memory and session files."""
    issues: list[ValidationIssue] = []
    severity = "ERROR" if forge_paths.STRICT_AGENT_SYSTEM else "WARNING"
    required = (
        (forge_paths.TASK_FILE, "task.md"),
        (forge_paths.NEXT_STEPS_FILE, "next_steps.md"),
        (forge_paths.METRICS_FILE, "agent_metrics.json"),
        (forge_paths.MEMORY_POLICY_FILE, "memory_policy.md"),
    )
    for path, label in required:
        if not path.exists():
            issues.append(
                ValidationIssue(
                    _agent_relpath(path),
                    severity,
                    f"Missing required state file: '{label}'",
                )
            )

    if not forge_paths.AI_CONTEXT_FILE.exists():
        issues.append(
            ValidationIssue(
                "AI_CONTEXT.md",
                "WARNING",
                "Optional working context file is missing",
            )
        )

    metrics_file = forge_paths.METRICS_FILE
    if metrics_file.exists():
        try:
            data = json.loads(metrics_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(
                ValidationIssue(
                    _agent_relpath(metrics_file),
                    "ERROR",
                    f"Invalid metrics JSON: {exc}",
                )
            )
        else:
            if not data.get("summary", {}).get("test_count"):
                issues.append(
                    ValidationIssue(
                        _agent_relpath(metrics_file),
                        "WARNING",
                        "No summary.test_count in metrics",
                    )
                )
    return issues


def validate_memory_budget() -> list[ValidationIssue]:
    """Enforce the AGENT_LESSONS.md line budget from forge.toml."""
    path = forge_paths.LESSONS_FILE
    if not path.exists():
        return []
    lines = len(path.read_text(encoding="utf-8").splitlines())
    if lines > forge_paths.MAX_LESSON_LINES:
        return [
            ValidationIssue(
                _agent_relpath(path),
                "ERROR",
                f"Lesson log has {lines} lines (limit {forge_paths.MAX_LESSON_LINES}); "
                "run `forge.py memory prune` and consolidate into a SKILL.md",
            )
        ]
    return []


def system_main() -> None:
    """Run the structural validator and exit non-zero on errors."""
    quiet = "--quiet" in sys.argv
    skill_issues, available_skills = validate_skills()
    workflow_issues = validate_workflows(available_skills)
    template_issues = validate_templates(available_skills)
    link_issues = validate_links()
    state_issues = validate_state()
    memory_issues = validate_memory_budget()
    issues = [
        *skill_issues,
        *workflow_issues,
        *template_issues,
        *link_issues,
        *state_issues,
        *memory_issues,
    ]

    skills_checked = sum(
        1
        for root in forge_paths.all_skill_dirs()
        for directory in root.iterdir()
        if (directory / "SKILL.md").is_file()
    )
    workflows_checked = len(workflow_graph.workflow_files())
    templates_checked = sum(
        len([path for path in directory.glob("*.md") if path.name != "index.md"])
        for directory in forge_paths.template_workflow_dirs()
    )

    if not quiet:
        print(
            f"🔍 Validated {skills_checked} skills, {workflows_checked} workflows, "
            f"{templates_checked} templates\n"
        )

    if issues:
        errors = sum(1 for issue in issues if issue.severity == "ERROR")
        warnings = sum(1 for issue in issues if issue.severity == "WARNING")
        for issue in issues:
            print(str(issue))
        print(f"\n❌ {errors} error(s), {warnings} warning(s)")
        sys.exit(1 if errors else 0)

    if not quiet:
        print("✅ All agentic files pass system validation")
    sys.exit(0)


def main() -> None:
    """Dispatch to the requested validation subcommand."""
    argv = sys.argv[1:]
    if "--graph" in argv:
        workflow_graph.graph_main()
    elif "--conflicts" in argv:
        skill_conflicts.conflicts_main()
    else:
        system_main()


if __name__ == "__main__":
    main()

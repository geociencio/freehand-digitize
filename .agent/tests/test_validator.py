"""Tests for the Agentic Forge validators and graph."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import forge_paths
import pytest
import skill_conflicts
import validate_agent_system
import workflow_graph
from frontmatter import as_list, parse_frontmatter


def test_frontmatter_supports_inline_and_block_lists() -> None:
    content = (
        "---\n"
        "description: Example\n"
        "agent: architect\n"
        "skills: [coding-standards, testing-standards]\n"
        "template: true\n"
        "---\n"
        "# Body\n"
    )
    metadata = parse_frontmatter(content)
    assert metadata["agent"] == "architect"
    assert metadata["template"] is True
    assert as_list(metadata["skills"]) == ["coding-standards", "testing-standards"]


def test_all_skill_files_pass_validation() -> None:
    issues, names = validate_agent_system.validate_skills()
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    assert not errors
    assert "coding-standards" in names
    assert "project-context" in names


def test_all_workflows_pass_validation() -> None:
    _issues, names = validate_agent_system.validate_skills()
    issues = validate_agent_system.validate_workflows(names)
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    assert not errors


def test_links_are_valid() -> None:
    issues = validate_agent_system.validate_links()
    assert not issues


def test_state_files_exist() -> None:
    issues = validate_agent_system.validate_state()
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    assert not errors


def test_workflow_graph_has_no_broken_refs() -> None:
    nodes, broken = workflow_graph.scan_workflows()
    assert nodes
    assert not broken
    assert all(node.agent in validate_agent_system.CANONICAL_AGENTS for node in nodes)


def test_scaffold_templates_are_marked() -> None:
    templates = [
        path
        for directory in forge_paths.template_workflow_dirs()
        for path in directory.glob("*.md")
        if path.name != "index.md"
    ]
    assert templates
    assert all(
        parse_frontmatter(path.read_text(encoding="utf-8")).get("template") for path in templates
    )


def test_trigger_duplicates_are_reported() -> None:
    skills = [
        {"name": "a", "description": "A", "trigger": "when testing"},
        {"name": "b", "description": "B", "trigger": "When  testing"},
    ]
    issues = skill_conflicts.find_conflicts(skills)
    assert any("duplicate trigger" in issue for issue in issues)


def test_project_paths_are_resolved() -> None:
    assert forge_paths.FRAMEWORK_DIR.is_dir()
    assert forge_paths.WORKFLOW_DIR.is_dir()
    assert forge_paths.METRICS_FILE.is_file()
    assert forge_paths.MEMORY_POLICY_FILE.is_file()
    assert (forge_paths.FRAMEWORK_DIR / "tools" / "forge.py").is_file()


def test_overlay_workflow_accepts_project_agent(tmp_path, monkeypatch) -> None:
    workflow = tmp_path / "custom.md"
    workflow.write_text(
        "---\n"
        "description: Custom overlay workflow\n"
        "agent: qgis_driver\n"
        "skills: [coding-standards]\n"
        "---\n"
        "# Custom\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(workflow_graph, "workflow_files", lambda: [workflow])
    monkeypatch.setattr(validate_agent_system, "valid_agents", lambda: {"qgis_driver"})

    issues = validate_agent_system.validate_workflows({"coding-standards"})
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    assert not errors


def test_duplicate_workflow_names_are_errors(tmp_path, monkeypatch) -> None:
    first = tmp_path / "one" / "deploy.md"
    second = tmp_path / "two" / "deploy.md"
    for path in (first, second):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\ndescription: Deploy\nagent: architect\nskills: []\n---\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(workflow_graph, "workflow_files", lambda: [first, second])

    issues = validate_agent_system.validate_workflows(set())
    assert any("Duplicate workflow name" in issue.message for issue in issues)


def test_template_validation_is_non_blocking_by_default(tmp_path, monkeypatch) -> None:
    template = tmp_path / "release-plugin.md"
    template.write_text(
        "---\n"
        "description: Template\n"
        "agent: legacy_agent\n"
        "skills: [release-management]\n"
        "---\n"
        "```bash\nscripts/missing.py\n```\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        validate_agent_system.forge_paths, "template_workflow_dirs", lambda: [tmp_path]
    )
    monkeypatch.setattr(validate_agent_system.forge_paths, "STRICT_AGENT_SYSTEM", False)

    issues = validate_agent_system.validate_templates({"release-management"})
    assert issues
    assert all(issue.severity == "WARNING" for issue in issues)


def test_memory_budget_is_enforced(tmp_path, monkeypatch) -> None:
    lessons = tmp_path / "AGENT_LESSONS.md"
    lessons.write_text("\n".join("line" for _ in range(20)), encoding="utf-8")
    monkeypatch.setattr(validate_agent_system.forge_paths, "LESSONS_FILE", lessons)
    monkeypatch.setattr(validate_agent_system.forge_paths, "MAX_LESSON_LINES", 10)

    issues = validate_agent_system.validate_memory_budget()
    assert any(issue.severity == "ERROR" for issue in issues)


def test_quick_reference_workflow_skills_match_frontmatter() -> None:
    """The hand-maintained Quick Reference table must match workflow metadata."""
    content = forge_paths.QUICK_REFERENCE_FILE.read_text(encoding="utf-8")
    rows: dict[str, list[str]] = {}
    for line in content.splitlines():
        match = re.match(
            r"\| \[/([\w-]+)\]\(workflows/[\w-]+\.md\) \| [\w_]+ \| ([^|]+) \|",
            line,
        )
        if match:
            rows[match.group(1)] = [
                item.strip() for item in match.group(2).split(",") if item.strip()
            ]

    for path in sorted(forge_paths.WORKFLOW_DIR.glob("*.md")):
        if path.name == "index.md":
            continue
        frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert rows.get(path.stem) == as_list(frontmatter.get("skills")), path.stem


def test_graph_main_exits_nonzero_on_broken_references(tmp_path: Path, monkeypatch, capsys) -> None:
    workflow = tmp_path / "broken.md"
    workflow.write_text(
        "---\ndescription: Broken\nagent: architect\nskills: [missing]\n---\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(workflow_graph, "workflow_files", lambda: [workflow])
    monkeypatch.setattr(workflow_graph, "get_all_skills", lambda: set())
    monkeypatch.setattr(workflow_graph, "get_all_scripts", lambda: set())
    monkeypatch.setattr(sys, "argv", ["workflow_graph"])

    with pytest.raises(SystemExit) as exc:
        workflow_graph.graph_main()

    assert exc.value.code == 1
    assert "broken references" in capsys.readouterr().out.lower()


def test_core_docs_do_not_reference_project_specific_analyzers() -> None:
    """Generic framework docs must not hardcode one consumer's analyzer or logs."""
    banned = ("qgis_analyzer", "qgis-analyzer", "SecInterp", "docs/source/")
    roots = [
        forge_paths.FRAMEWORK_DIR / "tools",
        forge_paths.FRAMEWORK_DIR / "skills",
        forge_paths.FRAMEWORK_DIR / "workflows",
    ]
    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.suffix not in (".py", ".md"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in banned:
                if marker in text:
                    offenders.append(f"{path}: {marker}")

    assert not offenders, offenders


def test_deprecated_qa_docker_alias_points_to_testing_standards() -> None:
    path = forge_paths.SKILLS_DIR / "qa-docker" / "SKILL.md"
    assert path.is_file()
    content = path.read_text(encoding="utf-8")
    assert "testing-standards" in content
    assert "deprecated" in content.lower()

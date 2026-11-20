#!/usr/bin/env python3
"""Workflow dependency graph and broken-reference validator."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import forge_paths
from frontmatter import as_list, parse_frontmatter

PROJECT_ROOT = forge_paths.PROJECT_ROOT
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
_SCRIPT_RE = re.compile(r"scripts/([\w_]+\.py)")


@dataclass
class WorkflowNode:
    """A workflow and its declared/actual dependencies."""

    name: str
    file: str
    scope: str
    agent: str = ""
    skills: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    template: bool = False


@dataclass
class BrokenRef:
    """A reference to a skill, script or workflow that does not exist."""

    source: str
    source_file: str
    ref_type: str
    ref_name: str

    def __str__(self) -> str:
        """Render the broken reference for CLI output."""
        return f"  {self.source_file} [{self.ref_type}] → '{self.ref_name}' NOT FOUND"


def workflow_files() -> list[Path]:
    """Return every workflow file, including domain packs, excluding indexes."""
    files: list[Path] = []
    for directory in forge_paths.workflow_dirs():
        files.extend(sorted(path for path in directory.glob("*.md") if path.name != "index.md"))
    return list(dict.fromkeys(files))


def _scope(path: Path) -> str:
    """Return a stable scope label for a workflow path."""
    if path.parent == forge_paths.WORKFLOW_DIR:
        return "core"
    try:
        return str(path.parent.parent.relative_to(PROJECT_ROOT))
    except ValueError:
        return path.parent.parent.name


def extract_scripts(content: str) -> list[str]:
    """Extract ``scripts/*.py`` references from Markdown content."""
    return sorted(set(_SCRIPT_RE.findall(content)))


def extract_workflow_refs(content: str) -> list[str]:
    """Extract ``/workflow`` references, excluding filesystem paths."""
    refs = set()
    for match in re.finditer(r"/[\w-]+", content):
        ref = match.group(0).lstrip("/")
        if ref in {"app", "tmp", "usr", "home", "var", "etc"}:
            continue
        refs.add(ref)
    return sorted(refs)


def get_all_skills() -> set[str]:
    """Return every skill directory name, including domain packs."""
    skills: set[str] = set()
    for root in forge_paths.all_skill_dirs():
        for directory in root.iterdir():
            if directory.is_dir() and (directory / "SKILL.md").exists():
                skills.add(directory.name)
    return skills


def get_all_scripts() -> set[str]:
    """Return the project script names available to workflows."""
    if not SCRIPTS_DIR.exists():
        return set()
    return {path.name for path in SCRIPTS_DIR.glob("*.py")}


def _display_path(path: Path) -> str:
    """Return a project-relative path, falling back to the absolute path."""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def scan_workflows() -> tuple[list[WorkflowNode], list[BrokenRef]]:
    """Scan every workflow and validate its skill/script references."""
    nodes: list[WorkflowNode] = []
    broken: list[BrokenRef] = []
    all_skills = get_all_skills()
    all_scripts = get_all_scripts()
    all_workflows = {path.stem for path in workflow_files()}

    for filepath in workflow_files():
        try:
            content = filepath.read_text(encoding="utf-8")
        except OSError:
            continue

        frontmatter = parse_frontmatter(content)
        skills = as_list(frontmatter.get("skills"))
        scripts = extract_scripts(content)
        refs = [ref for ref in extract_workflow_refs(content) if ref in all_workflows]
        node = WorkflowNode(
            name=filepath.stem,
            file=_display_path(filepath),
            scope=_scope(filepath),
            agent=str(frontmatter.get("agent", "")),
            skills=skills,
            scripts=scripts,
            workflows=[ref for ref in refs if ref != filepath.stem],
            template=bool(frontmatter.get("template", False)),
        )
        nodes.append(node)

        for skill in skills:
            if skill not in all_skills:
                broken.append(BrokenRef(node.name, node.file, "skill", skill))
        if not node.template:
            for script in scripts:
                if script not in all_scripts and script not in forge_paths.OPTIONAL_SCRIPTS:
                    broken.append(BrokenRef(node.name, node.file, "script", script))

    return nodes, broken


def print_dependency_matrix(nodes: list[WorkflowNode]) -> None:
    """Print a tabular dependency matrix."""
    print("\n## Workflow → Script Dependencies\n")
    print("| Workflow | Scope | Template | Scripts |")
    print("| :--- | :--- | :--- | :--- |")
    for node in nodes:
        scripts = ", ".join(f"`{s}`" for s in node.scripts) if node.scripts else "—"
        print(f"| `/{node.name}` | {node.scope} | {node.template} | {scripts} |")

    print("\n## Workflow → Skill Dependencies\n")
    print("| Workflow | Agent | Skills |")
    print("| :--- | :--- | :--- |")
    for node in nodes:
        agent = node.agent or "—"
        skills = ", ".join(node.skills) if node.skills else "—"
        print(f"| `/{node.name}` | {agent} | {skills} |")

    print("\n## Workflow → Workflow Dependencies\n")
    print("| Workflow | References |")
    print("| :--- | :--- |")
    for node in nodes:
        refs = ", ".join(f"`/{w}`" for w in node.workflows) if node.workflows else "—"
        print(f"| `/{node.name}` | {refs} |")

    print("\n## Skill Usage Frequency\n")
    skill_count: dict[str, int] = {}
    for node in nodes:
        for skill in node.skills:
            skill_count[skill] = skill_count.get(skill, 0) + 1
    print("| Skill | Used by (workflows) |")
    print("| :--- | :--- |")
    for skill, count in sorted(skill_count.items(), key=lambda item: -item[1]):
        print(f"| `{skill}` | {count} |")


def print_summary(nodes: list[WorkflowNode], broken: list[BrokenRef]) -> None:
    """Print a compact summary of the graph."""
    active_skills = {
        directory.name
        for root in forge_paths.skill_dirs()
        for directory in root.iterdir()
        if directory.is_dir() and (directory / "SKILL.md").is_file()
    }
    all_scripts = get_all_scripts()
    used_skills = {skill for node in nodes for skill in node.skills}
    used_scripts = {script for node in nodes for script in node.scripts}
    unused_skills = active_skills - used_skills
    unused_scripts = all_scripts - used_scripts

    print("\n## Summary")
    print(f"- **Workflows**: {len(nodes)}")
    print(
        f"- **Skills**: {len(active_skills)} ({len(active_skills) - len(unused_skills)} "
        f"referenced, {len(unused_skills)} unreferenced by workflows)"
    )
    if unused_skills:
        print(f"  - Unreferenced by workflows: {', '.join(sorted(unused_skills))}")
    print(
        f"- **Scripts**: {len(all_scripts)} ({len(all_scripts) - len(unused_scripts)} "
        f"referenced, {len(unused_scripts)} unreferenced)"
    )
    if broken:
        print(f"- **Broken references**: {len(broken)}")


def graph_main() -> None:
    """CLI entry point for the workflow dependency graph."""
    json_output = "--json" in sys.argv

    nodes, broken = scan_workflows()

    if json_output:
        output = {
            "workflows": [
                {
                    "name": node.name,
                    "file": node.file,
                    "scope": node.scope,
                    "agent": node.agent,
                    "skills": node.skills,
                    "scripts": node.scripts,
                    "references": node.workflows,
                    "template": node.template,
                }
                for node in nodes
            ],
            "broken_refs": [
                {
                    "source": item.source,
                    "source_file": item.source_file,
                    "ref_type": item.ref_type,
                    "ref_name": item.ref_name,
                }
                for item in broken
            ],
        }
        print(json.dumps(output, indent=2))
        sys.exit(1 if broken else 0)

    print("# Workflow Dependency Graph\n")
    if broken:
        print("## ❌ Broken References\n")
        for item in broken:
            print(str(item))

    print_dependency_matrix(nodes)
    print_summary(nodes, broken)

    if broken:
        print("\n❌ Validation FAILED: broken references found.")
        sys.exit(1)
    print("\n✅ Validation PASSED: all references valid.")
    sys.exit(0)


if __name__ == "__main__":
    graph_main()

# Agentic Forge — Quick Reference

**Version**: 1.4.2 (genericized core; QGIS moved to `scaffold/qgis`)
**Requirements**: Python >= 3.9 (`tomli` on < 3.11) and PyYAML.

---

## 📋 Executive Summary

Agentic Forge is a **runtime-agnostic** agentic development framework. The core ships
**8 active skills** (plus one deprecated alias) and **14 workflows**; a project may add its own skills as an **overlay**
under `.agent-state/skills/` without touching the framework.

Domain packs (skills + workflows for a specific technology) live under
`scaffold/<domain>/` (e.g. `scaffold/qgis/`) and are **not** part of the core set.

---

## 🛠️ Core Skills (8 active + 1 deprecated alias)

Paths are relative to this file (framework root).

| Skill | Description | When to Use |
|:------|:------------|:------------|
| [agentic-memory](skills/agentic-memory/SKILL.md) | Lessons and patterns management | Extracting meta-lessons, preferences |
| [changelog-generator](skills/changelog-generator/SKILL.md) | User-facing changelogs from git commits | Writing release notes, CHANGELOG updates |
| [coding-standards](skills/coding-standards/SKILL.md) | Project coding standards | Writing Python code, refactoring |
| [commit-standards](skills/commit-standards/SKILL.md) | Conventional Commits standards | Creating commits, validating messages |
| [documentation-standards](skills/documentation-standards/SKILL.md) | Logs and project history standards | Updating development/maintenance logs |
| [i18n-standards](skills/i18n-standards/SKILL.md) | Internationalization standards | Adding translations, UI strings |
| [release-management](skills/release-management/SKILL.md) | Python package release process | Preparing releases, versioning |
| [testing-standards](skills/testing-standards/SKILL.md) | Automated testing, CI/CD, mocks | Designing testing strategies |
| [qa-docker](skills/qa-docker/SKILL.md) | **Deprecated alias** for `testing-standards` | Update references to `testing-standards` |

> Domain skills (QGIS API, UI framework, migration) live under `scaffold/qgis/skills/`.
> The reference project adds `project-context` and `geological-logic` in its overlay.

---

## 🔄 Workflows (14)

### Daily Development

| Workflow | Agent | Skills | Purpose |
|:---------|:------|:-------|:----------|
| [/start-session](workflows/start-session.md) | architect | coding-standards, testing-standards, agentic-memory | Start session with semantic skill injection |
| [/create-commit](workflows/create-commit.md) | qa_engineer | testing-standards, commit-standards, agentic-memory | Commit with quality validation |
| [/run-tests](workflows/run-tests.md) | qa_engineer | testing-standards | Run tests with intelligent interpretation |
| [/close-session](workflows/close-session.md) | qa_engineer | testing-standards, commit-standards, agentic-memory, documentation-standards, changelog-generator | Close session with auto-metrics and pruning |

### Refactoring and Quality

| Workflow | Agent | Skills | Purpose |
|:---------|:------|:-------|:----------|
| [/refactor-code](workflows/refactor-code.md) | architect | coding-standards, testing-standards | Refactor code with complexity validation |
| [/audit-package](workflows/audit-package.md) | auditor | coding-standards, testing-standards | Self-audit of the project's code |
| [/fix-linting](workflows/fix-linting.md) | qa_engineer | coding-standards, testing-standards | Automatically fix style issues |

### Features and i18n

| Workflow | Agent | Skills | Purpose |
|:---------|:------|:-------|:----------|
| [/build-feature](workflows/build-feature.md) | architect | coding-standards, testing-standards | Autonomous pipeline for new features |
| [/i18n-maintenance](workflows/i18n-maintenance.md) | qa_engineer | i18n-standards | Add or update translations |

### Release and Planning

| Workflow | Agent | Skills | Purpose |
|:---------|:------|:-------|:----------|
| [/release-package](workflows/release-package.md) | qa_engineer | release-management, testing-standards, commit-standards | Full package release process |
| [/start-phase](workflows/start-phase.md) | architect | coding-standards, testing-standards | Start major phase with planning |
| [/close-phase](workflows/close-phase.md) | architect | coding-standards, testing-standards, changelog-generator | Close phase with metrics and retro |
| [/ia-critic](workflows/ia-critic.md) | auditor | coding-standards, agentic-memory | Implementation plan audit |
| [/verify-standards](workflows/verify-standards.md) | architect | coding-standards, commit-standards, documentation-standards | Audit agent system consistency |

---

## ⚡ Tooling

The framework ships generic agentic tooling behind a single CLI, `.agent/tools/forge.py`
(paths resolve from `forge.toml`). Project-specific collectors stay in the project
(the project's `scripts/sync_metrics.py`):

| Tool | Purpose | Command |
|:-----|:--------|:--------|
| **System Validator** | Validate framework structure + overlay | `python .agent/tools/forge.py validate` |
| **Workflow Graph** | Dependency graph & broken-reference validator | `python .agent/tools/forge.py validate --graph` |
| **Skill Conflicts** | Cross-skill overlap detection | `python .agent/tools/forge.py validate --conflicts` |
| **Metric Validator** | Cross-file consistency check | `python .agent/tools/forge.py metrics validate` |
| **Metrics Report** | Markdown trend report | `python .agent/tools/forge.py metrics report` |
| **Session Close** | Rotate `last_session` | `python .agent/tools/forge.py metrics close-session --topic NAME` |
| **Project Commands** | Run `[project]` commands from `forge.toml` | `python .agent/tools/forge.py project <test\|test-full\|lint\|format\|type\|bump>` |
| **Memory Pruning** | Dry-run; add `--apply` to prune | `python .agent/tools/forge.py memory prune [--apply]` |
| **Memory Check** | Enforce the lesson line budget | `python .agent/tools/forge.py memory check` |
| **Lesson Extractor** | Propose `AGENT_LESSONS` candidates | `python .agent/tools/forge.py lesson propose` |
| **Metrics Sync** | Project ground-truth collection | `uv run python scripts/sync_metrics.py` |

---

## 📊 Quality Gates (generic)

The framework enforces these gates; **project values** live in
`.agent-state/memory/agent_metrics.json`:

- **Cyclomatic complexity** at or below the project limit
- **Docstrings** on public APIs + strict type hints
- **Mock-first** unit tests (no live service required)
- **i18n hygiene** (no untranslated user-facing strings)
- **Module size** limit
- **Security** scan

---

## 📚 References

- [README.md](README.md) — framework overview
- [AGENTS.md](AGENTS.md) — default agent config (roles, skills, workflows); a project may override it at its repo root
- [workflows/index.md](workflows/index.md) — workflow quick reference
- [scaffold/qgis/](scaffold/qgis/) — QGIS domain pack (skills + workflows)

> Project-specific state (memory, task board, `next_steps.md`, metrics) lives in
> `.agent-state/`, never in the framework.

---

**System Version**: 1.4.2 (genericized core; tests, CI and configurable project commands)

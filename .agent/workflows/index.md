# Workflow Quick Reference

> Maps each `workflows/*.md` to concrete actions.
> For humans: "I want to run X, what do I tell the agent?"
> For agents: "User said /X, what do I actually do?"

---

## Daily Development

### `/start-session`
**Tell the agent**: "Run /start-session"
**What happens**:
```
git submodule update --init --recursive
if [ -f scripts/sync_metrics.py ]; then uv run python scripts/sync_metrics.py; fi
uv run python .agent/tools/forge.py metrics validate
cat .agent-state/next_steps.md
cat .agent-state/task.md
uv sync
```
**Expected output**: Updated metrics, visible active tasks, dependencies OK.

### `/close-session`
**Tell the agent**: "Run /close-session with topic [name]"
**What happens**:
```
if [ -f scripts/sync_metrics.py ]; then uv run python scripts/sync_metrics.py; fi
uv run python .agent/tools/forge.py metrics close-session --topic [name]
# Update AGENT_LESSONS.md with 3 lessons
uv run python .agent/tools/forge.py memory prune   # dry-run; --apply to delete
uv run python .agent/tools/forge.py metrics report
# Update next_steps.md
git add . && git commit -m "chore(docs): close session [topic]"
```

### `/create-commit`
**Tell the agent**: "Run /create-commit with message [msg]"
**What happens**:
```
uv run python .agent/tools/forge.py project format
uv run python .agent/tools/forge.py project lint
git add . && git commit -m "[msg]"
```

### `/run-tests`
**Tell the agent**: "Run /run-tests"
**What happens**: `forge.py project test-full` plus `uv run pytest .agent/tests -q`

---

## Refactoring & Quality

### `/refactor-code`
**Tell the agent**: "Run /refactor-code on [file/module]"
**What happens**: Reads coding-standards, applies changes, validates complexity, runs lint.

### `/audit-package`
**Tell the agent**: "Run /audit-package"
**What happens**: project's self-analysis command → review the summary report

### `/fix-linting`
**Tell the agent**: "Run /fix-linting"
**What happens**: `ruff check --fix . && ruff format .`

---

## Features & i18n

### `/build-feature`
**Tell the agent**: "Run /build-feature [description]"
**What happens**: Reads the project's domain skills → implement → /ia-critic review → /create-commit

### `/i18n-maintenance`
**Tell the agent**: "Run /i18n-maintenance [language]"
**What happens**: Reads i18n-standards skill → edit translation map/catalog → run analyzer

### `/ia-critic`
**Tell the agent**: "Run /ia-critic on [plan]"
**What happens**: Reads AGENT_LESSONS.md → contrast against the project architecture → issue verdict

---

## Release & Planning

### `/release-package`
**Tell the agent**: "Run /release-package"
**What happens**: `project test-full/lint/type` → bump → build → `twine check` → tag → CI publication

### `/start-phase`
**Tell the agent**: "Run /start-phase [name]"
**What happens**: Reads next_steps.md → create plan → /ia-critic → start implementation

### `/close-phase`
**Tell the agent**: "Run /close-phase [name]"
**What happens**: Creates `docs/maintenance/phase_closure_[name].md` → update DEVELOPMENT_LOG.md → sync metrics

### `/verify-standards`
**Tell the agent**: "Run /verify-standards"
**What happens**:
```
uv run python .agent/tools/forge.py validate
uv run python .agent/tools/forge.py validate --graph
```

---

## Quality Gate Commands (Direct)

| Action | Command |
|--------|---------|
| Agent system validation | `uv run python .agent/tools/forge.py validate` |
| Workflow graph validation | `uv run python .agent/tools/forge.py validate --graph` |
| Skill conflict detection | `uv run python .agent/tools/forge.py validate --conflicts` |
| Metric consistency | `uv run python .agent/tools/forge.py metrics validate` |
| Metrics report | `uv run python .agent/tools/forge.py metrics report` |
| Memory prune | `uv run python .agent/tools/forge.py memory prune` |
| Lesson extraction | `uv run python .agent/tools/forge.py lesson propose` |

> QGIS-specific workflows (`/release-plugin`, `/audit-plugin`, `/run-tests-in-qgis`)
> are documented under `scaffold/qgis/workflows/`.

---

## Quick Reference Card

```
Start session:             /start-session
Close session:             /close-session [topic]
Commit with quality:       /create-commit [message]
Tests:                     /run-tests

Safe refactor:             /refactor-code [file]
Self audit:                /audit-package
Automatic linting:         /fix-linting

New feature:               /build-feature [desc]
Translations:              /i18n-maintenance [lang]
Plan review:               /ia-critic

Release:                   /release-package
Start phase:               /start-phase [name]
Close phase:               /close-phase [name]
Verify standards:          /verify-standards
```

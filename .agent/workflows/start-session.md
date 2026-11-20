---
description: Standard and robust procedure for starting a "Local First" development session
agent: architect
skills: [coding-standards, testing-standards, agentic-memory]
validation: |
  - Verify that all tests pass
  - Confirm that AI_CONTEXT.md is updated with recent metrics
  - Validate that there are no regressions in cyclomatic complexity
---

# Workflow: Start Session

This workflow optimizes the start of development by ensuring a synchronized,
**contextualized**, and validated environment using semantic context injection.

### 0. Framework Submodule
Ensure the `agentic-forge` framework submodule is present before reading anything else.
// turbo
```bash
git submodule update --init --recursive
```

### 0b. Skill Discovery
Identify the skills relevant to the active tasks from the root `AGENTS.md` "Agent Skills" table.
// turbo
```bash
cat AGENTS.md
```

🤖 **Agent Action**: Read only the matching `SKILL.md` files on demand; do not pre-load every skill (avoids token bloat).

### 1. Context Tuning (CRITICAL)
Updates and reads the context to understand "where we left off".
// turbo
```bash
cat .agent-state/next_steps.md && cat .agent-state/memory/AGENT_LESSONS.md
```

🤖 **Agent Action**: Validate Active Tasks.

*   **Task Management**:
    *   Verify if `.agent-state/task.md` exists.
    *   If it exists: Show the content ("Current Status").
    *   If it DOES NOT exist: Create it based on the active Implementation Plan or `next_steps.md`.

Review the following files in this order:
*   `.agent-state/next_steps.md`: **The Witness (Source of Truth)**. Defines the exact starting point and immediate goals.
*   `.agent-state/task.md`: **Active Board**. If it exists, it must align with `next_steps.md`. If not, create it based on `next_steps.md`.
*   `.agent-state/memory/AGENT_LESSONS.md`: **The Brain**. Error patterns to avoid and preferences.
*   `AI_CONTEXT.md`: Architectural context and long-term metrics.
*   `docs/DEVELOPMENT_LOG.md`: See summary of the last session (reverse chronological order).

### 1.5 Metric Coherence Validation (CRITICAL)
Before starting work, verify that all `.agent/` documentation files are consistent with ground-truth metrics. This catches stale references (test counts, quality scores, complexity thresholds) that may have drifted between sessions.

// turbo
```bash
if [ -f scripts/sync_metrics.py ]; then
  uv run python scripts/sync_metrics.py
fi
uv run python .agent/tools/forge.py metrics validate
```

🤖 **Agent Action**: If the validator reports inconsistencies, fix them before proceeding. Stale metrics in documentation lead to incorrect decisions.

### 2. Quick Quality Scan
Perform a quick scan of the project status to identify critical technical debt.
```bash
uv run python .agent/tools/forge.py project lint
```

### 3. Integrity Validation (Dependencies)
Ensure updated dependencies.
// turbo
```bash
uv sync
```

🤖 **Agent Action**: Verify that there are no dependency conflicts.

### 4. Status Verification (Sanity Check)
Confirm that the system is stable ("in green"). All tests must pass.

```bash
# Runs [project].test_command_full (or test_command) from forge.toml.
uv run python .agent/tools/forge.py project test-full
```

🤖 **Agent Action**: Use the **testing-standards** skill to interpret failures and identify regressions.

## Expected Result
- Synchronized and validated environment (All tests OK).
- Clear mental map of pending tasks in `next_steps.md`.
- Agent operating with the correct profiles and skills loaded.

## Structured Session Status
🤖 **Agent Action**: Conclude the initialization with a YAML block showing current metrics AND the delta from the previous session:
```yaml
session_init: success
context_sync: complete
active_task: [task_name]
current_metrics:
  tests: N
  quality_score: X
  cc_gate: PASS|FAIL
  i18n_gate: PASS|FAIL
delta_from_last:
  quality_score: +X.X
  tests: +N | -N | =
  issues: +N | -N | =
```

🤖 **Agent Action**: To compute the delta, compare `agent_metrics.json` → `last_session` values against the current metric output. If the delta shows a regression (negative quality, new complexity failures), flag it immediately.

**Philosophy**: Start coding knowing *exactly* what happened yesterday and with specialized context loaded.

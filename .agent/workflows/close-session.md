---
description: Procedure to end a work session, update logs, and archive results
agent: qa_engineer
skills: [testing-standards, commit-standards, agentic-memory, documentation-standards, changelog-generator]
stop_conditions:
  - "Tests fail during final verification → report failures, do NOT commit, escalate to user"
  - "Pre-commit hook fails 3+ times on same file → skip that file, report issue"
  - "AI_CONTEXT.md or next_steps.md cannot be generated → document manually and continue"
validation: |
  - Verify that all logs are updated
  - Confirm that tests pass before closing
  - Validate that .agent-state/next_steps.md exists and has clear content
---

# Workflow: Close Session

This workflow closes the development cycle, converting technical work into historical memory for the next session.

### 1. Memory Update (Logs & Roadmap)

🤖 **Agent Action**: Validate that all critical files are updated.

*   **Session Topic**: Define a short name for the session (e.g., `stabilization_mocks`).
*   **Active Implementation Plan**: Update task status in the current plan.
*   **Task Persistence**:
    *   Ensure `.agent-state/task.md` reflects actual progress.
    *   If a major phase was completed, archive it in `.agent-state/history/tasks/`.
    *   **DO NOT DELETE** this file if the phase continues.
*   **`.agent-state/next_steps.md`**: **[CRITICAL]** Create or update this file with the "handover": what's missing, what errors are pending, and what command to resume.
*   **Next Steps Archiving**: Copy `.agent-state/next_steps.md` to `.agent-state/history/next_steps/next_steps_YYYY-MM-DD.md` to maintain a historical record.
*   **`docs/maintenance/session_YYYY-MM-DD_[TOPIC].md`**: **[MANDATORY]** Create this file with the session's technical summary.
*   **`docs/DEVELOPMENT_LOG.md`**: **[CRITICAL]** Add entry following the `documentation-standards` format.
*   **`docs/CHANGELOG.md`**: Record user-visible changes in `[Unreleased]` using the **changelog-generator** skill based on session commits. **(NOTE: The `changelog-generator` skill is interpretive [prompt-based]. Do NOT attempt to run any Python script. Instead, use `git log` to read recent session commits, analyze them mentally, and use the file editing tool to write directly into CHANGELOG.md)**.

### 2. Final Verification (Safety Net)

🤖 **Agent Action**: Use **testing-standards** skill to validate stability before closing.

Run formatter, linter, and tests to ensure quality.
```bash
uv run python .agent/tools/forge.py project lint
uv run python .agent/tools/forge.py project format
```

```bash
# Project test command from forge.toml + framework tooling tests.
uv run python .agent/tools/forge.py project test-full
uv run pytest .agent/tests -q
```

🤖 **Agent Action**: Verify that tests pass. Alert if there are failures.

🤖 **Agent Action**: Validate Active Tasks.
Verify that `.agent-state/task.md` exists and is updated before committing.

### 3. Final Memory Synchronization (AI)

🚀 **Agent Action (Lesson Extraction — Gen 7)**: Run the structured lesson extraction protocol:

1. **Scan for candidates** — check these signals:
   - Error patterns: bugs that took 3+ attempts
   - Implicit preferences: user repeatedly approved a style
   - Technical hotspots: code areas difficult to test
   - New tooling: surprising script/command behavior
   - Metric changes: any score moved > 5 points

2. **Draft 2-3 lessons** in YAML:
   ```yaml
   - date: YYYY-MM-DD
     category: [TECHNICAL|ARCHITECTURE|TESTING|TOOLING|i18n|ENVIRONMENT|AGENTIC_SYSTEM]
     topic: short description
     lesson: What happened and why. Under 3 sentences.
     action: Concrete action for future sessions.
   ```

3. **Insert** into `.agent-state/memory/AGENT_LESSONS.md` at top of ACTIVE LESSONS.

4. **Skip if**: duplicates an existing lesson, already in a SKILL.md, or one-time throwaway.

🤖 **Agent Action (Metrics Sync — CRITICAL)**: Run the unified metric extraction before closing.
```bash
if [ -f scripts/sync_metrics.py ]; then
  uv run python scripts/sync_metrics.py
fi
uv run python .agent/tools/forge.py metrics close-session --topic [TOPIC]
```
This rotates `last_session` into `history` (preventing stale session records).
`scripts/sync_metrics.py` is the project collector and is run above; it refreshes
`agent_metrics.json` with live tests/coverage/lint results. Replace `[TOPIC]` with the
short session name defined in step 1.

🤖 **Agent Action (Metric Validation — CRITICAL)**: Verify that all `.agent/` documentation files are consistent with the ground truth.
```bash
uv run python .agent/tools/forge.py metrics validate
```
This scans all `.agent/` files for stale metric references (test counts, quality scores,
complexity thresholds) and reports any drift from `agent_metrics.json`. Fix any reported
inconsistencies before proceeding.

*   Run `uv run python .agent/tools/forge.py memory prune` (dry-run) and add `--apply` only after reviewing the proposed deletions.
*   Run `uv run python .agent/tools/forge.py lesson propose` to generate candidate lessons from the session diff.
*   Generate metrics report: `uv run python .agent/tools/forge.py metrics report`.

🤖 **Agent Action**: Update AI_CONTEXT.md and validate that next_steps.md is clear.
Ensure the AI "Brain" is up to date with the final changes.
// turbo
```bash
cat .agent-state/next_steps.md
```

### 4. Local Commit

🤖 **Agent Action**: Use **commit-standards** skill to generate an appropriate message.

Save your progress.
```bash
git add .
git commit -m "chore(docs): close session [TOPIC]"
```

**Recommended Format**: `chore(docs): close session [descriptive_topic]`

*If the pre-commit hook persists in failing:*
1. Review the detected error messages.
2. Run `git add` again if there were automatic changes.
3. Repeat the commit.

### 5. Summary for the User

🤖 **Agent Action**: Generate a structured session summary.

Generate a final message listing:
*   Updated log files.
*   Test status (e.g., N tests OK).
*   Content of `.agent-state/next_steps.md`.
*   Suggestion for the next session (command `/start-session`).

## Expected Result
- Session memory persisted in Logs and `next_steps.md`.
- Repository clean and technically validated.
- Clear instructions for the assistant to resume the task without context loss.

**Philosophy**: A session doesn't end when the code works, but when the story is told.

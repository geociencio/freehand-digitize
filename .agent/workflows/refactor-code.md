---
description: Guided workflow for code refactoring with complexity validation
agent: architect
skills: [coding-standards, testing-standards]
validation: |
  - Verify that cyclomatic complexity decreased (at or below the project limit)
  - Confirm that tests still pass after refactoring
  - Validate that no architecture violations were introduced
---

# Workflow: Refactor Code

This workflow guides code refactoring following project standards and using specialized knowledge from skills.

## When to Use This Workflow

- When the project's analyzer detects methods above the complexity limit.
- When `AI_CONTEXT.md` identifies critical technical debt.
- Before adding new features to complex modules.

## Refactoring Steps

1. **Identify Refactoring Target**:
   // turbo
   ```bash
   # project's static analysis / summary command
   ```

   🤖 **Agent Action**: Analyze the summary report to identify hotspots (methods above the complexity limit) and technical debt.

2. **Quick Auto-Correction** (Optional):
   // turbo
   ```bash
   # auto-correct command (e.g. `ruff check --fix .` or a custom `--fix` flag)
   ```
   🤖 **Agent Action**: If safe auto-corrections are available, apply them before proceeding with manual refactoring.
   Verify improvement with the project's analyzer.

3. **Load Specialized Context**:

   🤖 **Agent Action**: Identify relevant skills from the root `AGENTS.md` "Agent Skills" table and read the matching `SKILL.md` files on demand.

4. **Apply Refactoring**:

   🤖 **Agent Action**: Apply SOLID principles and reduce cyclomatic complexity.

5. **Validate with Tests**:
   // turbo
   ```bash
   # project's test command (local + containerized)
   ```

   🤖 **Agent Action**: Use **testing-standards** skill to ensure no regressions.

6. **Verify Quality Metrics**:
   // turbo
   ```bash
   # project's static analysis command
   ```

   🤖 **Agent Action**: Confirm improvement in the quality score and reduction in cyclomatic complexity.

6.5 Complexity Audit (Auditor Reflection) 🤖
- **Agent Reflection**: Activate the **@auditor** role.
- **Verification**: Ensure the refactor didn't introduce new architecture violations or hide complexity in "wrapper" functions.
- **Pattern Match**: Confirm adherence to the project's architectural standard.

7. **Refactoring Commit**:
   Use `/create-commit` workflow with a structured technical message.

## Expected Result
- More maintainable, testable code with reduced cyclomatic complexity (at or below the project limit).
- Zero functional regressions confirmed by tests.
- Technical documentation (docstrings) updated.

**Philosophy**: Refactor for clarity first, then for speed. Always validate complexity.

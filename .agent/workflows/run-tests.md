---
description: Run the project test suite reliably through forge.toml commands
agent: qa_engineer
skills: [testing-standards]
validation:
  - Verify that all tests pass
  - Confirm that coverage or the project's quality threshold is met
  - Confirm the framework tooling tests pass
---

# Workflow: Run Tests

The shared workflow delegates to the commands declared in `forge.toml`
(`[project].test_command` and `test_command_full`). This keeps pytest,
unittest, and other runners working across projects.

### 1. Fast Tests

```bash
uv run python .agent/tools/forge.py project test
```

### 2. Full Gate

```bash
uv run python .agent/tools/forge.py project test-full
```

### 3. Framework Tooling Tests

```bash
uv run pytest .agent/tests -q
```

### 4. Static Gates

```bash
uv run python .agent/tools/forge.py project lint
uv run python .agent/tools/forge.py project format
uv run python .agent/tools/forge.py project type
```

If a project has not declared a command yet, run its primary runner directly
(for example `uv run pytest -q` or
`PYTHONPATH=.. uv run python3 -m unittest discover tests`).

### 5. Optional Integration Tests

Run integration tests in a separate process when the project provides them.

🤖 **Agent Action**: Use the **testing-standards** skill to interpret failures
and validate the mocking strategy.

## Expected Result

- Clear report of the project's stability status.
- Identification of regressions or mock failures.
- Confirmation of whether the code is safe to integrate.

## Structured Result Summary

```yaml
test_run: complete
total_tests: N
passed: X
failed: Y
errors: Z
coverage_percent: N
stability_score: 0-100
```

---
description: Unified process for releasing a Python package (PyPI + Git tag).
agent: qa_engineer
skills: [release-management, testing-standards, commit-standards]
validation:
  - Tests passing (Green)
  - Version consistent across the project files
  - Build generated without errors (twine check OK)
  - Version verified via the project CLI
---

# Workflow: Release Package

Release workflow for a Python package. Commands come from `forge.toml`
(`[project].test_command_full`, `lint_command`, `format_command`,
`type_command`, `version_bump_command`) so the workflow works across projects.

### 1. Preparation

```bash
uv sync
uv run python .agent/tools/forge.py project test-full
uv run python .agent/tools/forge.py project lint
uv run python .agent/tools/forge.py project format
uv run python .agent/tools/forge.py project type
uv run python .agent/tools/forge.py validate
```

Confirm zero blocking findings before continuing.

### 2. Version and Documentation

- Bump the version with the configured command when available:

  ```bash
  uv run python .agent/tools/forge.py project bump
  ```

  Otherwise edit the version in the project's canonical file(s) manually.

- Update `CHANGELOG.md` (use the `changelog-generator` skill).
- Create release notes (for example `docs/releases/notes/v[VERSION].md`).
- Update README badges and the development log.
- Refresh metrics if the project has a collector:

  ```bash
  if [ -f scripts/sync_metrics.py ]; then
    uv run python scripts/sync_metrics.py
  fi
  uv run python .agent/tools/forge.py metrics validate
  ```

### 3. Build Verification

```bash
rm -rf dist/
uv build
uvx twine check dist/*
```

Verify the version with the project's CLI if it has one.

### 4. Commit, Tag and Push

```bash
git add <release files>
git commit -m "chore(release): prepare v[VERSION]"
git tag -a "v[VERSION]" -m "Release v[VERSION]"
git push origin main
git push origin "v[VERSION]"
```

### 5. Publication

Use the project's release pipeline. If it uses the standard tag-driven flow,
pushing the tag creates a draft GitHub Release and publishing that release
triggers the PyPI job. Do **not** upload to PyPI or create the release manually
when CI owns the process.

### 6. Post-Release Verification

Confirm the published version and release notes are visible.

## Expected Result

- Version consistent across the project files and the tag.
- Green quality gates and a clean `dist/` build.
- Release published through the project's pipeline.
- Release notes and changelog updated.

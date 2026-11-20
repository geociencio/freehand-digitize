---
name: release-management
description: Standards for the Python package release process with quality validation. Use when preparing releases, updating versions, or using the /release-package workflow.
---

# Release Management (Package)

Controls the version lifecycle of a Python package, ensuring that each delivery to
PyPI/GitHub meets the project's quality standards.

## When to use this skill
- When finishing a development phase and preparing a new version.
- When updating `pyproject.toml` for a new release.
- When generating release notes or updating the changelog.
- When using the `/release-package` workflow.

## Degree of Freedom
- **Strict**: The phase order, Semantic Versioning rules, and quality gates are
  non-negotiable.

## Detailed Workflow

### Phase 1: Quality and Preparation
1. **Quality Analysis**: run the project's static analysis and security scans.
   Validate: quality score above the project threshold, zero high-severity security
   issues, no critical violations (CC above the project limit).
2. **Linting & Type Checking**: run the project's linter/formatter and type checker.
3. **Update Badges**: reflect the latest metrics in `README.md`.

### Phase 2: Versioning and Documentation
1. **Synchronization**: update `version` in `pyproject.toml`.
2. **Changelog**: move `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` following
   [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
3. **Semantic Versioning ([SemVer](https://semver.org/spec/v2.0.0.html))**:
   - MAJOR (X): breaking changes.
   - MINOR (Y): backward-compatible new features.
   - PATCH (Z): backward-compatible bug fixes.
4. **Release Notes**: create `docs/releases/notes/vX.Y.Z.md`.

### Phase 3: Technical Verification
1. Run the full test suite.
2. Run the isolated/containerized environment check (if the project uses one).

### Phase 4: Git and Tagging
1. Release commit: `chore(release): prepare vX.Y.Z`.
2. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
3. Push: `git push origin main --tags`.

### Phase 5: Packaging and Distribution
1. Clean: `rm -rf dist/ build/`.
2. Build: `python -m build`.
3. Validate: `twine check dist/*`.
4. Upload: publish to PyPI and create a GitHub release with the artifacts.

## Instructions and Rules

### Critical Files
- **pyproject.toml**: the `version` field must be updated and match the release tag.

### Release Notes Template
```markdown
# Release vX.Y.Z - [Title]
Highlights:
- **feat**: ...
- **fix**: ...
```

## Quality Checklist
- [ ] Is the quality score above the project threshold?
- [ ] Have all version references been updated?
- [ ] Has the built artifact been validated (`twine check`)?
- [ ] Have Git tagging rules been followed?
- [ ] Did the full test suite pass?

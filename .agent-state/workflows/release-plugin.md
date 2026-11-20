---
description: Release Freehand Digitize to plugins.qgis.org (version bump, gates, ZIP, validation and upload).
agent: qa_engineer
skills: [release-management, qgis-release, qgis-migration-4x, testing-standards, commit-standards, changelog-generator]
stop_conditions:
  - "Any function exceeds CC > 10 → block and refactor"
  - "Any blocking gate fails (ruff, flake8, mypy, analyzer, tests, agent validate, qgis-manage) → block and fix"
  - "make security-scan reports a CRITICAL finding → block before packaging"
  - "Forbidden files (.agent, .agent-state, tests, docs, freehandEditing) found in the ZIP → abort and fix .qgisignore"
  - "The ZIP version is not numeric/unique or metadata.txt and pyproject.toml disagree → abort"
validation: |
  - make pre-release passes
  - make zip and make portal-check pass
  - make security-scan and make qt6-check pass (Docker)
  - dist/freehand_digitize.X.Y.Z.zip contains only the plugin runtime + metadata + icon + LICENSE + README
---

# Workflow: Release Plugin

Five-phase release for Freehand Digitize. The plugin has no runtime Python
dependencies and ships compiled English translation catalogs (`i18n/*.qm`).

## Phase 1 — Quality and preparation

```bash
make sync
make pre-release        # format, lint, flake8, mypy, analyzer, agent validate, tests, qgis validate
make security-scan      # no CRITICAL finding
make qt6-check          # no Qt6/PyQt6 enum error (Docker)
```

Block the release on any failure. Review `analysis_results/` for CC, docstrings
and module size.

## Phase 2 — Version and documentation

Update, in this order, and keep them consistent:

| File | What to change |
| :--- | :--- |
| `metadata.txt` | `version=X.Y.Z` and a `changelog` entry |
| `pyproject.toml` | `version = "X.Y.Z"` |
| `CHANGELOG.md` | new `## X.Y.Z — YYYY-MM-DD` section |
| `AI_CONTEXT.md` | current release and date |
| `.agent-state/task.md` | close the release tasks |
| `.agent-state/next_steps.md` | handoff for the next session |
| `README.md` | only if features or requirements changed |

Use the `changelog-generator` skill to turn commits into user-facing notes. Do
not invent metrics; record the actual test count and analyzer scores in
`.agent-state/memory/agent_metrics.json`.

## Phase 3 — Final verification

```bash
make test
make test-qgis
make zip                # package --repo-check + validate --zip
make portal-check
```

`make zip` must produce `dist/freehand_digitize.X.Y.Z.zip` with:

- one `freehand_digitize/` root folder;
- `metadata.txt`, `__init__.py`, `LICENSE`, `icon.png`, the plugin code and
  `i18n/freehand_digitize_en.qm`;
- no `tests/`, `docs/`, `.agent`, `.agent-state`, `.ai-context`,
  `freehandEditing/`, caches, `uv.lock` or `i18n/*.ts` (ship `.qm`, not `.ts`).

Audit the artifact:

```bash
unzip -l dist/freehand_digitize.X.Y.Z.zip
unzip -l dist/freehand_digitize.X.Y.Z.zip | grep -E "\.agent|tests|docs|freehandEditing|uv.lock"
```

The second command must print nothing.

## Phase 4 — Commit and tag

```bash
git add .
git commit -m "chore(release): prepare vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main && git push origin vX.Y.Z
```

## Phase 5 — Publish

1. Upload `dist/freehand_digitize.X.Y.Z.zip` at
   <https://plugins.qgis.org/plugins/> (manual).
2. Wait for the validation email: `Validating` → `Validated` /
   `Validated (configured)` / `Blocked`.
3. A `Blocked` status means a CRITICAL Bandit/detect-secrets finding. Fix it and
   upload a **new** version; never reuse the version string.
4. Create the GitHub release with the ZIP attached (draft first if the portal is
   still validating).
5. Run `uv run python .agent/tools/forge.py memory prune --apply` and update the
   session history.

## Expected result

- A published, portal-validated ZIP with no development files.
- Updated `metadata.txt`, `pyproject.toml`, `CHANGELOG.md`, state and metrics.
- No quality-gate regression.

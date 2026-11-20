# Changelog — Agentic Forge

All notable framework changes. Consuming projects pin a framework revision and
update `.agent/` deliberately; project-owned state stays in `.agent-state/`.

## [1.4.2] - 2026-10-19 — Quality-gate hotfix

### Fixed

- `forge_paths` catches `ValueError` when decoding TOML, restoring a clean mypy run
  on Python 3.11+ with current mypy versions.
- `forge_metrics_checks.should_skip_file` now skips the metrics file and tool caches
  (`.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `__pycache__`, `.git`), avoiding
  self-validation and inflated scans.
- `.gitignore` covers `.mypy_cache/` and `.pytest_cache/`.

### Migration

- No action required; consuming projects can bump `.agent/` to the v1.4.2 tag.

## [1.4.1] - 2026-10-18 — qa-docker compatibility alias

### Fixed

- Restored `skills/qa-docker/SKILL.md` as a **deprecated alias** that points to
  `testing-standards`. Existing project overlays, workflows and `AGENTS.md` links
  from v1.3.x keep validating until the alias is removed in the next major
  release. The alias contains no duplicated guidance.

### Migration

- Update `qa-docker` references to `testing-standards`; the alias is temporary.

## [1.4.0] - 2026-10-18 — Tests, CI and configurable tooling

### Added

- A pytest suite under `tests/` covering the validator, graph, memory pruning,
  lesson extraction and project-command runner.
- CI workflows (`.github/` and `.forgejo/`) plus `scripts/ci.sh` running Ruff,
  Format, mypy and pytest on Python 3.9, 3.11 and 3.13.
- `forge.py --version` backed by a `VERSION` file.
- `forge.py project <test|test-full|lint|format|type|bump>` commands driven by
  `forge.toml` (`test_command`, `lint_command`, `format_command`,
  `type_command`, `version_bump_command`).
- `max_lesson_lines` and `strict_agent_system` are now consumed by the tooling.
- Domain-pack (`scaffold/<domain>/`) skill and workflow validation; templates are
  marked with `template: true`.
- `tomli` fallback for Python < 3.11 and `requirements.txt` /
  `requirements-dev.txt`.

### Changed

- `qa-docker` was merged into `testing-standards`; Docker and mock guidance now
  lives in a single skill.
- Metrics checks and reports no longer hardcode a specific analyzer name; score
  sources and optional security/i18n KPIs are data-driven.
- The lesson extractor no longer references a specific analyzer command.
- `QUICK_REFERENCE.md` workflow/skill tables are synchronized with frontmatter
  and covered by a regression test.
- Documentation paths use `docs/MAINTENANCE_LOG.md` instead of a project-specific
  layout.

### Fixed

- Scaffold workflow `audit-plugin` referenced an overlay-only skill; it now uses
  the domain-pack `qgis-core` skill.
- `validate --graph` exits non-zero on broken references in the consolidated
  graph module.
- A standalone framework checkout now resolves its own root, and the optional
  project adapter `scripts/sync_metrics.py` no longer fails validation.
- Ruff, Ruff format and mypy are clean across the framework tooling and tests.

### Migration

- Replace `qa-docker` skill references with `testing-standards`.
- Projects that call the tooling on Python 3.9/3.10 must install
  `requirements.txt` (or `tomli`).
- Custom workflows can replace direct runner commands with `forge.py project`.

## [1.3.0] - 2026-10-18 — Quality gates that enforce

### Fixed

- `forge.py validate --graph` now exits `1` when a workflow references an unknown
  skill or script. Previously it always exited `0` unless `--validate` or
  `--json` was also passed, so the documented reference-integrity gate could not
  block anything.
- `forge.py metrics validate` no longer checks `scaffold/<domain>/` packs against
  the project's ground truth. Sample metrics shipped by domain packs (for
  example the QGIS reference values) produced permanent false positives.
- `coding-standards` now references `[project].max_cc` (default `10`) instead of
  hardcoding cyclomatic complexity 10, so projects with a different limit are
  validated consistently.
- `forge.py memory prune` now parses the Markdown-bullet lessons format used by
  projects, keeps supporting fenced YAML blocks, imports PyYAML lazily and exits
  non-zero on parse errors.

### Changed

- `forge.py memory prune` is a **dry-run by default**. Pass `--apply` to rewrite
  `AGENT_LESSONS.md` and delete expired `next_steps` snapshots.
- `QUICK_REFERENCE.md` and `workflows/index.md` document the new flag.

### Included from main since v1.2.0

- `forge.py memory check` enforces the 350-line active-lesson budget.
- Validation and the dependency graph include project overlay workflows from
  `.agent-state/workflows/`, and duplicate workflow names are rejected.
- Testing workflows standardize on `unittest`.
- QGIS release notes were refreshed to the current test count.

### Migration

- Custom close-session flows that expected `memory prune` to delete files must
  pass `--apply`.
- Repositories with broken skill/script references will now fail
  `validate --graph`; fix the references or run `--graph --json` first to inspect
  them.
- Projects without `[project].max_cc` keep the previous CC 10 default. YAML-based
  lesson files remain supported and are rewritten under `--apply`.

### Known follow-ups

- Tooling requires Python 3.11+ (`tomllib`) while some consuming projects still
  support 3.9.
- `forge_metrics.py` and `lesson_extractor.py` still contain reference-project
  constants that should be generalized.
- The framework tooling has no automated tests yet.

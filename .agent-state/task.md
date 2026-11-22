# Active Task Board — Freehand Digitize 2.0.2

> Detailed history: `.agent-state/history/tasks/`. This board only tracks the
> current work; closed sessions are archived.

## 🎯 Focus: 2.0.2 — parity, QA gate and deleted-layer guards

### Planning and baseline

- [x] Audit `freehandEditing` vs the 1.0.0 rewrite (16 defects identified).
- [x] Write and approve `docs/maintainer/PLAN_FREEHAND_PARITY.md`.
- [x] Revert the unreviewed scaffold and create the git baseline commit.
- [x] Vendor Agentic Forge 1.4.2 under `.agent/` (no submodule: the workspace
      was not a git repository at copy time).

### Plugin implementation

- [x] `core/`: constants, geometry rules, stroke sampling, settings + legacy
      `/freehandEdit/tolerance` migration.
- [x] `gui/`: pencil cursor, Qt5/Qt6 shims, geometry factory, `FreehandTool`
      (CTRL snapping, rubber band, secondary-release finish), `FeatureCreator`
      (defaults, form, undo, validity prompt).
- [x] `freehand_plugin.py`: action, tolerance spinbox, layer enablement,
      lifecycle, unload.
- [x] Metadata 2.0.0, 128×128 icon, GPL-2.0 LICENSE, README, CHANGELOG.

### QA

- [x] `pyproject.toml`, `uv.lock`, `.python-version`, Makefile.
- [x] ruff / flake8 / mypy / qgis-analyzer gates green.
- [x] 145 tests (57 unit + 88 QGIS 4.2.2 integration incl. gate) green.
- [x] `qgis-manage validate --strict` and ZIP validated.
- [x] CI, pre-commit, Dockerfile, devcontainer, detect-secrets baseline.
- [x] Python 3.9 syntax compatibility test.

### Process and planning

- [x] Add the mandatory plan-first procedure (`docs/maintainer/CHANGE_PROCEDURE.md`).
- [x] Add the `plan-first` skill and `/plan-change` workflow.
- [x] Reshape plan revision 2 approved for v2.0.0 (target = geometry under the
      stroke; optional selection filter).
- [x] Implement and verify reshape; plan marked IMPLEMENTED.
- [x] Implement vertex sampling settings (pixels/layer units, geographic
      warning) and edit-session gating (tools only while editing).
- [x] Implement feature difference with selected pair or mouse target/cutter
      and confirmation dialog.
- [x] CI checkout fix implemented; GitHub Actions run 44684907873 green.
- [x] Tag `v2.0.0` created and pushed; GitHub Release published with ZIP assets.
- [x] Feature roadmap approved (`docs/maintainer/PLAN_FEATURE_ROADMAP.md`);
      no stage started. Stage 1 awaits an explicit kickoff.
- [x] Deleted-layer lifecycle fix implemented as 2.0.1; GitHub Release
      published and deployed locally.
- [x] 2.0.1 uploaded to plugins.qgis.org; approval pending.
- [x] 2.0.2 guards published on GitHub and deployed; kept by the user.
- [x] P1 deleted-layer guards implemented as 2.0.2; GitHub Release `v2.0.2`
      published and deployed; **kept by the user**; portal upload pending 2.0.1
      approval.
- [ ] Portal: confirm 2.0.1 approval (portal 502 on 2026-11-22), then upload 2.0.2.
- [ ] English i18n base + `es`/`pt_BR`/`fr`/`de`/`it`/`id` catalogs
      (`docs/maintainer/PLAN_I18N_ENGLISH_BASE.md`, revision 3) proposed;
      release gated until 2.0.2 is public in the portal.
- [ ] Portal: 2.0.1 pending approval; 2.0.2 GitHub-only, not uploaded.

### Internationalization

- [x] `QCoreApplication.translate` integration with the `FreehandDigitize` context.
- [x] English catalog (`i18n/freehand_digitize_en.ts/.qm`) and master data JSON.
- [x] Locale loader with full/2-letter fallback and translator lifecycle.
- [x] `make transup` / `transcompile` / `i18n-check` + catalog tests.

### Documentation guides

- [x] `docs/ARCHITECTURE_EN.md` adapted to the real core/gui design.
- [x] `DOCS_STYLE_GUIDE`, `COMMIT_GUIDELINES`, `LOGGING_GUIDELINES` and
      `USER_GUIDE_CONVENTIONS` adapted under `docs/maintainer/`.
- [x] `docs/maintenance/DEVELOPMENT_LOG.md` created with the 2.0.0 session.
- [x] `scripts/check_docs.py` + `make docs-check` wired into `pre-release` and CI.
- [x] Language policy: English README/CHANGELOG/user guide/metadata; internal
      plan, parity report, development log and logging guide in Spanish.

### Agentic system and docs

- [x] `AGENTS.md`, `AI_CONTEXT.md`, `forge.toml`, `opencode.json`.
- [x] `.agent-state/` state, memory, overlay skills and workflows.
- [x] `docs/maintainer/FEATURE_PARITY.md` and adapted
      `docs/maintainer/uv_modernization_guide.md`.
- [x] `forge validate` green with `strict_agent_system = true`.

## 📌 Pending

- [x] P0 QA gate implemented: `test-qgis` fails when QGIS is unavailable;
      `forge test-full` runs 88 tests.
- [x] P1 deleted-layer guards implemented as 2.0.2; kept by the user.

- [x] Run `make pre-release` and `make security-scan` end to end.
- [x] Run `make qt6-check` (packaged ZIP, no enum errors).
- [x] Run `make docker-test` (QGIS/Qt5 container: 88 integration cases OK).
- [x] Metadata points to the dedicated repository (https://github.com/geociencio/freehand-digitize).
- [x] Implement freehand reshape (features under the stroke, optional selection
      filter, multi-feature single undo) and deploy it to QGIS 4.

# Next Steps — Freehand Digitize 2.0.1

**Updated:** 2026-11-21
**Session:** release_2_0_1_layer_fix

## ✅ Current state

- **Plugin 2.0.1** implemented with full `freehandEditing` parity plus freehand
  reshape, sampling, edit-session gating and feature difference: tolerance
  spinbox/persistence, geographic-CRS policy, pixel/layer-unit sampling, CTRL
  snapping, pencil cursor, layer-CRS geometry, attribute form, provider defaults,
  undo, validity prompt, layer enablement, secondary-release finish and ESC cancel.
- **2.0.1** fixes the editing-signal lifecycle; **2.0.2** guards the remaining
  deleted-layer paths in creators/tool/callbacks.
- **Architecture**: `core/` (no QGIS/Qt) + `gui/` (PyQGIS) +
  `freehand_plugin.py` (wiring); Qt5/Qt6 shims in `gui/qt_compat.py`.
- **Tests**: 145 total — 57 unit (no QGIS) and 88 integration (incl. QGIS gate),
  green against both QGIS 4.2.2 (host, Qt6) and the QGIS container (Qt5);
  `make test` reports the integration layer as skipped when QGIS is absent.
- **QA gate fixed**: `test-qgis` auto-detects a QGIS Python (or uses
  `QGIS_PYTHON`) and fails with `REQUIRE_QGIS=1` if QGIS is missing.
- **QA**: ruff, flake8, mypy (core), qgis-analyzer (`--max-cc 10`),
  `qgis-manage validate --strict`, `package --repo-check`, `validate --zip`,
  `security --portal` (0 findings) and `pyqgis4-checker` (0 enum errors) green;
  CI/pre-commit/Docker/detect-secrets configured.
- **i18n**: Spanish source UI with an English catalog; locale loader, master
  data JSON, `make i18n-check` and catalog tests.
- **Docs**: English README, CHANGELOG, metadata and user guide; architecture,
  style/commit/user-guide conventions, a development log and `make docs-check`;
  internal plan, parity report, development log and logging guide remain Spanish.
- **Agentic**: framework vendored in `.agent/`, state in `.agent-state/`,
  roles in `opencode.json`, config in `forge.toml`.

## 🧪 Verification commands

```bash
UV_CACHE_DIR=$PWD/.uvcache uv sync --frozen
make test
make test-qgis
make lint && make flake8 && make mypy
make analyzer
make agent-validate
make qgis-validate
make zip
```

## 📌 Remaining

1. **2.0.1 portal approval**: 2.0.0 is approved; 2.0.1 is uploaded and pending.
   2.0.2 is published on GitHub; upload 2.0.2 to the portal after 2.0.1 is
   approved (or if 2.0.1 is blocked).
2. After 2.0.2 portal approval, announce the patch.
3. **Feature roadmap approved**; no stage started. On request, begin Stage 1
   (Backspace) for 2.1.0.
4. Residual deleted-layer guards in creators/tool remain a separate P1.
5. Run the real QGIS 3.28 smoke test (or raise `qgisMinimumVersion`).
6. Optional: add `ai-context-core` and `make context` if the team wants the
   generated context bundle; `AI_CONTEXT.md` is curated manually for now.

## ▶️ How to resume

```bash
# from the repository root
/start-session
```

Then check the portal approval and, if continuing development, ask for Stage 1.

## 📎 Key files

- `AGENTS.md` — canonical agent rules.
- `docs/maintainer/FEATURE_PARITY.md` — upstream vs 2.0.0 matrix.
- `docs/maintainer/PLAN_FREEHAND_PARITY.md` — approved plan.
- `docs/maintainer/uv_modernization_guide.md` — uv/QA guide.
- `.agent-state/memory/AGENT_LESSONS.md` — QGIS/Qt/tooling traps.

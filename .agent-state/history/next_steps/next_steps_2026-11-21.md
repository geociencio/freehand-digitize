# Next Steps — Freehand Digitize 2.0.1

**Updated:** 2026-11-21
**Session:** release_2_0_1_layer_fix

## ✅ Current state

- **Plugin 2.0.1** implemented with full `freehandEditing` parity plus freehand
  reshape, sampling, edit-session gating and feature difference: tolerance
  spinbox/persistence, geographic-CRS policy, pixel/layer-unit sampling, CTRL
  snapping, pencil cursor, layer-CRS geometry, attribute form, provider defaults,
  undo, validity prompt, layer enablement, secondary-release finish and ESC cancel.
- **2.0.1** fixes the deleted-layer `RuntimeError` (sip + destroyed signal).
- **Architecture**: `core/` (no QGIS/Qt) + `gui/` (PyQGIS) +
  `freehand_plugin.py` (wiring); Qt5/Qt6 shims in `gui/qt_compat.py`.
- **Tests**: 134 total — 57 unit (no QGIS) and 77 integration, green against both
  QGIS 4.2.2 (host, Qt6) and the QGIS container (Qt5); `make test` reports the
  integration layer as skipped when QGIS is absent.
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

1. **Upload 2.0.1 to the portal**: 2.0.0 is approved and public (plugin ID
   7091), but it still has the deleted-layer bug. Upload
   `dist/freehand_digitize.2.0.1.zip`; 2.0.1 is already published on GitHub.
2. After the 2.0.1 portal approval, announce the update; the GitHub Release is
   already public.
3. **Feature roadmap approved**; no stage started. On request, begin Stage 1
   (Backspace) for 2.1.0.
4. Run the real QGIS 3.28 smoke test (or raise `qgisMinimumVersion`).
5. Optional: add `ai-context-core` and `make context` if the team wants the
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

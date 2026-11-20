# Implementation Plan — Freehand Reshape

> **Status: PROPOSED** — no code changes until the user explicitly approves this
> plan.
>
> Version: 2.1.0 (recommended; see §9) | Date: 2026-11-19
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Goal

Add a **reshape** action to Freehand Digitize: the user selects one existing
line or polygon feature, activates *Reshape*, draws a freehand stroke that
crosses the feature boundary, and the feature geometry is reshaped as a single
undoable edit.

The new action must coexist with the existing freehand creation tool and keep
the plugin's QGIS 3.28–4.x / Qt5–Qt6 compatibility, translation catalogs, tests
and packaging gates.

---

## 2. Scope and non-goals

### In scope

- A second checkable action in the Digitize toolbar and the Vector menu.
- A freehand reshape tool that reuses the existing stroke capture (layer CRS,
  device-pixel thinning, `Ctrl` snapping, `Esc` cancel).
- Applying the reshape to **exactly one selected feature** of the active,
  editable line/polygon layer.
- One undo command per reshape; provider failure and invalid geometry are
  handled without leaving an empty command.
- Spanish source strings + English catalog entries.
- Integration tests, docs, metadata and version bump.

### Out of scope

- Reimplementing every QGIS native reshape workflow (selection prompt, multiple
  selected features, click-based vertex editing).
- A separate tolerance for reshaping; the raw stroke is used.
- Reshaping point layers or non-editable/read-only providers.
- Changing the existing creation workflow.

---

## 3. Current state

- `FreehandTool` (`gui/freehand_tool.py`) captures a stroke, builds a line or
  polygon and emits `geometryFinished(geometry, layer)`.
- `FreehandDigitizePlugin` (`freehand_plugin.py`) owns one action, one tool, the
  tolerance spinbox and the layer enablement.
- `FeatureCreator` (`gui/feature_creator.py`) simplifies, validates and inserts
  a **new** feature.
- `gui/texts.py` holds translatable UI strings; `gui/i18n.py` loads the catalog.
- There is no selection-aware action and no geometry modification of existing
  features.

---

## 4. API evidence (QGIS 4.2.2, Python 3.14, PyQt6)

| Claim | Verified result |
| :--- | :--- |
| `QgsMapToolReshape` is reusable from Python | **No.** `qgis.gui` exposes no `QgsMapToolReshape` in QGIS 4.2.2; the `qgis/qgis:latest` container (3.99.0-Master) also lacks it. |
| `QgsGeometry.reshapeGeometry` exists | **Yes.** Signature: `reshapeGeometry(reshapeLineString: QgsLineString) -> Qgis.GeometryOperationResult`. |
| Result codes | `Success`, `NothingHappened`, `InvalidBaseGeometry`, `InvalidInputGeometryType`, `GeometryEngineError`, `LayerNotEditable`, … |
| Line reshape | Feature `(0,0)-(5,0)-(10,0)`, stroke `(3,-1),(3,1),(7,1),(7,-1)` → `Success`, geometry `(0 0, 3 0, 3 1, 7 1, 7 0, 10 0)`. A single crossing returns `NothingHappened`. |
| Polygon reshape | Square `(0,0)-(10,10)`, vertical stroke `(5,-2)-(5,12)` → `Success`; the result is the half-polygon bounded by the stroke. The direction/intersections determine the result, as in the QGIS reshape algorithm. |
| Undo | `layer.beginEditCommand` + `layer.changeGeometry` + `layer.endEditCommand`, then `undoStack().undo()` restores the original geometry. |
| Selection | `layer.selectedFeatureIds()` returns the selected ids; one selected feature is enough. |

Prototype location: ephemeral `/tmp` script; **no repository code was changed**.

---

## 5. UX and behaviour

### Action

- Spanish source label: **“Reformar geometría”**.
- English catalog: **“Reshape feature”**.
- Tooltip (Spanish source): “Selecciona una entidad de la capa activa y dibuja un
  trazo que cruce su borde para reformarla.”
- Added to the Digitize toolbar and **Vector → Freehand Digitize**, next to the
  creation action.

### Required preconditions

1. Active layer is a valid, editable **line or polygon** vector layer.
2. **Exactly one** feature is selected.
3. The layer is in edit mode (the tool starts the session if needed).

If a precondition fails, the action is unchecked and a message-bar warning is
shown; no geometry is modified.

### Drawing

- Same cursor, rubber band (line) and device-pixel thinning as the creation
  tool.
- `Ctrl` snapping of the first/last vertex is reused.
- The stroke is stored in **layer coordinates**.
- Release any mouse button finishes; `Esc` cancels the stroke.
- The tolerance spinbox is **not** applied: reshape uses the raw stroke. The
  spinbox remains associated with new-feature creation.

### Applying

1. `QgsLineString` is built from the stroke points.
2. `feature.geometry().reshapeGeometry(line_string)` is called.
3. Only `Success` continues; other codes produce a translated warning.
4. The result must be non-empty and `isGeosValid()`; otherwise abort.
5. `beginEditCommand("Freehand Digitize: reformar entidad")` →
   `changeGeometry(fid, geometry)` → `endEditCommand`, repaint, refresh.
6. `Ctrl+Z` restores the previous geometry.

### Failure messages

- No selection: “Selecciona una entidad para reformar.”
- More than one: “Selecciona solo una entidad para reformar.”
- Not editable: reuse the existing “No se pudo poner «{name}» en edición.”
- Stroke did not cross: “El trazo no cruza la entidad; no se modificó nada.”
- Invalid result: “La geometría reformada no es válida; no se modificó nada.”
- Provider rejection: “La capa «{name}» rechazó la reforma.”

---

## 6. Design

### Files

| File | Action | Responsibility |
| :--- | :--- | :--- |
| `gui/freehand_tool.py` | Modify | `MODE_CREATE` / `MODE_RESHAPE`; force a line stroke and line rubber band in reshape mode; minimum 2 points; keep snapping/thinning. |
| `gui/reshape_creator.py` | **New** | Selection validation, `QgsLineString`, `reshapeGeometry`, edit command, `changeGeometry`, warnings. |
| `gui/texts.py` | Modify | Reshape action/tooltip, undo label and failure strings. |
| `freehand_plugin.py` | Modify | Second action/tool/creator, activation, signal routing, check-state sync, unload helpers. |
| `tests/integration/test_reshape_creator.py` | **New** | Line/polygon reshape, undo, selection and failure cases. |
| `tests/integration/test_freehand_tool.py` | Modify | Reshape-mode tool behaviour. |
| `tests/integration/test_plugin.py` | Modify | Reshape action/lifecycle/end-to-end. |
| `i18n/freehand_digitize_en.ts/.qm` | Regenerate | New catalogue entries. |
| `scripts/i18n/master_data/en.json` | Modify | Spanish → English translations. |
| `README.md`, `docs/user/USER_GUIDE.md`, `docs/ARCHITECTURE_EN.md`, `CHANGELOG.md`, `metadata.txt` | Modify | Feature docs and version. |
| `tests/test_i18n_catalogs.py` | Modify | Required reshape string(s) and count expectations if hard-coded. |

### Data flow

```
selected feature
      │
      ▼
Reshape action ──► validate layer + exactly one selection + editable
      │
      ▼
FreehandTool(mode="reshape") ──► stroke in layer CRS (Ctrl snapping)
      │
      ▼
geometryFinished(line geometry, layer)
      │
      ▼
ReshapeCreator
  1. selectedFeatureIds() → one fid
  2. QgsLineString from line geometry
  3. geom.reshapeGeometry(line)
  4. result == Success and geom.isGeosValid()
  5. beginEditCommand → changeGeometry(fid, geom) → endEditCommand
  6. repaint / refresh
```

### Plugin lifecycle

- `self.reshape_tool` and `self.reshape_action` alongside the existing ones.
- `_on_map_tool_set` checks both actions.
- `_deactivate_tool` unsets whichever tool is active and unchecks both.
- `unload` is refactored into small helpers (`_disconnect_signals`,
  `_cleanup_tools`, `_cleanup_actions`, `_remove_translator`) to keep cyclomatic
  complexity at or below 10.

---

## 7. Tests

### Integration (`tests/integration`)

| Test | Assertion |
| :--- | :--- |
| `test_reshape_line_feature` | Line stroke crossing twice changes the geometry and returns `True`. |
| `test_reshape_polygon_feature` | Polygon stroke crossing twice changes the ring and returns `True`. |
| `test_reshape_undo` | One `undo()` restores the original geometry. |
| `test_reshape_requires_selection` | No selection → `False`, warning, no edit command. |
| `test_reshape_requires_single_selection` | Two selected features → `False`, warning. |
| `test_reshape_without_intersection` | Stroke not crossing → `False`, warning, geometry unchanged. |
| `test_reshape_starts_editing` | Non-editable layer → starts editing and applies. |
| `test_reshape_mode_emits_line` | `FreehandTool(mode=reshape)` emits a line, never a closed polygon. |
| `test_reshape_action_exists` | Plugin exposes the second action and tool. |
| `test_reshape_action_requires_selection` | Activation without selection warns and does not install the tool. |

Run:

```bash
make test
make test-qgis
make docker-test
```

### Static/i18n

```bash
make lint
make flake8
make mypy
make analyzer
make i18n-check
make docs-check
make agent-validate
```

---

## 8. i18n

Context: `FreehandDigitize`. New Spanish source strings:

| Source (Spanish) | English catalog |
| :--- | :--- |
| `Reformar geometría` | `Reshape feature` |
| `Selecciona una entidad de la capa activa y dibuja un trazo que cruce su borde para reformarla.` | `Select a feature on the active layer and draw a stroke crossing its boundary to reshape it.` |
| `Selecciona una entidad para reformar.` | `Select a feature to reshape.` |
| `Selecciona solo una entidad para reformar.` | `Select only one feature to reshape.` |
| `El trazo no cruza la entidad; no se modificó nada.` | `The stroke does not cross the feature; nothing was changed.` |
| `La geometría reformada no es válida; no se modificó nada.` | `The reshaped geometry is not valid; nothing was changed.` |
| `La capa «{name}» rechazó la reforma.` | `Layer “{name}” rejected the reshape.` |
| `Freehand Digitize: reformar entidad` | `Freehand Digitize: reshape feature` |

Procedure: `make transup` → `make transcompile` → `make i18n-check`; add the
reshape action string to `tests/test_i18n_catalogs.py` required strings.

---

## 9. Versioning

**Decision required.** Recommended: **2.1.0** (new user-facing feature, backwards
compatible). Alternative: fold into **2.0.0** if v2.0.0 has not been tagged or
published yet (currently no `v2.0.0` tag exists).

Files to bump for 2.1.0:

- `metadata.txt` (`version`, `changelog`, `about` feature list)
- `pyproject.toml` (`version`)
- `CHANGELOG.md` (new `## 2.1.0` section)
- `tests/test_metadata.py` (expected version)
- version headers in `docs/ARCHITECTURE_EN.md`, `docs/user/USER_GUIDE.md`,
  `docs/maintainer/DOCS_STYLE_GUIDE.md`, `docs/maintainer/COMMIT_GUIDELINES.md`
  (if they are updated in the same change)
- `AI_CONTEXT.md` and `.agent-state/memory/agent_metrics.json`

If folded into 2.0.0, only the changelog/about and tests need the new bullet.

---

## 10. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| Reshape semantics are surprising (a polygon may be cut instead of notched) | Document the “stroke crosses the boundary twice” rule; test line and polygon; do not promise a specific notch shape. |
| User expects the native QGIS click-based reshape | State in the plan/release notes that the native tool is not available to Python; this is a freehand reshape. |
| Multiple selected features | Require exactly one; warn otherwise. |
| Non-editable layer | Reuse `startEditing` and the existing warning. |
| Invalid geometry after reshape | Abort before `changeGeometry`; keep the original. |
| Empty undo command | `destroyEditCommand()` on failure. |
| CC regression in `unload` | Split cleanup into helpers; run `make analyzer`. |
| QGIS 3.28 API differences | Integration suite in the Qt5/QGIS container; `QgsLineString`/`reshapeGeometry` are QGIS 3 APIs. |
| i18n catalog drift | `make transup` + `make i18n-check`; test required strings and placeholders. |
| Metadata/ZIP regression | `make qgis-validate`, `make zip`, `make portal-check`. |

---

## 11. Acceptance criteria

- [ ] The reshape action is visible in the Digitize toolbar and Vector menu.
- [ ] Action activation without a selection or with multiple selections warns and
      does not install the tool.
- [ ] A selected line feature is reshaped by a crossing stroke; one undo restores
      it.
- [ ] A selected polygon feature is reshaped by a crossing stroke.
- [ ] A non-crossing stroke changes nothing and warns.
- [ ] `Esc` cancels; `Ctrl` snapping works; the stroke is in layer CRS.
- [ ] English and Spanish UI strings are translated and catalog-complete.
- [ ] `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` and
      `make docker-test` pass.
- [ ] No regression in the creation workflow or existing tests.
- [ ] The plan is marked `IMPLEMENTED` with the commit hash and results.

---

## 12. Implementation procedure (after approval)

1. Update `docs/maintainer/PLAN_RESHAPE.md` status to `APPROVED` and record the
   version decision.
2. Add reshape strings to `gui/texts.py`; run `make transup` after the code wraps
   them.
3. Add `MODE_RESHAPE` to `gui/freehand_tool.py` (line stroke, line rubber band,
   minimum 2 points).
4. Add `gui/reshape_creator.py` with selection/geometry/edit-command logic.
5. Wire the second action/tool in `freehand_plugin.py`; refactor `unload` into
   helpers.
6. Add integration tests (creator, tool, plugin).
7. Add the reshape strings to `scripts/i18n/master_data/en.json`; run
   `make transup`, `make transcompile`, `make i18n-check`.
8. Update README, user guide, architecture, CHANGELOG and metadata; bump the
   version per §9.
9. Run `make pre-release`, `make zip`, `make security-scan`, `make qt6-check`,
   `make docker-test`.
10. Mark the plan `IMPLEMENTED` with results and commit.
11. Deploy with `uv run qgis-manage deploy --qgis-version 4` and smoke-test in
    QGIS 4 (and QGIS 3.28/3.99 container).

---

## 13. Verification commands

```bash
make test
make test-qgis
make docker-test
make pre-release
make zip
make security-scan
make qt6-check
make docs-check
make i18n-check
make agent-validate
```

---

## 14. Rollback

- Revert the feature commit(s) with `git revert <sha>`.
- If only the deployed plugin is wrong, redeploy the previous commit with
  `qgis-manage deploy`.
- Keep the plan document; mark it `REJECTED`/`REVERTED` with the reason.

---

## 15. Approval

The plan is **PROPOSED**. Implementation starts only after the user confirms:

1. Version: **2.1.0** or fold into 2.0.0?
2. UX: require exactly one selected feature (recommended) and no tolerance for
   reshape?
3. Scope: single-part and multi-part line/polygon best effort (recommended), with
   no native click-based reshape?
4. Action label: **Reformar geometría** / **Reshape feature** (or another label)?

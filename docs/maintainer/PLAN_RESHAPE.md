# Implementation Plan — Freehand Reshape

> **Status: PROPOSED (revision 2)** — no code changes until the user explicitly
> approves this plan.
>
> Version: 2.1.0 (recommended; see §9) | Date: 2026-11-19
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)
>
> **Revision 2 (2026-11-19):** the target is no longer “one preselected feature”.
> The reshape is applied to the geometries **under the drawn stroke**; a
> selection, when present, restricts the operation to the selected features.

---

## 1. Goal

Add a **reshape** action to Freehand Digitize: the user draws a freehand stroke
over existing line/polygon features and the geometries **under that stroke** are
reshaped as one undoable edit. Preselecting a feature is optional; a selection
narrows the target set.

The action must coexist with the freehand creation tool and preserve QGIS
3.28–4.x / Qt5–Qt6 compatibility, i18n, tests and packaging gates.

---

## 2. Scope and non-goals

### In scope

- A second checkable action in the Digitize toolbar and the Vector menu.
- A freehand reshape tool reusing stroke capture (layer CRS, device-pixel
  thinning, `Ctrl` snapping, `Esc` cancel).
- **Automatic target detection**: all features of the active layer whose
  geometry intersects the stroke, limited to the drawn stroke's bounding box.
- **Optional selection filter**: if one or more features are selected, only the
  selected features that also intersect the stroke are reshaped.
- Multiple features reshaped in one operation and one undo command.
- Clear messages for no target, no successful reshape, invalid geometry and
  provider failure.
- Spanish source strings + English catalog, tests, docs, metadata and version
  bump.

### Out of scope

- The native QGIS click-based reshape workflow (not exposed to Python; see §4).
- Reshaping point layers or non-editable/read-only providers.
- Applying the simplification tolerance to the reshape stroke (raw stroke; see
  §5).
- Automatic feature creation; the existing creation action is unchanged.
- Undoing individual features of a multi-feature reshape (the whole operation is
  one undo command).

---

## 3. Current state

- `FreehandTool` (`gui/freehand_tool.py`) captures a stroke, builds a line or
  polygon and emits `geometryFinished(geometry, layer)`.
- `FreehandDigitizePlugin` (`freehand_plugin.py`) owns one action, one tool, the
  tolerance spinbox and layer enablement.
- `FeatureCreator` (`gui/feature_creator.py`) simplifies, validates and inserts
  **new** features.
- There is no selection-aware action and no modification of existing features.

---

## 4. API evidence (QGIS 4.2.2, Python 3.14, PyQt6)

| Claim | Verified result |
| :--- | :--- |
| `QgsMapToolReshape` is reusable from Python | **No.** `qgis.gui` exposes no `QgsMapToolReshape` in QGIS 4.2.2; the `qgis/qgis:latest` container (3.99.0-Master) also lacks it. |
| `QgsGeometry.reshapeGeometry` exists | **Yes.** `reshapeGeometry(reshapeLineString: QgsLineString) -> Qgis.GeometryOperationResult`. |
| Result codes | `Success`, `NothingHappened`, `InvalidBaseGeometry`, `InvalidInputGeometryType`, `GeometryEngineError`, `LayerNotEditable`, … |
| Line reshape | Feature `(0,0)-(5,0)-(10,0)`, stroke `(3,-1),(3,1),(7,1),(7,-1)` → `Success`, geometry `(0 0, 3 0, 3 1, 7 1, 7 0, 10 0)`. A single crossing returns `NothingHappened`. |
| Polygon reshape | Square `(0,0)-(10,10)`, vertical stroke `(5,-2)-(5,12)` → `Success`; the result is the half-polygon bounded by the stroke. Direction/intersections determine the result, as in the QGIS reshape algorithm. |
| Undo | `beginEditCommand` + `changeGeometry` + `endEditCommand`, then `undoStack().undo()` restores the original geometry. |
| Target detection under the stroke | `QgsFeatureRequest().setFilterRect(stroke.boundingBox())` + `feature.geometry().intersects(stroke)` returned both polygons of a stacked pair when a vertical stroke crossed them. |
| Selection as filter | `layer.selectedFeatureIds()` can restrict the candidate set; an empty selection means “all features under the stroke”. |

Prototype location: ephemeral `/tmp` scripts; **no repository code was changed**.

---

## 5. UX and behaviour

### Action

- Spanish source label: **“Reformar geometría”**.
- English catalog: **“Reshape feature”**.
- Tooltip (Spanish source): “Dibuja un trazo que cruce la geometría que quieras
  reformar. Si hay una selección, solo se reformarán las entidades
  seleccionadas.”
- Added to the Digitize toolbar and **Vector → Freehand Digitize**, next to the
  creation action.
- The action is enabled for editable line/polygon layers; **no preselection is
  required**.

### Target resolution

1. Build the stroke in layer coordinates.
2. Candidate set:
   - If `layer.selectedFeatureIds()` is **not empty**: candidates are those
     selected features whose geometry intersects the stroke.
   - If the selection is **empty**: candidates are all features in the stroke
     bounding box whose geometry intersects the stroke.
3. For each candidate, call `reshapeGeometry(stroke_line_string)`.
4. Keep only `Success` results with a valid, non-empty geometry.
5. Apply all successful results in **one** edit command; one `Ctrl+Z` restores all
   of them.
6. If no candidate intersects: warn “El trazo no cruza ninguna entidad”.
7. If candidates intersect but none can be reshaped: warn “El trazo no reformó
   ninguna entidad”.
8. On success with more than one feature, show an info message with the count;
   with one feature, no extra message is required.

### Drawing

- Same cursor, line rubber band and device-pixel thinning as the creation tool.
- `Ctrl` snapping of the first/last vertex is reused.
- Release any mouse button finishes; `Esc` cancels.
- The tolerance spinbox is **not** applied: the raw stroke is used. The spinbox
  remains associated with new-feature creation.

### Failure messages

- Layer not editable: reuse “No se pudo poner «{name}» en edición.”
- No feature under stroke: “El trazo no cruza ninguna entidad.”
- No successful reshape: “El trazo no reformó ninguna entidad.”
- Invalid result: “La geometría reformada no es válida; no se modificó nada.”
- Provider rejection: “La capa «{name}» rechazó la reforma.”

### Selection examples

| Selection | Stroke crosses | Result |
| :--- | :--- | :--- |
| None | Feature A | A reshaped |
| None | Features A and B | A and B reshaped in one undo |
| A | A and B | Only A reshaped |
| A | B only | Warning; B is not touched |
| A and B | A | Only A reshaped |

---

## 6. Design

### Files

| File | Action | Responsibility |
| :--- | :--- | :--- |
| `gui/freehand_tool.py` | Modify | `MODE_CREATE` / `MODE_RESHAPE`; force a line stroke and line rubber band in reshape mode; minimum 2 points; keep snapping/thinning. |
| `gui/reshape_creator.py` | **New** | Target detection under the stroke, optional selection filter, `QgsLineString`, `reshapeGeometry`, atomic edit command, messages. |
| `gui/texts.py` | Modify | Reshape action/tooltip, undo label, target/error messages, count message. |
| `freehand_plugin.py` | Modify | Second action/tool/creator, activation, signal routing, check-state sync, unload helpers. |
| `tests/integration/test_reshape_creator.py` | **New** | Auto-target, selection filter, line/polygon, multi-feature, undo, failures. |
| `tests/integration/test_freehand_tool.py` | Modify | Reshape-mode tool behaviour. |
| `tests/integration/test_plugin.py` | Modify | Reshape action/lifecycle/end-to-end. |
| `i18n/freehand_digitize_en.ts/.qm` | Regenerate | New catalogue entries. |
| `scripts/i18n/master_data/en.json` | Modify | Spanish → English translations. |
| `README.md`, `docs/user/USER_GUIDE.md`, `docs/ARCHITECTURE_EN.md`, `CHANGELOG.md`, `metadata.txt` | Modify | Feature docs and version. |
| `tests/test_i18n_catalogs.py` | Modify | Required reshape strings and count if hard-coded. |

### Target resolution algorithm

```
stroke_geom = QgsGeometry.fromPolylineXY(stroke_points)   # layer CRS
selected = layer.selectedFeatureIds()

if selected:
    candidates = [layer.getFeature(fid) for fid in selected]
    candidates = [f for f in candidates if f.geometry().intersects(stroke_geom)]
else:
    request = QgsFeatureRequest().setFilterRect(stroke_geom.boundingBox())
    candidates = [f for f in layer.getFeatures(request)
                  if f.geometry().intersects(stroke_geom)]

line = QgsLineString([QgsPoint(x, y) for x, y in stroke_points])
results = []
for feature in candidates:
    geom = feature.geometry()
    if geom.reshapeGeometry(line) == Qgis.GeometryOperationResult.Success:
        if geom.isGeosValid():
            results.append((feature.id(), geom))

if not results:
    warn(...)
    return False

layer.beginEditCommand("Freehand Digitize: reformar entidad(es)")
for fid, geom in results:
    if not layer.changeGeometry(fid, geom):
        layer.destroyEditCommand()
        warn("La capa rechazó la reforma.")
        return False
layer.endEditCommand()
layer.triggerRepaint()
refresh()
info(f"{len(results)} entidad(es) reformada(s)")
return True
```

### Data flow

```
reshape action
      │
      ▼
validate layer (editable, line/polygon)  ← no selection required
      │
      ▼
FreehandTool(mode="reshape") ──► stroke in layer CRS (Ctrl snapping)
      │
      ▼
geometryFinished(line geometry, layer)
      │
      ▼
ReshapeCreator
  1. selectedFeatureIds() → optional filter
  2. QgsFeatureRequest(bbox) + intersects(stroke)
  3. geom.reshapeGeometry(QgsLineString)
  4. keep Success + isGeosValid()
  5. one beginEditCommand → changeGeometry(each) → endEditCommand
  6. repaint / refresh / info count
```

### Plugin lifecycle

- `self.reshape_tool` and `self.reshape_action` alongside the existing ones.
- `_on_map_tool_set` checks both actions.
- `_deactivate_tool` unsets whichever tool is active and unchecks both.
- `unload` is refactored into small helpers (`_disconnect_signals`,
  `_cleanup_tools`, `_cleanup_actions`, `_remove_translator`) to keep cyclomatic
  complexity at or below 10.
- The reshape action is enabled for editable line/polygon layers; target
  resolution happens at stroke release, not at activation.

---

## 7. Tests

### Integration (`tests/integration`)

| Test | Assertion |
| :--- | :--- |
| `test_reshape_line_under_stroke_no_selection` | Stroke over a line feature reshapes it without preselecting. |
| `test_reshape_polygon_under_stroke_no_selection` | Stroke over a polygon reshapes its ring. |
| `test_reshape_multiple_features_one_undo` | Two features under the stroke are reshaped; one undo restores both. |
| `test_selection_filters_targets` | Selected A + stroke over A and B → only A changes. |
| `test_selection_without_intersection_warns` | Selected A + stroke over B only → no change, warning. |
| `test_reshape_no_feature_under_stroke` | Empty area → warning, no edit command. |
| `test_reshape_stroke_without_intersection` | Feature under bbox but not intersected → no change. |
| `test_reshape_without_success` | Candidate intersects but `reshapeGeometry` returns `NothingHappened` → warning. |
| `test_reshape_invalid_geometry` | Invalid result is rejected and original kept. |
| `test_reshape_starts_editing` | Non-editable layer → starts editing and applies. |
| `test_reshape_mode_emits_line` | `FreehandTool(mode=reshape)` emits a line, never a closed polygon. |
| `test_reshape_action_exists` | Plugin exposes the second action and tool. |
| `test_reshape_action_does_not_require_selection` | Activation installs the tool with no selection. |

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
| `Dibuja un trazo que cruce la geometría que quieras reformar. Si hay una selección, solo se reformarán las entidades seleccionadas.` | `Draw a stroke crossing the geometry you want to reshape. If there is a selection, only the selected features are reshaped.` |
| `El trazo no cruza ninguna entidad.` | `The stroke does not cross any feature.` |
| `El trazo no reformó ninguna entidad.` | `The stroke did not reshape any feature.` |
| `La geometría reformada no es válida; no se modificó nada.` | `The reshaped geometry is not valid; nothing was changed.` |
| `La capa «{name}» rechazó la reforma.` | `Layer “{name}” rejected the reshape.` |
| `{count} entidad(es) reformada(s).` | `{count} feature(s) reshaped.` |
| `Freehand Digitize: reformar entidad(es)` | `Freehand Digitize: reshape feature(s)` |

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
  (if updated in the same change)
- `AI_CONTEXT.md` and `.agent-state/memory/agent_metrics.json`

If folded into 2.0.0, only the changelog/about and tests need the new bullet.

---

## 10. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| Multiple features are reshaped unexpectedly | Document the rule; selection filters targets; show the count; one undo reverts all. |
| Overlapping features under the stroke | Selection is the disambiguator; warn when more than one feature is reshaped. |
| Reshape semantics are surprising (a polygon may be cut instead of notched) | Document “stroke crosses the boundary twice”; test line and polygon; do not promise a specific notch shape. |
| User expects the native QGIS click-based reshape | State in the plan/release notes that the native tool is not available to Python; this is a freehand reshape. |
| Non-editable layer | Use `startEditing` and the existing warning. |
| Invalid geometry | Abort that feature; if no valid results, change nothing. |
| Partial provider failure | Build all results first; one edit command; `destroyEditCommand` on any `changeGeometry` failure. |
| Large layers | Bounding-box request limits the candidate scan; intersection test filters further. |
| CC regression in `unload` | Split cleanup into helpers; run `make analyzer`. |
| QGIS 3.28 API differences | Integration suite in the Qt5/QGIS container; `QgsLineString`/`reshapeGeometry` are QGIS 3 APIs. |
| i18n catalog drift | `make transup` + `make i18n-check`; test required strings/placeholders. |
| Metadata/ZIP regression | `make qgis-validate`, `make zip`, `make portal-check`. |

---

## 11. Acceptance criteria

- [ ] The reshape action is visible in the Digitize toolbar and Vector menu.
- [ ] No preselection is required; a stroke over a feature reshapes it.
- [ ] A selection restricts the operation to selected features that intersect
      the stroke.
- [ ] Multiple features under the stroke are reshaped in one undo step.
- [ ] A stroke that crosses nothing warns and changes nothing.
- [ ] A non-crossing candidate warns and changes nothing.
- [ ] `Esc` cancels; `Ctrl` snapping works; the stroke is in layer CRS.
- [ ] English and Spanish UI strings are translated and catalog-complete.
- [ ] `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` and
      `make docker-test` pass.
- [ ] No regression in the creation workflow or existing tests.
- [ ] The plan is marked `IMPLEMENTED` with the commit hash and results.

---

## 12. Implementation procedure (after approval)

1. Update this plan status to `APPROVED` and record the version decision.
2. Add reshape strings to `gui/texts.py`.
3. Add `MODE_RESHAPE` to `gui/freehand_tool.py` (line stroke, line rubber band,
   minimum 2 points).
4. Add `gui/reshape_creator.py` with target detection, selection filter,
   geometry reshape and atomic edit command.
5. Wire the second action/tool in `freehand_plugin.py`; refactor `unload` into
   helpers.
6. Add integration tests (creator, tool, plugin) including multi-feature and
   selection-filter cases.
7. Add the reshape strings to `scripts/i18n/master_data/en.json`; run
   `make transup`, `make transcompile`, `make i18n-check`.
8. Update README, user guide, architecture, CHANGELOG and metadata; bump the
   version per §9.
9. Run `make pre-release`, `make zip`, `make security-scan`, `make qt6-check`,
   `make docker-test`.
10. Mark the plan `IMPLEMENTED` with results and commit.
11. Deploy with `uv run qgis-manage deploy --qgis-version 4` and smoke-test in
    QGIS 4 (and the QGIS 3.28/3.99 container).

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

The plan is **PROPOSED (revision 2)**. Implementation starts only after the user
confirms:

1. **Targeting**: no selection → all features under the stroke; with selection →
   only selected features under the stroke (recommended). Is that correct?
2. **Version**: **2.1.0** or fold into 2.0.0?
3. **Tolerance**: raw stroke, no simplification (recommended)?
4. **Label**: **Reformar geometría** / **Reshape feature** (or another)?
5. **Scope**: line + polygon, single-part and multi-part best effort?

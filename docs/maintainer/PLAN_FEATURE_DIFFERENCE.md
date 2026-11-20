# Implementation Plan — Feature Difference (Cut)

> **Status: IMPLEMENTED (2026-11-20)** — approved for **v2.0.0** with mouse
> selection (target and cutter) and the confirmation dialog. Implementation
> follows this plan.
>
> Version: 2.0.0 | Date: 2026-11-20
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Goal

Add a feature-level **difference / cut** operation: subtract one existing feature
from another and update the target in place.

- Target feature **A** keeps its attributes and becomes `A.difference(B)`.
- Cutter feature **B** is left unchanged.
- The operation is one undo command.

The primary case is polygon − polygon; line targets with line cutters are also
supported in the same layer. Cross-type and cross-layer differences are out of
scope for this UI.

---

## 2. Scope and non-goals

### In scope

- A **Diferencia de entidades** / **Feature difference** action in the Digitize
  toolbar and the Vector menu.
- Two ways to choose the target and cutter on the **active layer**:
  1. exactly two selected features → confirmation dialog;
  2. otherwise, a **mouse pick tool**: click the target feature, then the cutter.
- Action enabled while the layer is in edit mode (the current edit-session gate),
  regardless of the current selection count; picking is the fallback.
- `QgsGeometry.difference` with empty/invalid result checks.
- Target updated in one edit command; cutter untouched; attributes of the target
  preserved.
- Spanish source strings + English catalog, tests, docs and metadata.

### Non-goals

- **Split** into two new features (a line cutting a polygon into separate
  features). This plan implements difference, which returns one target geometry
  (possibly multipart).
- Cross-layer difference (target on one layer, cutter on another). A follow-up
  plan can add a layer picker.
- More than two selected features or multiple cutters.
- Picking features from another layer with the mouse (same-layer picking only).
- Point targets (the plugin only supports line/polygon layers).
- Attribute transfer or automatic deletion of the cutter.

---

## 3. Current state

- The plugin has edit-session gating: create/reshape require `layer.isEditable()`.
- `FeatureCreator` creates new features; `ReshapeCreator` modifies features under
  a freehand stroke.
- There is no feature-level boolean operation and no selection-count-aware
  action.
- The active layer's `selectionChanged` signal is not connected; the plugin only
  reacts to `currentLayerChanged`, `editingStarted` and `editingStopped`.
- No map tool identifies a feature for a Boolean operation.

### Mouse-pick API

`QgsMapToolIdentifyFeature(canvas, layer)` is available in QGIS 4.2.2 and emits
`featureIdentified` when the user clicks a feature of the chosen layer. It
provides the click-to-pick behavior needed here without a custom spatial query.
The signal has a `QgsFeature` and a feature-id overload; the implementation will
use the feature overload and fall back to a small `QgsFeatureRequest` query if
the binding is ambiguous on a target QGIS version.

---

## 4. API evidence (QGIS 4.2.2)

| Operation | Result |
| :--- | :--- |
| `QgsGeometry.difference(other)` | Returns a new `QgsGeometry`; the inputs are unchanged. |
| Polygon − polygon | Square `(0,0)-(10,10)` minus `(5,0)-(15,10)` → `Polygon ((5 0, 0 0, 0 10, 5 10, 5 0))`, valid. |
| Line − polygon (cross-layer only) | Line `(0,0)-(10,0)` minus a box around `x=4..6` → `MultiLineString ((0 0,4 0),(6 0,10 0))`; not exposed by the same-layer dialog. |
| Polygon − line (cross-layer only) | A vertical line through the square produces a polygon with a zero-width slit; not exposed by the same-layer dialog. |
| Empty result | A cutter covering the target returns an empty polygon (`isEmpty()` true). |
| Same geometry | `A.difference(A)` is empty. |
| Storing a multiline | A memory `LineString` layer accepted a `MultiLineString` result via `changeGeometry`. |

Prototype scripts ran in `/tmp`; **no repository code was changed**.

---

## 5. UX

### Action

- Spanish source label: **“Diferencia de entidades”**.
- English catalog: **“Feature difference”**.
- Tooltip: “Selecciona exactamente dos entidades: la objetivo y la de corte.”
- Added to the Digitize toolbar and **Vector → Freehand Digitize**.
- Enabled when the active layer is a valid line/polygon layer in **edit mode**.
- If exactly **two** features are selected, the action opens the confirmation
  dialog directly.
- Otherwise, the action activates the **pick tool**: click the target, then the
  cutter; after the second click the confirmation dialog opens with those two
  features.
- Disabled outside edit mode.

### Mouse pick flow

1. The user activates **Diferencia de entidades** without exactly two selected
   features.
2. The status bar/message bar says “Haz clic en la entidad objetivo”.
3. The pick tool highlights/accepts a feature on the active layer; it stores the
   target id.
4. The message changes to “Haz clic en la entidad de corte”.
5. A second click stores the cutter. Clicking the same feature again warns and
   keeps waiting for a different cutter.
6. The confirmation dialog opens with the picked target/cutter; the user can
   swap them or cancel.
7. `Esc` cancels the pick tool and unchecks the action; stopping editing cancels
   it too.

Picking does not need to modify the layer selection, but the picked features are
validated again when the dialog is accepted.

### Dialog

When the action is triggered, show a compact dialog:

```
┌──────────────────────────────────────────────┐
│ Diferencia de entidades                      │
│                                              │
│ Entidad objetivo: [ fid 3 — …          ▼ ]   │
│ Entidad de corte: [ fid 7 — …          ▼ ]   │
│                                              │
│ ⓘ La entidad objetivo se actualiza; la de    │
│   corte no se modifica.                      │
│                                              │
│              [Cancelar] [Aplicar]            │
└──────────────────────────────────────────────┘
```

- Both combos list the two chosen features (selected or picked), labelled with
  `fid` and a short attribute/display value when available.
- Defaults: for a selection, the first selected feature is the target and the
  second is the cutter; for mouse picking, the first click is the target and the
  second the cutter. The user can swap them with the combos.
- Target and cutter must be different; `Aplicar` is disabled if they match.
- `Cancelar` changes nothing.
- The dialog is available only with exactly two selected features (the action is
  disabled otherwise).

### Apply

1. Read both features from the active layer.
2. `result = target.geometry().difference(cutter.geometry())`.
3. If `result.isEmpty()`: warn
   “La diferencia está vacía; no se modificó la entidad.” and stop.
4. If `not result.isGeosValid()`: warn
   “La geometría resultante no es válida; no se modificó la entidad.” and stop.
5. `beginEditCommand("Freehand Digitize: diferencia de entidades")`;
   `changeGeometry(target_fid, result)`; `endEditCommand`.
6. Repaint and refresh; show an info message.
7. The cutter is never written; the target keeps its attributes.
8. One `Ctrl+Z` restores the target geometry.

---

## 6. Design

### Files

| File | Action | Responsibility |
| :--- | :--- | :--- |
| `gui/difference_dialog.py` | **New** | Two feature combos, swap validation, target/cutter selection. |
| `gui/difference_pick_tool.py` | **New** | Click target, then cutter on the active layer; emits both ids; `Esc` cancels. |
| `gui/difference_creator.py` | **New** | Read features, `difference`, empty/valid checks, edit command. |
| `gui/texts.py` | Modify | Action, dialog, warnings and undo label. |
| `freehand_plugin.py` | Modify | Third action, dialog, selection signals, enablement, cleanup. |
| `tests/integration/test_difference_creator.py` | **New** | Polygon/line/empty/invalid/undo/cutter cases. |
| `tests/integration/test_difference_dialog.py` | **New** | Combo contents, defaults, swap, cancel. |
| `tests/integration/test_plugin.py` | Modify | Action gating, selection updates, end-to-end difference. |
| `tests/test_i18n_catalogs.py` | Modify | Required difference strings. |
| `i18n/freehand_digitize_en.ts/.qm` | Regenerate | New catalogue entries. |
| `scripts/i18n/master_data/en.json` | Modify | Spanish → English translations. |
| `README.md`, `docs/user/USER_GUIDE.md`, `docs/ARCHITECTURE_EN.md`, `CHANGELOG.md`, `metadata.txt` | Modify | Feature docs and metadata. |

### Core model

No new `core/` module is required: `QgsGeometry.difference` is a QGIS operation,
and the selection/edit logic belongs to the GUI layer.

### Plugin wiring

- `self.difference_action`, `self._difference_creator` and
  `self._difference_pick_tool`.
- `_on_difference_triggered`:
  - require `_is_drawable(layer)` (editable line/polygon);
  - if exactly two features are selected, open
    `DifferenceDialog(layer, selected_ids, parent)`;
  - otherwise activate the pick tool and let it collect target/cutter ids;
  - when the pick tool has both ids, open the dialog with them.
- Pick tool:
  - constructed with the canvas and the active layer;
  - first click stores the target; second click stores a different cutter;
  - emits `featuresPicked(target_id, cutter_id)`;
  - `Esc` cancels; the plugin deactivates the tool and unchecks the action.
- `_update_ui_state`: difference action enabled whenever `_is_drawable(layer)`;
  no selection-count gate.
- `editingStopped`: cancels the pick tool and clears its ids.
- `unload`: remove the third action, cancel the pick tool and disconnect its
  signals.

### Geometry checks

- Same-layer means polygon − polygon or line − line; line − polygon and
  polygon − line need a cutter on another layer and are a follow-up.
- Line − line can produce a multiline, which QGIS line layers accept.
- Empty result: keep the target unchanged (do not delete it automatically).
- Invalid result: keep the target unchanged.
- Provider rejection: `destroyEditCommand()` and warn; no partial change.

---

## 7. Tests

### Integration

| Test | Assertion |
| :--- | :--- |
| `test_difference_polygons` | Polygon A minus B updates A's geometry; B and A's attributes unchanged. |
| `test_difference_line_by_line` | Line A minus a line segment yields a multiline and is stored. |
| `test_difference_no_overlap` | Non-overlapping cutter leaves A unchanged but the operation is reported. |
| `test_empty_difference_is_rejected` | Cutter covers A → warning, A unchanged, no undo command. |
| `test_invalid_result_is_rejected` | Invalid result is rejected (mock/forced case), A unchanged. |
| `test_difference_undo` | One undo restores A's original geometry. |
| `test_cutter_is_untouched` | Cutter geometry/attributes are identical after the operation. |
| `test_difference_dialog_defaults` | Target is the first selected, cutter the second. |
| `test_difference_dialog_swap` | Swapping target/cutter updates the selected ids. |
| `test_difference_dialog_rejects_same_feature` | Apply is disabled when both combos match. |
| `test_difference_action_enabled_in_edit_mode` | Enabled with 0 or 1 selected feature; disabled outside edit mode. |
| `test_difference_uses_two_selected_features` | With exactly two selected, the dialog opens directly. |
| `test_difference_pick_target_and_cutter` | Two clicks store target/cutter and open the dialog. |
| `test_difference_pick_same_feature_is_rejected` | Second click on the same feature warns and waits. |
| `test_difference_pick_escape_cancels` | `Esc` unchecks the action and unsets the tool. |
| `test_difference_pick_cancelled_by_editing_stopped` | Stopping editing cancels the pick tool. |
| `test_difference_end_to_end_pick` | Pick target/cutter, accept dialog, target updated. |

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

Context: `FreehandDigitize`. New strings:

| Source (Spanish) | English catalog |
| :--- | :--- |
| `Diferencia de entidades` | `Feature difference` |
| `Selecciona exactamente dos entidades: la objetivo y la de corte.` | `Select exactly two features: the target and the cutter.` |
| `Haz clic en la entidad objetivo.` | `Click the target feature.` |
| `Haz clic en la entidad de corte.` | `Click the cutter feature.` |
| `La entidad de corte debe ser distinta de la objetivo.` | `The cutter feature must be different from the target.` |
| `Entidad objetivo:` | `Target feature:` |
| `Entidad de corte:` | `Cutter feature:` |
| `La entidad objetivo se actualiza; la de corte no se modifica.` | `The target feature is updated; the cutter is not modified.` |
| `La diferencia está vacía; no se modificó la entidad.` | `The difference is empty; the feature was not changed.` |
| `La geometría resultante no es válida; no se modificó la entidad.` | `The resulting geometry is not valid; the feature was not changed.` |
| `La capa «{name}» rechazó la diferencia.` | `Layer “{name}” rejected the difference.` |
| `Freehand Digitize: diferencia de entidades` | `Freehand Digitize: feature difference` |
| `Aplicar` | `Apply` |

Procedure: `make transup` → `make transcompile` → `make i18n-check`; add the
action string to `tests/test_i18n_catalogs.py`.

---

## 9. Versioning

**Decision required.** Recommended: **2.0.0** (unreleased; no tag exists).
Alternative: 2.1.0 if v2.0.0 is considered closed.

Files if a bump is chosen: `metadata.txt`, `pyproject.toml`, `CHANGELOG.md`,
`tests/test_metadata.py`, version headers and `AI_CONTEXT.md`.

---

## 10. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| “Corte” is expected to split into two features | Explicitly document difference vs split; open decision below; a split feature can be a separate plan. |
| Same-layer limitation | Two selected features on the active layer only; cross-layer is a follow-up. |
| Empty result | Keep the target unchanged and warn; never delete silently. |
| Invalid result | Reject before `changeGeometry`. |
| Multipart result | QGIS line layers accept multiline; test; warn if a provider rejects. |
| Selection order is unreliable | Dialog lets the user choose target/cutter instead of relying on order. |
| Selection changes while dialog is open | Validate ids on apply; abort with a warning if a feature disappeared. |
| Mouse pick signal overload differs between PyQt5/PyQt6 | Use the `QgsFeature` overload; fall back to a small `QgsFeatureRequest` query; integration test on both environments. |
| Picking the same feature twice | Warn and keep waiting for a different cutter. |
| Too many features selected | Use the pick tool instead of guessing; with exactly two, use them directly. |
| Provider rejection | `destroyEditCommand`; no partial update. |

---

## 11. Acceptance criteria

- [ ] Action visible and enabled for an editable line/polygon layer.
- [ ] With exactly two selected features, the confirmation dialog opens directly.
- [ ] Without exactly two selected features, clicking the target and cutter on
      the map opens the dialog.
- [ ] Same target/cutter is rejected; `Esc`/stopping editing cancels the pick.
- [ ] Dialog lets the user choose/swap target and cutter.
- [ ] Polygon − polygon updates the target and leaves the cutter untouched.
- [ ] Line − line stores a valid multiline.
- [ ] Empty/invalid results warn and leave the target unchanged.
- [ ] One undo restores the target; attributes are preserved.
- [ ] Spanish/English strings are complete.
- [ ] `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` and
      `make docker-test` pass.
- [ ] The plan is marked `IMPLEMENTED` with the commit hash and results.

---

## 12. Implementation procedure (after approval)

1. Mark this plan `APPROVED` and record the version/scope decisions.
2. Add strings and the `DifferenceDialog`.
3. Add `DifferencePickTool` with click target/cutter, same-feature guard and
   `Esc`.
4. Add `DifferenceCreator` with geometry checks and edit command.
5. Wire the action, pick-tool fallback, dialog, enablement and cleanup in the
   plugin.
6. Add integration tests (creator, dialog, pick tool, plugin).
7. Update the catalog; run `make transup`, `make transcompile`,
   `make i18n-check`.
8. Update README, user guide, architecture, CHANGELOG, metadata and state.
9. Run `make pre-release`, `make zip`, `make security-scan`, `make qt6-check`,
   `make docker-test`.
10. Deploy and smoke-test in QGIS 4; mark the plan `IMPLEMENTED`.

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
- The action is additive; existing create/reshape/sampling behavior is untouched.
- Keep this plan; mark it `REJECTED`/`REVERTED` with the reason.

---

## 15. Results

- `DifferenceDialog`, `DifferencePickTool` and `DifferenceCreator` implemented.
- Two selected features open the dialog directly; otherwise two mouse clicks pick
  target and cutter, then the dialog opens.
- Empty/invalid results are rejected; the cutter is untouched; one undo restores
  the target.
- Tests: 134 total (57 unit + 77 integration), including dialog, pick tool,
  creator and plugin gating.
- `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` and
  `make docker-test` pass; deployed smoke test in QGIS 4 passes.
- **Commit:** to be filled by the integration commit.

---

## 16. Approval

The plan is **PROPOSED**. Implementation starts only after the user confirms:

1. **Operation**: difference (`target = target − cutter`, cutter unchanged,
   one feature) rather than split into two features?
2. **Layers**: same active layer, with mouse picking as the fallback (recommended),
   or cross-layer difference?
3. **Mouse flow**: two clicks (target, cutter) then the confirmation dialog
   (recommended), or apply immediately after the second click?
4. **Empty result**: keep the target unchanged with a warning (recommended), or
   delete the target?
5. **Version**: **2.0.0** (recommended, unreleased) or 2.1.0?

# Implementation Plan — Edit-Session Gating

> **Status: IMPLEMENTED (2026-11-19)** — approved with the sampling plan for
> **v2.0.0**. Implementation follows this plan.
>
> Version: 2.0.0 | Date: 2026-11-19
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Goal

Make the Freehand Digitize tools follow the QGIS edit session:

- the **create** and **reshape** actions are enabled **only** while the active
  line/polygon layer is in edit mode;
- entering edit mode enables them;
- leaving edit mode **cancels any stroke and deactivates the tool**;
- activation **does not auto-start** editing.

The sampling-settings dialog is a configuration action, not a map tool, so it
remains available even when no layer is in edit mode.

---

## 2. Scope and non-goals

### In scope

- Enable/disable the create and reshape actions from `layer.isEditable()`.
- Connect/disconnect the active layer's `editingStarted` and `editingStopped`
  signals.
- Deactivate both tools, uncheck their actions and cancel an in-progress stroke
  when editing stops.
- Remove `startEditing()` calls from the plugin, the map tool, `FeatureCreator`
  and `ReshapeCreator`; require an existing edit session instead.
- Update the tolerance spinbox enablement (only while editing).
- Tests, docs and changelog for the new behaviour.

### Out of scope

- Changing how QGIS starts edit sessions from the layer panel.
- Adding a plugin-specific “start editing” button.
- Per-layer edit state persistence.
- The vertex-sampling feature in
  [PLAN_VERTEX_SAMPLING.md](PLAN_VERTEX_SAMPLING.md); both plans can be
  implemented together, but this one only changes the edit-session gate.

---

## 3. Current state

- `freehand_plugin._is_drawable(layer)` checks validity, line/polygon geometry and
  `supportsEditing()`, but **not** `layer.isEditable()`.
- `_activate_tool()` / `_activate_reshape_tool()` call `_start_editing()`, which
  invokes `layer.startEditing()` automatically.
- `FreehandTool._ensure_editable()` calls `startEditing()` on press.
- `FeatureCreator._ensure_editable()` and `ReshapeCreator._ensure_editable()` also
  start editing.
- The plugin does not connect `editingStarted`/`editingStopped`, so stopping
  editing does not deactivate an active tool.
- The UI guide says “the tool also starts the edit session”.
- Tests assert the auto-start behaviour
  (`test_activate_tool_starts_editing`,
  `test_starts_editing_when_needed`, etc.).

---

## 4. Desired behaviour

| Situation | Expected |
| :--- | :--- |
| Active line/polygon layer is not editable | Create and reshape actions disabled; spinbox disabled. |
| User starts editing the active layer | Actions enabled; no tool is activated automatically. |
| User activates create/reshape while editing | Tool installed; action checked. |
| User stops editing while a tool is active | Stroke cancelled; tool unset; action unchecked; actions disabled. |
| User stops editing with no tool active | Actions disabled; no map-tool change. |
| User changes to a non-editable layer | Active tool unset; actions disabled. |
| User changes to an editable layer | Actions enabled; tool remains unset. |
| Sampling settings action | Remains enabled regardless of edit mode. |
| Press on a non-editable layer (defensive) | Warning; no stroke; no `startEditing()`. |

---

## 5. Design

### Plugin (`freehand_plugin.py`)

- Rename the predicate to `_is_editable_drawable(layer)` and require:
  valid `QgsVectorLayer`, line/polygon, `supportsEditing()`, `layer.isEditable()`.
- Replace `iface.currentLayerChanged.connect(self._update_ui_state)` with
  `_on_current_layer_changed`, which:
  1. disconnects the previous layer's editing signals;
  2. stores the new layer in `self._editing_layer`;
  3. connects `editingStarted` and `editingStopped` for a vector layer;
  4. calls `_update_ui_state()`.
- `_on_editing_started()` → `_update_ui_state()`.
- `_on_editing_stopped()`:
  - cancel strokes on both tools;
  - unset the active tool and uncheck both actions;
  - `_update_ui_state()` (actions/spinbox disabled).
- `_activate_tool()` / `_activate_reshape_tool()`:
  - require `_is_editable_drawable(layer)`;
  - no `startEditing()`;
  - if not editable, uncheck the action, show the “activate editing” warning and
    update the UI.
- Remove `_start_editing()`.
- `_deactivate_tool(cancel_stroke=True)`:
  - cancel both strokes;
  - unset whichever tool is active;
  - uncheck both actions.
- `_update_ui_state()`:
  - `drawable = self._is_editable_drawable(layer)`;
  - actions and spinbox enabled only when drawable;
  - if not drawable and an action is checked, deactivate.
- `_disconnect_signals()` also disconnects the stored `editingStarted` /
  `editingStopped` signals.
- `unload()` clears `_editing_layer`.

### Map tool (`gui/freehand_tool.py`)

- Replace `_ensure_editable()` with `_require_editable()`:
  - `return True` if `layer.isEditable()`;
  - otherwise warn
    “Activa la edición de la capa «{name}» antes de dibujar.” and return `False`.
- No `startEditing()` anywhere in the tool.

### Feature and reshape creators

- `FeatureCreator._ensure_editable()` and `ReshapeCreator._ensure_editable()`:
  - require `layer.isEditable()`;
  - warn if not;
  - never call `startEditing()`.
- The plugin precondition means these warnings are defensive; they also protect
  direct unit/integration calls.

### Signal lifecycle

```
iface.currentLayerChanged
        │
        ▼
_on_current_layer_changed
  disconnect old editingStarted/editingStopped
  connect new layer
  _update_ui_state
        │
        ├── editingStarted  → _update_ui_state (enable)
        └── editingStopped  → cancel strokes → unset tool → uncheck → update (disable)
```

`self._editing_layer` keeps the layer whose signals are connected so they can be
disconnected on layer change and unload.

---

## 6. Tests

### Integration (`tests/integration`)

| Test | Assertion |
| :--- | :--- |
| `test_actions_disabled_when_layer_is_not_editable` | Create/reshape disabled before `startEditing()`. |
| `test_actions_enabled_when_editing_starts` | `layer.startEditing()` enables both actions and the spinbox. |
| `test_actions_disabled_when_editing_stops` | `layer.commitChanges()`/`rollBack()` disables both and the spinbox. |
| `test_activation_does_not_start_editing` | Triggering the action without an edit session leaves the layer non-editable, action unchecked and shows a warning. |
| `test_editing_stopped_deactivates_tool_and_cancels_stroke` | Start a stroke, stop editing; canvas tool is unset, actions unchecked and no feature is created. |
| `test_layer_change_reconnects_editing_signals` | Editing layer A no longer affects the UI after switching to B. |
| `test_editing_stopped_keeps_sampling_settings_enabled` | Sampling action remains enabled (when implemented). |
| Update `test_end_to_end_stroke_creates_a_feature` | Start editing explicitly before activating; feature still created. |
| Update `test_end_to_end_reshape` | Start editing explicitly; reshape still works. |

### Creator/tool tests

- `FeatureCreator`: remove “starts editing” expectation; add
  `test_rejects_non_editable_layer`; start editing in the success tests.
- `ReshapeCreator`: same; the helpers start editing where needed.
- `FreehandTool`: start editing in `setUp` for drawing tests; add
  `test_press_without_edit_session_warns_and_emits_nothing`.

Run:

```bash
make test
make test-qgis
make docker-test
```

---

## 7. i18n

Context: `FreehandDigitize`. New/changed source strings:

| Source (Spanish) | English catalog |
| :--- | :--- |
| `Activa la edición de la capa «{name}» antes de dibujar.` | `Start editing layer “{name}” before drawing.` |
| `La capa activa no está en edición.` (optional dialog/tooltip) | `The active layer is not in edit mode.` |

The existing “Select an editable line or polygon vector layer before drawing.”
tooltip stays valid; the docs will explain that the layer must be in edit mode.

Procedure: `make transup` → `make transcompile` → `make i18n-check`.

---

## 8. Versioning

**Decision required.** Recommended: **2.0.0** (unreleased; no tag). Alternative:
2.1.0 if v2.0.0 is closed.

Files if a bump is chosen: `metadata.txt`, `pyproject.toml`, `CHANGELOG.md`,
`tests/test_metadata.py`, version headers and `AI_CONTEXT.md`.

---

## 9. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| Users accustomed to auto-start see disabled actions | Document “start editing first”; clear tooltip and warning; changelog entry. |
| Tool stays active after `commitChanges()` | Connect `editingStopped`; test commit and rollback. |
| Stroke in progress when editing stops | Cancel both tools before unsetting; test. |
| Editing signals connected twice after layer changes | Disconnect the previous `_editing_layer`; test A→B→A. |
| Fake/test layers lack editing signals | Guard with `isinstance(layer, QgsVectorLayer)` and `getattr`; tests use real memory layers. |
| Modal form and editing state | Feature form still runs inside the edit session; no change. |
| Sampling feature interaction | Sampling settings action stays independent; map tools gated. |

---

## 10. Acceptance criteria

- [ ] Create/reshape actions are disabled when the active line/polygon layer is
      not in edit mode.
- [ ] Starting editing enables them; stopping editing disables them.
- [ ] Stopping editing deactivates an active tool, unchecks its action and
      cancels an in-progress stroke.
- [ ] Activating a tool never calls `startEditing()`.
- [ ] Pressing on a non-editable layer warns and creates/reshapes nothing.
- [ ] The sampling settings action remains available.
- [ ] Existing creation and reshape flows work when editing is active.
- [ ] `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` and
      `make docker-test` pass.
- [ ] The plan is marked `IMPLEMENTED` with the commit hash and results.

---

## 11. Implementation procedure (after approval)

1. Mark this plan `APPROVED` and record the version decision.
2. Update `_is_editable_drawable`, `_update_ui_state`, activation and unload.
3. Add `_on_current_layer_changed`, `_on_editing_started`,
   `_on_editing_stopped` and the editing-signal disconnect helper.
4. Remove `startEditing()` from the plugin, tool, `FeatureCreator` and
   `ReshapeCreator`; add the warning string.
5. Update tests (plugin, tool, creators) and add the new gating tests.
6. Update `gui/texts.py`/catalog; run `make transup`, `make transcompile`,
   `make i18n-check`.
7. Update README, user guide, architecture, CHANGELOG, metadata and state.
8. Run `make pre-release`, `make zip`, `make security-scan`, `make qt6-check`,
   `make docker-test`.
9. Deploy and smoke-test in QGIS 4; mark the plan `IMPLEMENTED`.

---

## 12. Verification commands

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

## 13. Rollback

- Revert the feature commit(s) with `git revert <sha>`.
- Restore the auto-start behavior only if the product decision changes; the
  plan records the trade-off.
- Keep this plan; mark it `REJECTED`/`REVERTED` with the reason.

---

## 14. Results

- Create/reshape actions now require `layer.isEditable()`; the plugin no longer
  calls `startEditing()`.
- `editingStarted`/`editingStopped` are connected per active layer; stopping
  editing cancels the stroke, unsets the tool and unchecks the actions.
- `SamplingDialog`/sampling action remains available outside edit mode.
- Tests: 117 total (57 unit + 60 integration), including the new gating cases.
- `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` and
  `make docker-test` pass; deployed smoke test in QGIS 4 passes.
- **Commit:** to be filled by the integration commit.

---

## 14. Approval

The plan is **PROPOSED**. Implementation starts only after the user confirms:

1. **Behaviour**: actions disabled outside edit mode; stopping editing cancels
   the stroke and deactivates the tool (recommended). Is that correct?
2. **Sampling settings**: keep the settings dialog available outside edit mode
   (recommended)?
3. **Version**: **2.0.0** (recommended, unreleased) or 2.1.0?
4. **Interaction with the sampling plan**: implement both together after
   approval, or gate editing first and sampling afterwards?

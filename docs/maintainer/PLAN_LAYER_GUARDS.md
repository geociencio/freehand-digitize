# Implementation Plan — Deleted-Layer Guards (P1)

> **Status: IMPLEMENTED (2026-11-21), retained by the user.** 2.0.2 was
> implemented before explicit plan approval and the user chose to keep it.
> Portal 2.0.2 upload waits for 2.0.1 approval.
>
> **Process note:** “create the plan” is not implementation approval; the next
> plan must stop after PROPOSED and wait.
>
> Target version: **2.0.2** (patch) | Date: 2026-11-21
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Problem

2.0.1 fixed the plugin's editing-signal lifecycle, but other paths still access
a `QgsVectorLayer` after its C++ object has been destroyed:

```text
RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
```

The repository analysis (`docs/maintenance/analysis_2026-11-21_repository.md`)
reproduced it with `sip.delete(layer)` on:

- `FeatureCreator.create`;
- `ReshapeCreator.reshape`;
- `FreehandTool` press/move/release;
- plugin completion callbacks (`_on_geometry_finished`,
  `_on_reshape_finished`, `_open_difference_dialog`).

The normal GUI path rarely deletes a layer mid-stroke, but the fix is incomplete:
`_ensure_editable` / `_require_editable` call `layer.isEditable()` and
`layer.name()` without checking `sip.isdeleted`.

---

## 2. Goal

Make every user-facing creation/editing path fail **cleanly** when its layer no
longer exists:

- no unhandled `RuntimeError`;
- a translated warning;
- no partial feature/geometry/edit command;
- the stroke/tool is cancelled and the UI returns to a safe state.

---

## 3. Design

### Shared helper

Add `gui/layer_utils.py`:

```python
from qgis.PyQt import sip

def is_layer_alive(layer) -> bool:
    if layer is None:
        return False
    try:
        return not sip.isdeleted(layer)
    except (AttributeError, RuntimeError, TypeError):
        return False
```

Move the plugin's `_is_layer_alive` to this module and import it in
`freehand_plugin.py`, `FeatureCreator`, `ReshapeCreator` and `FreehandTool`.
No QGIS import in `core/`.

### `FeatureCreator`

- `create`: return `False` with a warning if the layer is not alive before
  touching it.
- `_ensure_editable`: same guard.
- Wrap the edit sequence (`beginEditCommand`, `createFeature`, form, `addFeature`,
  `endEditCommand`) so a `RuntimeError` from a layer deleted mid-operation logs
  and destroys the edit command; never leave an open command.
- The attribute form may outlive the layer; catch its failure path.
- No feature count change when the layer is gone.

### `ReshapeCreator`

- `reshape`: guard before `asPolyline`, `_candidates`, `_ensure_editable` and
  `_apply`.
- `_candidates`/`_apply`: if the layer dies mid-operation, restore already
  changed features where possible, `destroyEditCommand`, warn and return
  `False`.
- Empty/invalid behavior unchanged.

### `FreehandTool`

- `_require_editable`: check `is_layer_alive` before `isEditable`/`name`.
- `canvasPressEvent`: if the active layer disappeared, warn and return.
- `canvasMoveEvent`/`canvasReleaseEvent`: if the captured layer is no longer
  alive, cancel the stroke, clear the rubber band, emit nothing and keep the
  plugin usable.
- No access to `layer.geometryType()` or `toLayerCoordinates` on a dead wrapper.

### Plugin completion callbacks

- `_on_geometry_finished` / `_on_reshape_finished`: if the layer is not alive,
  warn and return (and uncheck/deactivate the relevant action).
- `_open_difference_dialog`: guard the layer before constructing the dialog.
- Existing `_on_editing_layer_destroyed` remains.

### i18n

Add one string:

| Spanish source | English catalog |
| :--- | :--- |
| `La capa ya no está disponible; se canceló la operación.` | `The layer is no longer available; the operation was cancelled.` |

Use it in the creators/tool/plugin guards. Run `make transup`, `make
transcompile`, `make i18n-check`.

---

## 4. Tests

All new tests are integration tests (need `sip.delete`).

| Test | Assertion |
| :--- | :--- |
| `test_feature_creator_rejects_deleted_layer` | `sip.delete(layer)` → `create()` returns `False`, warning, no exception. |
| `test_reshape_creator_rejects_deleted_layer` | `reshape()` returns `False`, warning, no exception. |
| `test_tool_press_after_layer_deleted` | Press/move/release emits nothing and cancels safely. |
| `test_plugin_geometry_finished_with_deleted_layer` | Completion callback warns and does not insert. |
| `test_plugin_reshape_finished_with_deleted_layer` | Completion callback warns and does not modify. |
| `test_difference_dialog_with_deleted_layer` | Dialog is not opened; warning shown. |

The deleted-layer tests must clear canvas layers and unset map tools before
`sip.delete` (the 2.0.1 tests already do this) to avoid Qt teardown double frees.

Expected counts:

- `make test`: 145 tests (57 unit + 88 skipped).
- `make test-qgis`: 88 tests (86 integration + gate? recount at implementation).
- `make docker-test`: same integration count with `REQUIRE_QGIS=1`.

---

## 5. Versioning and release

**2.0.2 patch**:

- `metadata.txt`, `pyproject.toml`, `CHANGELOG.md`, `tests/test_metadata.py`;
- GitHub Release and tag `v2.0.2`;
- deploy to QGIS 4;
- **portal sequencing**: 2.0.1 is uploaded and pending approval. Wait for its
  approval before uploading 2.0.2, or ask the portal maintainers whether 2.0.2
  supersedes the pending 2.0.1. Do not upload 2.0.2 blindly while 2.0.1 is in
  review.

No plugin behavior changes beyond the guards and warning.

---

## 6. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| `sip` import differs Qt5/Qt6 | `from qgis.PyQt import sip`; test in the Qt5 container. |
| Layer dies mid-edit | Catch `RuntimeError`; destroy the edit command; warn; no partial change. |
| Form modal during deletion | Catch form failure; return `False`; no addFeature. |
| Double cleanup/tests | Clear canvas and map tool before `sip.delete`; reuse the 2.0.1 test helper. |
| Portal version overlap | Upload 2.0.2 only after 2.0.1 approval or explicit maintainer guidance. |
| False-green regression | The new `REQUIRE_QGIS=1` gate protects both suites. |

---

## 7. Acceptance criteria

- [ ] Deleting a layer does not raise from `FeatureCreator`, `ReshapeCreator`,
      `FreehandTool` or plugin completion callbacks.
- [ ] A translated warning is shown; no feature/geometry is written.
- [ ] Existing 2.0.1 lifecycle tests still pass.
- [ ] `make test`, `make test-qgis`, `make docker-test`, `make pre-release`,
      `make zip`, `make security-scan`, `make qt6-check` pass.
- [ ] CI green with the gate active.
- [ ] 2.0.2 version metadata is consistent.
- [ ] Portal sequence is respected (2.0.1 approval first).

---

## 8. Procedure

1. Mark this plan `APPROVED`.
2. Add `gui/layer_utils.py` and the translated warning.
3. Guard `FeatureCreator`, `ReshapeCreator`, `FreehandTool` and the plugin
   callbacks.
4. Add the integration tests; update counts/metrics.
5. Bump to 2.0.2; update CHANGELOG/metadata.
6. Run all gates; deploy; tag/release 2.0.2.
7. Upload 2.0.2 after 2.0.1 portal approval.

---

## 9. Results

- Added `gui/layer_utils.py` (`is_layer_alive`) and the translated
  `layer_gone_text` warning.
- Guarded `FeatureCreator`, `ReshapeCreator`, `FreehandTool` and plugin
  completion callbacks.
- Added 6 integration tests using a deleted `QObject` (safe teardown); the
  existing 2.0.1 tests still cover real `QgsVectorLayer` deletion.
- Tests: 145 total (57 unit + 88 integration incl. gate).
- `make test-qgis` and `make docker-test`: 88 OK; `make pre-release`: OK.
- **Commit:** `ea943a2 fix: guard remaining deleted-layer paths`.

---

## 10. Approval

The plan is **PROPOSED**. Implementation starts only after the user confirms:

1. **Version**: 2.0.2 patch (recommended) or fold into a later feature release?
2. **Portal**: wait for 2.0.1 approval before uploading 2.0.2 (recommended)?
3. **Scope**: guard all creators/tool/plugin paths, not just the callbacks?

# Implementation Plan — Deleted-Layer Lifecycle Fix

> **Status: IMPLEMENTED (2026-11-21)** — approved and implemented as **2.0.1**.
> The 2.0.1 portal upload waits for the 2.0.0 approval status.
>
> Target version: 2.0.1 (patch) | Date: 2026-11-21
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Problem

QGIS raises a Python exception when the active vector layer is deleted while the
plugin still holds a reference to it:

```text
RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
  freehand_plugin.py, line 473, in _on_current_layer_changed
  freehand_plugin.py, line 487, in _disconnect_editing_signals
    self._disconnect(layer.editingStarted, self._on_editing_started)
```

The plugin stores `self._editing_layer` to disconnect `editingStarted` /
`editingStopped` when the active layer changes. QGIS may destroy the layer before
`currentLayerChanged` delivers the new/empty layer; reading `layer.editingStarted`
on the dead wrapper raises `RuntimeError` **before** `_disconnect()` can catch
anything, because `_disconnect` only guards `signal.disconnect()`.

---

## 2. Evidence (QGIS 4.2.2)

Reproduction in an ephemeral script:

```python
from qgis.PyQt import sip
layer = QgsVectorLayer("LineString?crs=EPSG:4326", "l", "memory")
layer.destroyed.connect(...)
sip.delete(layer)
sip.isdeleted(layer)        # True
layer.editingStarted        # RuntimeError: wrapped C/C++ object ... deleted
```

- `destroyed` is emitted when the C++ object is deleted.
- `sip.isdeleted(layer)` reliably identifies the dead wrapper.
- The same pattern exists in the plugin's `_disconnect_editing_signals`.

---

## 3. Fix design

### `freehand_plugin.py`

1. Import the binding's SIP module:
   ```python
   from qgis.PyQt import sip
   ```
2. Add a small helper:
   ```python
   @staticmethod
   def _layer_alive(layer) -> bool:
       if layer is None:
           return False
       try:
           return not sip.isdeleted(layer)
       except (AttributeError, RuntimeError, TypeError):
           return False
   ```
3. `_disconnect_editing_signals()`:
   - take the stored layer into a local, set `self._editing_layer = None` **first**;
   - return if not `_layer_alive(layer)`;
   - wrap both signal accesses/disconnects in `try/except (RuntimeError, TypeError)`;
   - never leave a dead reference behind.
4. `_on_current_layer_changed()`:
   - normalize a deleted active layer to `None`;
   - compare the live layer with `_editing_layer` only after the alive check;
   - connect editing signals only if the layer is alive;
   - connect `layer.destroyed` to `_on_editing_layer_destroyed`.
5. `_on_editing_layer_destroyed()`:
   - clear `_editing_layer`;
   - if the destroyed layer was the difference pick layer, deactivate the pick;
   - call `_update_ui_state()`.
6. Defensive guards:
   - `_update_ui_state()`, `_activation_warning()`, `_effective_tolerance()` and
     `_is_geographic()` should treat dead layers as `None`;
   - `unload()` must survive a layer destroyed before the plugin.
7. No change to the map tool's normal drawing path.

### Why not only a broad `try/except`?

A broad catch around `_disconnect_editing_signals` would hide the symptom but
keep a dead reference and repeat the error on unload. Clearing the reference
first, checking `sip.isdeleted`, and reacting to `destroyed` fixes the lifecycle.

---

## 4. Tests

### Integration

| Test | Assertion |
| :--- | :--- |
| `test_deleted_active_layer_does_not_raise` | `sip.delete(layer)` then `_on_current_layer_changed()`; no exception, `_editing_layer is None`, actions disabled. |
| `test_unload_after_layer_deleted` | Delete the layer, then `plugin.unload()`; no exception. |
| `test_destroyed_signal_clears_editing_layer` | `sip.delete(layer)`; the `destroyed` slot clears the reference. |
| `test_live_layer_still_receives_editing_signals` | Existing behavior: start/stop editing still updates actions. |
| `test_difference_pick_cancelled_when_layer_deleted` | Delete a layer used by the pick tool; pick tool is cleaned up. |

Run:

```bash
make test
make test-qgis
make docker-test
```

### Static/i18n

No new user-facing strings are required; run the standard gates.

---

## 5. Versioning

Patch release **2.0.1**:

- `metadata.txt`: version `2.0.1` + changelog bullet;
- `pyproject.toml`: version `2.0.1`;
- `CHANGELOG.md`: `## 2.0.1 — 2026-11-20` with the crash fix;
- `tests/test_metadata.py`: expected version;
- README/user guide: no feature change required; mention the fix in the changelog.

The 2.0.0 portal upload remains pending approval. The plan recommends:
1. fix and deploy 2.0.1 locally;
2. publish the GitHub patch release;
3. upload 2.0.1 to the portal only after checking the 2.0.0 approval status, to
   avoid replacing a submission that is still in review.

---

## 6. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| `sip` import differs PyQt5/PyQt6 | Use `from qgis.PyQt import sip`; test in the Qt5 container. |
| `destroyed` slot receives a deleted object | The slot only clears state; it does not access the C++ object. |
| Layer destroyed while a stroke is active | `_on_editing_layer_destroyed` deactivates the difference pick; the tool's own cancel path is already guarded. |
| Signals disconnected twice | `_disconnect` ignores `TypeError`/`RuntimeError`; reference is cleared first. |
| Hiding a real bug with broad catches | Guards are narrow (`sip.isdeleted` / signal access) and covered by tests. |
| Version 2.0.1 vs pending 2.0.0 | Do not overwrite the portal submission until its status is known; GitHub patch can be published independently. |

---

## 7. Acceptance criteria

- [ ] Deleting the active layer no longer raises `RuntimeError`.
- [ ] `_editing_layer` is cleared when the layer is destroyed.
- [ ] Plugin unload works after the layer is deleted.
- [ ] Live layers still connect/disconnect editing signals correctly.
- [ ] The difference pick tool is cancelled if its layer is destroyed.
- [ ] `make pre-release`, `make test-qgis`, `make docker-test`, `make zip`,
      `make security-scan` and `make qt6-check` pass.
- [ ] Version 2.0.1 is consistent in metadata/pyproject/CHANGELOG/tests.

---

## 8. Procedure

1. Mark this plan `APPROVED`.
2. Add `sip`/`_layer_alive`, the destroyed slot, and the guarded disconnect.
3. Add lifecycle integration tests.
4. Bump to 2.0.1; update changelog and metadata.
5. Run all gates; deploy to QGIS 4; smoke-test deleting a layer.
6. Commit, tag `v2.0.1`, GitHub Release; portal upload after checking 2.0.0.

---

## 8. Results

- Added `sip.isdeleted`-based guards and a `_layer_alive` helper.
- `_disconnect_editing_signals` clears the reference before disconnecting and
  catches dead-object access.
- `destroyed` is connected per active layer and clears the reference/tools.
- Added 4 integration tests (deleted active layer, stale reference, unload,
  difference pick).
- Tests: 138 total (57 unit + 81 integration); QGIS 4.2.2 and Qt5 container.
- **Commit:** to be filled by the fix commit.

---

## 9. Approval

The plan is **PROPOSED**. Implementation starts only after the user confirms:

1. Fix as a **2.0.1 patch** (recommended) or commit without a version bump?
2. Publish `v2.0.1` on GitHub now, but wait for the 2.0.0 portal approval before
   uploading 2.0.1?

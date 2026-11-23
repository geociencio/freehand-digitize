# Implementation Plan — Snapping and Difference Pick Fixes

> **Status: PROPOSED** — no code changes until the user approves.
>
> Target: **2.1.0** (with the already-unreleased i18n work) | Date: 2026-11-22
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Evidence

The manual review in
[analysis_2026-11-22_code_review.md](../maintenance/analysis_2026-11-22_code_review.md)
found two user-visible defects that the current suite misses.

### 1.1 Terminal Ctrl snapping is silently dropped

`canvasReleaseEvent` calls `_add_release_point`; that method calls
`StrokeRecorder.add`, which applies the normal sampling threshold. If the user
stops the cursor before releasing, the release device point equals the last
recorded device point (distance `0`), so the snapped point is rejected.

Result: the first vertex snaps, but the **last** vertex does not.

Existing test `test_ctrl_snaps_the_first_vertex` only covers the first vertex.

### 1.2 Difference pick rejects edit-buffer features

`DifferencePickTool._on_feature_identified` returns for `feature_id <= 0`.
Features added to the edit buffer before commit can have negative IDs, and some
formats use `fid == 0`. Those features cannot be selected as target/cutter.

Result: a user digitizes two polygons and cannot difference them until saving.

---

## 2. Scope

### A. Terminal snapping

Add a final-point path to `StrokeRecorder` that bypasses the sampling threshold
without bypassing the maximum point cap:

```python
def add_final(self, layer_point, device_point) -> bool:
    """Append the final vertex even when it is inside the sampling threshold."""
```

Rules:

- reject when `len >= max_points`;
- reject exact duplicate layer coordinates;
- otherwise append and update `_last_device` / `_last_layer`.

`FreehandTool._add_release_point` uses `add_final`, not `add`.
Normal `canvasMoveEvent` keeps using `add` and its distance threshold.
When the release point is identical to the previous layer point, no duplicate
is appended and the rubber band is unchanged.

### B. Difference pick IDs

- Remove the arbitrary `feature_id <= 0` guard.
- For a `QgsFeature`, require `feature.isValid()`; accept any valid integer ID,
  including `0` and negatives.
- For an integer payload, accept any integer, including `0`/negative; invalid
  feature retrieval is handled by `DifferenceCreator`.
- Add an integration test that creates features inside an edit session, verifies
  their IDs, and picks them.
- If `layer.getFeature(negative_id)` does not resolve the edit-buffer feature,
  add a small helper in `DifferenceCreator` that resolves the feature from
  `layer.editBuffer().addedFeatures()` before failing. The test decides whether
  this fallback is required; do not add it speculatively.

### C. No-overlap difference

`DifferenceCreator.apply` currently treats a non-intersecting cutter as a
successful no-op: it opens/ends an edit command and reports “applied”.

Add:

```python
if not target.geometry().intersects(cutter.geometry()):
    self._info(no_overlap_text())
    return False
```

- No edit command when there is no intersection.
- Target geometry unchanged.
- New translated string in `gui/texts.py`:
  “The cutter does not intersect the target; the feature was not changed.”
- Update `master_data` for `es`, `pt_BR`, `fr`, `de`, `it`, `id`; compile catalogs.

The existing `test_difference_without_overlap` changes from `assertTrue` to
`assertFalse` and asserts no undo entry.

### D. Display labels in the difference dialog

`DifferenceDialog._feature_label` currently uses the first non-empty text field.
Prefer the layer display expression/field:

1. `layer.displayExpression()` if non-empty and evaluates;
2. `layer.displayField()` if non-empty;
3. first non-empty text field as fallback;
4. `Feature <id>` last.

No new string unless the fallback label is introduced; keep “Feature {id}” out
of scope unless needed.

### E. Test maintenance

- Replace deprecated `QgsGeometry.isGeosEqual()` in
  `tests/integration/test_difference_creator.py` with
  `isTopologicallyEqual()` (QGIS 4.2+).
- Add unit tests for `StrokeRecorder.add_final` and integration tests for
  terminal snapping, negative/zero FID picking, no-overlap and display labels.

---

## 3. Tests

| Test | Assertion |
| :--- | :--- |
| `test_add_final_bypasses_pixel_threshold` | final point added when closer than 1.5 px |
| `test_add_final_rejects_exact_duplicate` | no duplicate layer point |
| `test_add_final_respects_max_points` | cap still enforced |
| `test_ctrl_snaps_the_last_vertex` | release on a vertex snaps the last geometry point |
| `test_ctrl_release_same_device_point_keeps_snap` | stopped cursor still snaps |
| `test_pick_edit_buffer_negative_fid` | target/cutter with negative IDs emit pair |
| `test_pick_zero_fid` | `0` is accepted when valid |
| `test_pick_invalid_feature_is_ignored` | invalid feature emits nothing |
| `test_difference_without_overlap_does_not_edit` | `False`, unchanged, no undo entry |
| `test_difference_dialog_uses_display_expression` | label comes from display expression |

Expected count: **~160 tests**; recalculate after implementation.

---

## 4. Version and release

- No version bump in this plan.
- The fixes join the already-unreleased **2.1.0** (English i18n base + six
  catalogs).
- Release remains gated: 2.0.1 portal approval → upload 2.0.2 → 2.0.2 approval →
  2.1.0 tag/ZIP/notes.
- If the user wants a patch before i18n, the alternative is **2.0.3** on GitHub;
  do not move the published 2.0.2 tag.

---

## 5. Risks

| Risk | Mitigation |
| :--- | :--- |
| Negative IDs are not retrievable with `getFeature` | Test first; use edit-buffer fallback only if the test proves it is needed. |
| Final point duplicates the last vertex | `add_final` rejects exact layer duplicates. |
| Snapping no longer works when Ctrl is released late | The release path is independent of the move threshold. |
| No-overlap check changes existing behavior | Update the existing test and assert no undo entry. |
| Display expression evaluation fails | Fall back to display field, text field, then ID. |
| i18n catalogs drift | `make transup`, `transcompile`, `i18n-check`; six catalogs must stay complete. |
| Current 2.0.2 artifact changes | Do not tag/build 2.0.2 from this work; 2.1.0 only. |

---

## 6. Acceptance criteria

- [ ] Last vertex snaps with Ctrl even when the cursor stopped before release.
- [ ] Edit-buffer/negative/zero IDs can be picked and differenced.
- [ ] Non-overlapping difference returns `False`, changes nothing and creates no
      undo entry.
- [ ] Display labels prefer the layer display expression/field.
- [ ] All new tests pass in QGIS 4.2.2 and the Qt5 container.
- [ ] Six catalogs remain complete.
- [ ] `make pre-release`, Docker, security and Qt6 pass.
- [ ] No tag/release/portal upload in this plan.

---

## 7. Procedure

1. Add the failing tests for terminal snapping and negative/zero FIDs.
2. Implement `add_final` and the release-path change.
3. Implement the pick-ID fix; verify whether edit-buffer fallback is needed.
4. Add the no-overlap guard and translated string.
5. Implement display-expression labels.
6. Replace deprecated geometry comparisons.
7. Run `make transup`, `transcompile`, `i18n-check`, `make pre-release`,
   `make docker-test`.
8. Update the plan with results and commit.

---

## 8. Approval

The plan is **PROPOSED**. It starts only after the user approves:

1. Terminal snap fix with `StrokeRecorder.add_final`.
2. Accept valid negative/zero FIDs, with test-driven edit-buffer fallback.
3. No-overlap difference as a non-edit with warning/info.
4. Display-expression labels and test cleanup.
5. Join the unreleased 2.1.0, no tag yet.

Do you approve this plan?

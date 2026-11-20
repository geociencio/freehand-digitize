# Implementation Plan — Staged Editing Features

> **Status: APPROVED (roadmap only)** — approved by the user on 2026-11-20.
> **No stage has started**; each stage requires an explicit kickoff. Code remains
> at v2.0.0.
>
> Version target: 2.1.0 (quick wins), 2.2.0 (geometry editing), 2.3.0 (overlap
> guard) | Date: 2026-11-20
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Goal

Add the researched features in small, independently releasable stages. Each stage
must be useful on its own, keep the plugin dependency-free (QGIS/PyQt only), and
pass the full quality gates before moving on.

The roadmap deliberately puts the cheap, low-risk improvements first and the
geometry-editing operations later. A stage can be dropped without blocking the
others.

---

## 2. Stages at a glance

| Stage | Feature | Release | Effort | Risk |
| :---: | :--- | :---: | :---: | :---: |
| 1 | Backspace removes the last vertex | 2.1.0 | S (2–4 h) | Low |
| 2 | Live vertex counter | 2.1.0 | S (2–3 h) | Low |
| 3 | Optional stroke smoothing | 2.1.0 | S/M (4–6 h) | Medium |
| 4 | Pause/resume a stroke | 2.1.0 | S (3–4 h) | Low |
| 5 | Shortcuts + always-snap option | 2.1.0 | S (3–4 h) | Medium |
| — | **Release 2.1.0 gate** | | | |
| 6 | Live length/area | 2.2.0 | M (1–2 d) | Medium |
| 7 | Split a feature with a stroke | 2.2.0 | M/L (2–3 d) | High |
| 8 | Add a ring/hole to a polygon | 2.2.0 | M (1–2 d) | Medium |
| 9 | Add a part to a multipart feature | 2.2.0 | M (1–2 d) | Medium |
| — | **Release 2.2.0 gate** | | | |
| 10 | Overlap guard for new features | 2.3.0 | M (2–3 d) | Medium |

Effort is indicative; the actual estimate is refined at each stage kickoff.

---

## 3. Stage 1 — Backspace removes the last vertex

### Goal

While drawing, `Backspace` removes the last recorded vertex and the corresponding
rubber-band point, without cancelling the stroke.

### UX

- Works in create and reshape modes.
- If only one vertex remains, `Backspace` cancels the stroke (same as `Esc`).
- `Esc` keeps cancelling the whole stroke.

### Design

| File | Change |
| :--- | :--- |
| `core/stroke.py` | Add `pop_last()`; keep a parallel `_devices` list so the sampling threshold uses the new last point. |
| `gui/qt_compat.py` | Add `KEY_BACKSPACE` (Qt5/Qt6). |
| `gui/freehand_tool.py` | Handle `KEY_BACKSPACE` while drawing; call `pop_last()` and `QgsRubberBand.removeLastPoint()`; refresh. |
| `tests/core/test_stroke.py` | Pop updates points and the last device/layer point. |
| `tests/integration/test_freehand_tool.py` | Backspace removes a vertex; one-vertex Backspace cancels. |

### Risks and acceptance

- Qt may route Backspace to the canvas; the tool consumes it while drawing.
- No new strings (or one status message if added).
- Gate: `make pre-release`; test on QGIS 4 and the Qt5 container.

---

## 4. Stage 2 — Live vertex counter

### Goal

Show the current vertex count while drawing, so the user can see the sampling
effect in real time.

### UX

- Status bar message: `"N vértices"` while drawing.
- Cleared on release, cancel and tool deactivation.
- No setting; always on.

### Design

| File | Change |
| :--- | :--- |
| `gui/freehand_tool.py` | `_update_status()` after start/add/pop; `_clear_status()` on finish/cancel/deactivate. |
| `tests/integration/fakes.py` | Add a minimal `statusBarIface()` with `showMessage`/`clearMessage`. |
| `gui/texts.py` | `"N vértices"` + English catalog. |
| Tests | Status appears after moves, updates after Backspace, clears on release. |

### Risks and acceptance

- Guard a missing/limited status bar with `getattr`/`try`.
- No performance concern: one message per recorded vertex.
- Gate: no regression in drawing; i18n check.

---

## 5. Stage 3 — Optional stroke smoothing

### Goal

Optionally smooth the finished geometry before validation/insertion. Off by
default; applies only to new features.

### UX

- In **Configuración de trazo** (the existing sampling dialog, renamed):
  - checkbox **Suavizar trazo**;
  - iterations `1–5` (default 2), disabled when unchecked.
- Applies after simplification and before validity checks.
- Reshape/difference are not smoothed in this stage.

### Design

| File | Change |
| :--- | :--- |
| `core/constants.py` | `SMOOTH_ENABLED_KEY`, `SMOOTH_ITERATIONS_KEY`, defaults/ranges. |
| `core/settings.py` | `SmoothingStore` (or extend the settings store) with enabled/iterations. |
| `gui/feature_creator.py` | After simplify: `QgsGeometry.smooth(iterations, 0.25)` when enabled; reject empty/invalid results; log failures. |
| `gui/sampling_dialog.py` | Add the smoothing group; rename the dialog title to **Configuración de trazo**; keep sampling controls. |
| Tests | Smoothing off preserves geometry; on changes it and remains valid; invalid fallback; dialog values; i18n. |

API evidence: `QgsGeometry.smooth(iterations, offset)` exists in QGIS 4.2.2 and
returns valid line/polygon geometries in the prototype.

### Risks and acceptance

- Smoothing changes shape (rounds corners); default off, documented.
- Do not smooth invalid input silently; validate after smoothing.
- If smoothing returns invalid/empty, abort with a warning and keep the original.
- Gate: feature creator tests, ZIP, i18n.

---

## 6. Stage 4 — Pause/resume a stroke

### Goal

Let the user pause recording, reposition the pointer, and resume without adding
vertices for the movement.

### UX

- `P` toggles pause while drawing.
- Status message: “Trazo pausado” / “Trazo reanudado”.
- Moves while paused do not add vertices.
- Release while paused finishes with the already-recorded points; `Esc` cancels.

### Design

| File | Change |
| :--- | :--- |
| `gui/qt_compat.py` | `KEY_P` constant. |
| `gui/freehand_tool.py` | `_paused` state; ignore `add()` while paused; toggle in `keyPressEvent`; status message. |
| Tests | Paused moves are not recorded; resume records; release finishes; `Esc` cancels. |
| i18n | Pause/resume strings. |

This addresses the upstream “Pausing” request:
<https://github.com/vinayan/freehandEditing/issues/5>.

### Risks and acceptance

- `P` must not conflict with QGIS; verify and document.
- Pausing does not move the existing last vertex; only suppresses new points.
- Gate: integration tests in both environments.

---

## 7. Stage 5 — Shortcuts and always-snap

### Goal

Reduce mouse travel and make snapping usable without holding `Ctrl`.

### UX

- Actions get shortcuts (candidate: `Ctrl+Alt+C` create, `Ctrl+Alt+R` reshape,
  `Ctrl+Alt+D` difference, `Ctrl+Alt+S` settings). Verify against QGIS
  defaults and change if they conflict.
- In **Configuración de trazo**: checkbox **Ajustar siempre**.
- When enabled, the first/last vertex snapping runs without `Ctrl`; `Ctrl` still
  works when disabled.

### Design

| File | Change |
| :--- | :--- |
| `freehand_plugin.py` | Assign `QKeySequence` shortcuts to the actions; tooltip shows them. |
| `core/constants.py` / `core/settings.py` | `ALWAYS_SNAP_KEY` and store. |
| `gui/freehand_tool.py` | `_should_snap = always_snap or _ctrl_pressed`; read the setting at press. |
| `gui/sampling_dialog.py` | Always-snap checkbox in the same dialog. |
| Tests | Shortcut exists; always-snap records snapped first/last without Ctrl; Ctrl still works. |

### Risks and acceptance

- Global shortcuts can collide with QGIS; test in a real QGIS session and choose
  non-conflicting sequences.
- Snapping still depends on the QGIS snapping configuration.
- Gate: integration tests + manual shortcut check.

---

## 8. Release 2.1.0 — Quick wins

1. Bump `metadata.txt` and `pyproject.toml` to `2.1.0`.
2. Add the changelog section and update README/user guide.
3. Run `make pre-release`, `make zip`, `make security-scan`, `make qt6-check`,
   `make docker-test`.
4. Deploy and smoke-test in QGIS 4 (and the available Qt5 container).
5. Tag `v2.1.0`, push, GitHub Release, portal upload (manual).
6. Update state, metrics and development log.

Acceptance: the five stages work together; smoothing/always-snap default off;
no regression in create/reshape/difference/sampling/edit gating.

---

## 9. Stage 6 — Live length/area

### Goal

Extend the status line with the current length (lines) or area (polygons).

### UX

- `"N vértices · 12.34 m"` or `"N vértices · 45.6 m²"`, using the layer CRS.
- Geographic layers use the project ellipsoid; units are labelled (m, km, m²,
  ha) and degrees are never presented as metres.
- Cleared on finish/cancel.

### Design

| File | Change |
| :--- | :--- |
| `gui/freehand_tool.py` | Build a `QgsDistanceArea` from the layer CRS/project transform context; measure the in-progress geometry; format units. |
| Tests | Known line/polygon in projected and geographic CRS; status text; clear on release. |
| i18n | Unit/label strings. |

### Risks and acceptance

- Geographic CRS: use ellipsoidal measurement, clearly label units.
- Do not compute on every mouse move if it becomes expensive; update on recorded
  vertices only.
- Gate: measurement tests in both CRS types.

---

## 10. Stage 7 — Split a feature with a stroke

### Goal

Split one selected line or polygon into two features with a freehand stroke,
preserving attributes and undo.

### UX

- Select exactly **one** editable feature in the active layer.
- Action **Dividir con trazo**; draw a stroke crossing the feature.
- The stroke is the split line; the original and the new part keep attributes.
- One undo restores the original single feature.

### Design

| File | Change |
| :--- | :--- |
| `gui/freehand_tool.py` | `MODE_SPLIT` (open line). |
| `gui/split_creator.py` | `QgsGeometry.splitGeometry(line, topological=True, splitFeature=True)`; validate result; update original + add new features; one edit command; copy attributes. |
| `freehand_plugin.py` | Action, selection precondition, signal wiring, cleanup. |
| Tests | Polygon split, line split, no intersection, invalid result, undo, attributes, cutter/stroke rejection. |

API evidence: `QgsGeometry.splitGeometry(splitLine, topological, splitFeature)`
returns `(result, new_geometries, topological_test_points)` in QGIS 4.2.2.

### Risks and acceptance

- Split semantics are subtle; test polygon and line cases and a non-crossing
  stroke.
- Copy attributes explicitly; do not rely on provider defaults for the new part.
- One undo command for the whole split.
- This is **not** the same as the difference feature.
- Gate: dedicated split tests in both environments.

---

## 11. Stage 8 — Add a ring/hole to a polygon

### Goal

Draw a freehand closed ring inside a selected polygon and add it as a hole.

### UX

- Select exactly one editable polygon.
- Action **Agregar anillo**; draw a closed ring; release.
- The ring must be inside the polygon and not cross existing rings; otherwise a
  warning and no change.

### Design

| File | Change |
| :--- | :--- |
| `gui/freehand_tool.py` | `MODE_RING` (closed ring, minimum 3 points). |
| `gui/ring_creator.py` | `QgsGeometry.addRing(ring_points)`; validate result; update target; one undo. |
| `freehand_plugin.py` | Action, selection precondition, wiring. |
| Tests | Hole added, ring outside rejected, crossing ring rejected, undo, attributes. |

API evidence: `QgsGeometry.addRing(Iterable[QgsPointXY])` exists in QGIS 4.2.2.

### Risks and acceptance

- Ring closure and validity are the hard parts; reject before `changeGeometry`.
- Only polygons; points/lines are out of scope.
- Gate: ring tests + manual check.

---

## 12. Stage 9 — Add a part to a multipart feature

### Goal

Add a new freehand part (line/polygon) to one selected multipart feature.

### UX

- Select exactly one multipart line/polygon feature.
- Action **Agregar parte**; draw the new part.
- The new part is appended; one undo restores the previous geometry.

### Design

| File | Change |
| :--- | :--- |
| `gui/freehand_tool.py` | `MODE_PART` (line or polygon matching the layer). |
| `gui/part_creator.py` | `QgsGeometry.addPart(part_geometry)`; validate; update; one undo. |
| `freehand_plugin.py` | Action, selection precondition, wiring. |
| Tests | Add polygon part, add line part, singlepart rejected/convert policy, undo. |

API evidence: `QgsGeometry.addPart(part, geomType)` exists in QGIS 4.2.2.

### Risks and acceptance

- Single-part features: decide whether to convert to multipart or reject; plan
  recommends **reject with a clear message** in this stage.
- Geometry type must match the layer.
- Gate: add-part tests + undo.

---

## 13. Release 2.2.0 — Geometry editing

1. Version 2.2.0; changelog, README, user guide, architecture.
2. Full gates, ZIP, security, Qt6, Docker.
3. Deploy and smoke-test split/ring/part.
4. Tag, GitHub Release, portal upload (manual).
5. State/metrics/log.

Acceptance: split/ring/part are independent actions; each has a dedicated undo;
difference/reshape/create behavior unchanged.

---

## 14. Stage 10 — Overlap guard for new features

### Goal

A simple safety option: refuse to create a polygon that overlaps existing
features in the active layer, instead of silently producing overlapping geometry.

### UX

- Checkbox **Evitar solapamientos** in **Configuración de trazo**.
- Before insertion, query nearby features (bbox + intersection) and reject with a
  warning if the new polygon overlaps an existing one.
- Touching boundaries are allowed; lines/points are out of scope.
- This is a **guard**, not full topological editing/clipping.

### Design

| File | Change |
| :--- | :--- |
| `core/settings.py` | `OVERLAP_GUARD_KEY` boolean. |
| `gui/feature_creator.py` | After validity/smoothing, before insert: bbox query + `geometry.overlaps()`; reject with warning. |
| `gui/sampling_dialog.py` | Checkbox. |
| Tests | Overlapping polygon rejected; touching polygon accepted; empty layer accepted; lines unaffected; no performance regression on a moderate layer. |

### Risks and acceptance

- False positives/negatives from topology and shared boundaries; document the
  limitation.
- No clipping or splitting; full “prevent overlap” remains out of scope.
- Gate: overlap tests + manual check; release 2.3.0.

---

## 15. Cross-cutting rules

- **Plan-first per stage**: approve the roadmap, then implement one stage at a
  time; each stage updates its own plan/issue before code.
- **Core/GUI boundary**: geometry logic that can be pure stays in `core/`; QGIS
  operations stay in `gui/`.
- **Edit-session gate**: all modification actions require `layer.isEditable()`.
- **Undo**: every mutation is one edit command.
- **i18n**: Spanish source + English catalog; `make transup`/`i18n-check`.
- **Tests**: unit for pure rules (stroke, settings), integration for QGIS;
  Qt5 container for every release.
- **Quality**: `make pre-release`, `make zip`, `make security-scan`,
  `make qt6-check`, `make docker-test`.
- **Versioning**: 2.1.0 quick wins, 2.2.0 geometry editing, 2.3.0 overlap guard.
- **No runtime dependencies**; QGIS 3.28–4.x / Qt5–Qt6.

---

## 16. Risks and decisions

| Risk | Mitigation |
| :--- | :--- |
| Feature creep | Stage gates; each stage is independently shippable. |
| Smoothing surprises users | Default off; document; validate result. |
| Split/ring/part complexity | Dedicated creators, tests and manual smoke checks; do not bundle with quick wins. |
| Global shortcut conflicts | Test against QGIS defaults; choose `Ctrl+Alt+*`; document. |
| Geographic measurement units | Ellipsoidal measure and explicit unit labels. |
| Overlap guard overpromises | Call it a guard; no clipping; document boundary rules. |
| QGIS 3.28 differences | Test APIs in container; `QgsGeometry` methods exist in 3.x. |

**Decisions requested:**

1. Release split: 2.1.0 quick wins, 2.2.0 geometry editing, 2.3.0 overlap guard?
2. Shortcut set: `Ctrl+Alt+C/R/D/S` (or no shortcuts)?
3. Smoothing: fixed offset `0.25`, iterations 1–5 (default 2)?
4. Add-part policy for singlepart features: reject (recommended) or convert?
5. Live length/area: project ellipsoid for geographic CRS (recommended)?
6. Start with Stage 1 after approval, or approve the whole roadmap?

---

## 17. Approval

The roadmap is **APPROVED**. No stage has started; implementing Stage 1 requires
a new explicit instruction and a stage kickoff.

Suggested first implementation batch: **Stages 1–5 for 2.1.0**, then a release
gate; geometry editing (Stages 6–9) and the overlap guard (Stage 10) follow in
separate releases.

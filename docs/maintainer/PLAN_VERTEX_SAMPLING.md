# Implementation Plan — Vertex Sampling Settings

> **Status: IMPLEMENTED (2026-11-19)** — approved with the edit-session plan for
> **v2.0.0**. Implementation follows this plan.
>
> Version: 2.0.0 | Date: 2026-11-19
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Goal

Let the user choose **how many vertices are captured per distance**:

- **Pixels** — one vertex every N device pixels (current behavior, independent
  of CRS and zoom).
- **Layer units** — one vertex every N layer units (metres/feet for projected
  CRS, **degrees** for geographic CRS).

The choice must be persisted, apply to both creation and reshape, and warn the
user when a geographic CRS makes “layer units = degrees” unsuitable for uniform
distance sampling.

---

## 2. Scope and non-goals

### In scope

- A settings dialog with:
  - a **unit** selector: `Pixels` / `Layer units`;
  - a **minimum distance** spinbox whose range, decimals and tooltip change with
    the unit;
  - a geographic-CRS warning when the active layer uses a geographic CRS.
- Persisted settings in `QgsSettings`:
  - `freehand_digitize/sampling_unit` (`px` or `layer`);
  - `freehand_digitize/sampling_distance_px`;
  - `freehand_digitize/sampling_distance_layer`.
- Separate stored distances per unit, so switching px ↔ layer never reinterprets
  `1.5` as `1.5°`.
- `StrokeRecorder` support for both thinning modes.
- Apply the options to the creation and reshape tools at the next stroke; no
  restart.
- Spanish source strings + English catalog, unit and integration tests, docs and
  metadata.

### Out of scope

- Geodesic distance (`QgsDistanceArea`) for geographic CRS. Layer-unit sampling
  is Euclidean in the layer CRS; for a geographic CRS that means degrees, not
  metres. A future enhancement could add a geodesic mode.
- Changing the 20,000-point safety cap (`MAX_STROKE_POINTS`) from the UI.
- Per-layer settings or project-level settings; the options are plugin-wide.
- Automatic simplification; the existing tolerance spinbox remains independent.

### Dependency

This plan assumes the edit-session gate from
[PLAN_EDIT_SESSION.md](PLAN_EDIT_SESSION.md): the create/reshape tools are only
active while the layer is in edit mode. The sampling **settings dialog** remains
available outside edit mode because it is configuration, not a map tool. The
tool tests that draw a stroke must start editing explicitly.

---

## 3. Current state

- `core/constants.py` defines `MIN_SAMPLE_PIXELS = 1.5` and
  `MAX_STROKE_POINTS = 20000`.
- `core/stroke.py` `StrokeRecorder` compares **device pixel** distances against
  `min_distance_px`; it does not store layer-space distances.
- `gui/freehand_tool.py` creates one `StrokeRecorder()` with the defaults and
  uses it for every stroke.
- The only sampling-related UI is the simplification tolerance spinbox (0–5
  layer units), which is applied **after** capture by `FeatureCreator`.
- `core/settings.py` already provides an injectable `SettingsBackend` protocol
  and `ToleranceStore`; the new store can follow the same pattern.

Verified facts:

- `MIN_SAMPLE_PIXELS = 1.5` (`core/constants.py`).
- `StrokeRecorder.add` uses `device_point` deltas squared against
  `min_distance_px**2` (`core/stroke.py`).
- `FreehandTool.__init__` sets `self._recorder = StrokeRecorder()` and reuses it
  (`gui/freehand_tool.py`).
- `QgsSettings` is already used by `ToleranceStore` and the plugin; no new
  runtime dependency is needed.

---

## 4. Semantics and geographic-CRS observation

| Mode | Unit of the distance | Depends on zoom? | Depends on CRS? | Use case |
| :--- | :--- | :---: | :---: | :--- |
| Pixels (default) | Device pixels | Yes (screen density) | No | Smooth, uniform stroke regardless of CRS. |
| Layer units | Layer CRS units | No | Yes | A geographic density (e.g. one vertex every 0.5 m) in projected data. |

### Geographic CRS rule

For a **projected** CRS, layer units are metres/feet and the Euclidean distance
is meaningful. For a **geographic** CRS, layer units are **degrees**:

- one degree of latitude is roughly constant (~111 km), but one degree of
  longitude shrinks with latitude (cos φ);
- a Euclidean degree distance is **not** a uniform ground distance and changes
  with latitude;
- `StrokeRecorder` compares layer coordinates directly, so it will not apply a
  geodesic correction.

**Decision proposed:** allow layer units for geographic layers, but show a clear
warning in the dialog and in the tooltip:

> “La capa activa usa un CRS geográfico. En unidades de capa la distancia se
> mide en grados; un grado de longitud no tiene una longitud constante (depende
> de la latitud). Usa píxeles si quieres una densidad uniforme en pantalla.”

The warning is informational; the user can still choose degrees. If the project
prefers stricter behavior, the alternative is to disable the “Layer units”
option for geographic CRS (consistent with the tolerance policy); this plan does
**not** do that unless requested.

### Values and ranges

| Setting | Default | Minimum | Maximum | Decimals | Step |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Pixels | 1.5 | 0.5 | 50.0 | 1 | 0.5 |
| Layer units | 0.5 (projected) / 0.0001 (geographic first use) | 0.000001 | 100000.0 | 6 | 0.1 |

The layer default is seeded from the active layer when no value has been stored:
`0.0001°` (~11 m at the equator) for geographic CRS, `0.5` for projected CRS.
The stored value is then reused.

A distance of `0` is clamped to the minimum; the recorder already accepts every
point when the threshold is zero, but the UI should not expose that as a normal
mode.

---

## 5. UX

### Entry point

- New action **Configuración de muestreo** / **Sampling settings** in
  **Vector → Freehand Digitize** and as a small gear button in the Digitize
  toolbar (after the tolerance spinbox).
- Enabled whenever the plugin is loaded, even with no active layer; opening it
  without a layer simply omits the geographic warning.

### Dialog

```
┌──────────────────────────────────────────────┐
│ Configuración de muestreo                    │
│                                              │
│ Unidad de muestreo:  [ Píxeles        ▼ ]    │
│ Distancia mínima:    [ 1.5        ] px       │
│                                              │
│ ⓘ Píxeles: independiente del CRS y del zoom. │
│   Unidades de capa: depende del CRS.         │
│                                              │
│ ⚠ La capa activa usa un CRS geográfico...    │
│                                              │
│              [Restablecer] [Cancelar] [OK]   │
└──────────────────────────────────────────────┘
```

- Changing the unit updates the spinbox decimals, range, suffix (`px`, `m`/`°`
  or no suffix) and the distance shown (the stored value for that unit).
- `Restablecer` restores the default for the selected unit.
- `OK` saves and closes; `Cancel` discards.
- If the active layer is geographic, the warning label is visible; if no layer is
  active, only the general explanation is shown.
- The suffix for layer units is omitted (QGIS layer units can be metres, feet or
  degrees); the explanation names the active CRS units when known.

### Application

- The plugin passes a `SamplingStore` to both `FreehandTool` instances.
- On press, the tool builds a `StrokeRecorder` from the current options; changes
  take effect on the next stroke without restarting QGIS.
- Both creation and reshape use the same sampling options.
- The existing tolerance spinbox remains a separate, post-capture simplification.

---

## 6. Design

### Files

| File | Action | Responsibility |
| :--- | :--- | :--- |
| `core/constants.py` | Modify | Sampling keys, defaults, ranges and unit constants. |
| `core/stroke.py` | Modify | `SamplingOptions`; pixel/layer thinning in `StrokeRecorder`. |
| `core/settings.py` | Modify | `SamplingStore` with validation and separate per-unit values. |
| `gui/sampling_dialog.py` | **New** | `QDialog` with unit combo, distance spinbox, warning and reset. |
| `gui/qt_compat.py` | Modify | Reusable `exec_dialog` helper for PyQt5/PyQt6. |
| `gui/freehand_tool.py` | Modify | Build the recorder from the sampling options on each press. |
| `freehand_plugin.py` | Modify | Settings action, store, dialog and tool injection. |
| `tests/core/test_stroke.py` | Modify | Pixel and layer thinning cases. |
| `tests/core/test_settings.py` | Modify | `SamplingStore` defaults, save/load, invalid values. |
| `tests/integration/test_sampling_dialog.py` | **New** | Dialog values, geographic warning, accept/cancel/reset. |
| `tests/integration/test_plugin.py` | Modify | Sampling action and tool configuration. |
| `tests/integration/test_freehand_tool.py` | Modify | Tool uses the configured recorder. |
| `i18n/freehand_digitize_en.ts/.qm` | Regenerate | New strings. |
| `scripts/i18n/master_data/en.json` | Modify | Spanish → English translations. |
| `README.md`, `docs/user/USER_GUIDE.md`, `docs/ARCHITECTURE_EN.md`, `CHANGELOG.md`, `metadata.txt` | Modify | Feature docs and metadata. |

### Core model

```python
SAMPLE_UNIT_PX = "px"
SAMPLE_UNIT_LAYER = "layer"

@dataclass(frozen=True)
class SamplingOptions:
    unit: str = SAMPLE_UNIT_PX
    distance_px: float = 1.5
    distance_layer: float = 0.5

@dataclass
class StrokeRecorder:
    options: SamplingOptions = SamplingOptions()
    max_points: int = 20000
    _last_layer: tuple[float, float] | None = None
    # add():
    #   if options.unit == SAMPLE_UNIT_LAYER:
    #       compare squared layer distance with distance_layer**2
    #   else:
    #       compare squared device distance with distance_px**2
```

- Keep `min_distance_px` as a compatibility property for existing tests or
  migrate the tests to `SamplingOptions`; prefer the explicit options object.
- `reset()` clears `_last_layer`.
- Invalid/negative distances are clamped in `SamplingStore`; the recorder also
  treats a non-positive threshold as “accept every point”.

### Settings store

```python
class SamplingStore:
    def load(self) -> SamplingOptions: ...
    def save(self, unit: str, distance: float) -> SamplingOptions: ...
    def layer_default(self, is_geographic: bool) -> float: ...
```

- Keys: `freehand_digitize/sampling_unit`, `.../sampling_distance_px`,
  `.../sampling_distance_layer`.
- `load()` validates the unit; unknown → `px`. Missing distances → defaults.
- `save()` writes the selected unit and only the corresponding distance.
- The protocol is the existing `SettingsBackend`; unit tests use the fake backend.
- No `QgsSettings` import in `core/`.

### Tool and plugin wiring

- `FreehandTool.__init__(..., sampling_store=None)`; store defaults to a
  `SamplingStore` with an in-memory backend? Better: the plugin passes the store;
  if `None`, use `SamplingOptions()` defaults for tests.
- `_new_recorder()`:
  ```python
  options = self._sampling_store.load() if self._sampling_store else SamplingOptions()
  return StrokeRecorder(options)
  ```
- Call `_new_recorder()` at press time (before `start`), so settings changes are
  picked up without restart.
- Plugin:
  - create `SamplingStore(self._settings)`;
  - pass it to both `FreehandTool` instances;
  - add `sampling_action`, connect to `_on_sampling_settings`;
  - `_on_sampling_settings`: build `SamplingDialog(self.iface.activeLayer(),
    self._sampling_store, self.iface.mainWindow())`; execute with the shared
    helper; on accepted, the store is already saved.
  - Add the action to the Vector menu and the Digitize toolbar.
  - `unload`: remove the action and dialog reference.

### Dialog details

- `QComboBox` with data `"px"` / `"layer"`.
- `QDoubleSpinBox`:
  - px: range 0.5–50, 1 decimal, suffix `" px"`, step 0.5.
  - layer: range 0.000001–100000, 6 decimals, no suffix, step 0.1.
- Warning `QLabel` (word-wrapped) shown only when
  `layer.crs().isGeographic()`.
- General help label always visible.
- `Restablecer` sets the selected unit's default; for layer with a geographic
  active layer, use `0.0001`, otherwise `0.5`.
- `QDialogButtonBox` with Ok/Cancel/Reset; use `exec_dialog` for Qt5/Qt6.
- On accept: `store.save(unit, spin.value())`.
- No modal form interaction with the map tool; the dialog is opened from the
  plugin action, not from a canvas event.

---

## 7. Tests

### Unit (`tests/core`, no QGIS)

| Test | Assertion |
| :--- | :--- |
| `test_pixel_thinning_is_unchanged` | Existing 1.5 px behavior still works. |
| `test_layer_thinning_uses_layer_units` | Points below the layer distance are skipped; points above are recorded. |
| `test_layer_thinning_ignores_device_distance` | A large device delta with a small layer delta is skipped (and vice versa) to prove the mode. |
| `test_recorder_reset_clears_last_layer` | A new stroke starts from the first point. |
| `test_sampling_store_defaults` | Missing keys → px / 1.5. |
| `test_sampling_store_roundtrip` | Each unit and distance round-trips; the other unit keeps its value. |
| `test_sampling_store_invalid_unit` | Unknown unit falls back to px. |
| `test_sampling_store_clamps` | Distances are clamped to the allowed range. |

### Integration (`tests/integration`, real QGIS)

| Test | Assertion |
| :--- | :--- |
| `test_sampling_dialog_defaults` | Shows px and 1.5 for a fresh store. |
| `test_sampling_dialog_geographic_warning` | Warning visible for an EPSG:4326 layer; hidden for EPSG:3857. |
| `test_sampling_dialog_unit_switch` | Switching to layer updates range/decimals and keeps separate values. |
| `test_sampling_dialog_accept_saves` | OK persists unit and distance. |
| `test_sampling_dialog_reset` | Reset restores the default for the selected unit. |
| `test_sampling_dialog_cancel_does_not_save` | Cancel leaves the store unchanged. |
| `test_tool_uses_layer_sampling` | Tool configured with layer units records fewer/different points than px. |
| `test_sampling_action_exists` | Plugin exposes the settings action. |

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
| `Configuración de muestreo` | `Sampling settings` |
| `Unidad de muestreo:` | `Sampling unit:` |
| `Píxeles` | `Pixels` |
| `Unidades de la capa` | `Layer units` |
| `Distancia mínima:` | `Minimum distance:` |
| `Un vértice cada…` (tooltip) | `One vertex every…` |
| `Píxeles: independiente del CRS y del zoom. Unidades de capa: depende del CRS.` | `Pixels: independent of CRS and zoom. Layer units: depends on the CRS.` |
| `La capa activa usa un CRS geográfico. En unidades de capa la distancia se mide en grados; un grado de longitud no tiene una longitud constante (depende de la latitud). Usa píxeles si quieres una densidad uniforme en pantalla.` | `The active layer uses a geographic CRS. In layer units the distance is measured in degrees; one degree of longitude is not a constant length (it depends on latitude). Use pixels for a uniform on-screen density.` |
| `Restablecer` | `Reset` |
| `Cancelar` | `Cancel` |
| `Aceptar` | `OK` |

Procedure: `make transup` → `make transcompile` → `make i18n-check`; add the
unit strings to `tests/test_i18n_catalogs.py`.

---

## 9. Versioning

**Decision required.** Recommended: **2.0.0** (no `v2.0.0` tag exists yet;
this is the same unreleased release as reshape). Alternative: **2.1.0** if
v2.0.0 is considered closed.

Files if a bump is chosen: `metadata.txt`, `pyproject.toml`, `CHANGELOG.md`,
`tests/test_metadata.py`, version headers and `AI_CONTEXT.md`.

---

## 10. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| Degrees are mistaken for a uniform ground distance | Explicit geographic warning in dialog/tooltip; document the latitude dependence; recommend pixels. |
| Switching units reinterprets `1.5` as `1.5°` | Separate `sampling_distance_px` and `sampling_distance_layer` keys. |
| Layer-unit distance depends on CRS/scale | Explain in the dialog and docs; layer units are intentional for projected data. |
| Pixel distance depends on screen/zoom | Document that px is a screen density, not a ground distance. |
| User expects metres in a geographic layer | The warning names degrees explicitly; geodesic sampling is a documented non-goal. |
| Settings are ignored until restart | Rebuild the recorder at each press; integration test covers applying new values. |
| The dialog leaks the tool state | Open it from the plugin action; no modal interaction with `setIgnoreClick`. |
| Performance with very small distances | The 20,000-point cap remains; document it. |
| i18n drift | `make transup`/`i18n-check`; required-string test. |
| Qt5/Qt6 dialog differences | Use `exec_dialog` helper and `qgis.PyQt` imports. |

---

## 11. Acceptance criteria

- [ ] The settings action is visible in the Vector menu and the Digitize toolbar.
- [ ] The user can choose **Pixels** or **Layer units** and a minimum distance.
- [ ] Pixel mode preserves the current 1.5 px behavior by default.
- [ ] Layer mode records vertices by layer-coordinate distance, not device pixels.
- [ ] Switching units preserves a separate distance per unit.
- [ ] A geographic active layer shows the degrees/latitude warning when layer
      units are selected.
- [ ] Settings persist across QGIS sessions and apply to create and reshape
      without restart.
- [ ] The existing tolerance spinbox and simplification behavior are unchanged.
- [ ] Spanish/English strings are complete; `make i18n-check` passes.
- [ ] `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` and
      `make docker-test` pass.
- [ ] The plan is marked `IMPLEMENTED` with the commit hash and results.

---

## 12. Implementation procedure (after approval)

1. Mark this plan `APPROVED` and record the version decision.
2. Add constants and `SamplingOptions`/`StrokeRecorder` layer-mode support.
3. Add `SamplingStore` and unit tests.
4. Add `SamplingDialog` and the `exec_dialog` compatibility helper.
5. Inject the store into both tools; rebuild the recorder at press.
6. Wire the settings action/dialog in the plugin; cleanup in `unload`.
7. Add integration tests for the dialog, tool and plugin.
8. Add strings to `gui/texts.py` and `master_data/en.json`; run `make transup`,
   `make transcompile`, `make i18n-check`.
9. Update README, user guide, architecture, CHANGELOG and metadata.
10. Run `make pre-release`, `make zip`, `make security-scan`, `make qt6-check`,
    `make docker-test`.
11. Deploy and smoke-test in QGIS 4; mark the plan `IMPLEMENTED`.

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
- The default `px`/1.5 behavior means old projects are unaffected if the new
  settings keys are absent.
- Keep this plan; mark it `REJECTED`/`REVERTED` with the reason.

---

## 16. Results

- `SamplingOptions` + layer/pixel thinning in `StrokeRecorder`.
- `SamplingStore` with separate pixel/layer distances and validation.
- `SamplingDialog` with the geographic-CRS warning, reset and per-unit values.
- Both map tools rebuild the recorder from the store at press time.
- Tests: 117 total (57 unit + 60 integration), including dialog and tool cases.
- `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` and
  `make docker-test` pass; deployed smoke test in QGIS 4 passes.
- **Commit:** `dcfb191 feat: add sampling units and edit-session gating`.

---

## 15. Approval

The plan is **PROPOSED**. Implementation starts only after the user confirms:

0. **Edit-session gate**: approve/implement
   [PLAN_EDIT_SESSION.md](PLAN_EDIT_SESSION.md) first (recommended) or together.
1. **Geographic CRS**: allow layer units (degrees) with a warning (recommended),
   or disable layer units for geographic layers?
2. **Version**: **2.0.0** (recommended, unreleased) or 2.1.0?
3. **Entry point**: settings action in the Vector menu + toolbar gear (recommended)
   or only the menu?
4. **Defaults**: px 1.5, layer 0.5 projected / 0.0001 geographic (recommended)?

# Freehand Digitize

Freehand digitizing of **lines and polygons** in QGIS, restoring the features of
the classic [`freehandEditing`](https://github.com/vinayan/freehandEditing)
plugin and adapting them to **QGIS 3.28–4.x** (Qt5 and Qt6).

Drag with the left mouse button over the map and release to create the feature
on the active layer. The stroke is stored in the **layer CRS** (on-the-fly
reprojection safe) and simplified with the configurable tolerance. The same
freehand workflow can also **reshape** existing line/polygon geometries: draw a
stroke across them and release.

---

## Features

| Feature | Detail |
| :--- | :--- |
| Freehand drawing | Lines and polygons; polygons close automatically. |
| Reshape | Draw a stroke across existing line/polygon geometries to reshape them; a selection narrows the targets. |
| Multi-feature reshape | Every geometry under the stroke changes in one undo command. |
| Sampling settings | One vertex every N **pixels** or N **layer units**; a geographic CRS warns that layer units are degrees. |
| Edit-session aware | Create/reshape are enabled only while the layer is in edit mode; stopping editing cancels the stroke. |
| Feature difference | Select two features, or click the target and cutter, to subtract one from the other; one undo command. |
| Simplification tolerance | `QDoubleSpinBox` 0–5, 3 decimals, step 0.1; persisted between sessions. |
| Geographic CRS | The tolerance is disabled and 0 is applied (degrees are not metres). |
| `Ctrl` snapping | Snaps the first and last vertex to existing vertices (QGIS snapping engine). |
| Pencil cursor | Dedicated XPM cursor with `CrossCursor` fallback. |
| Attribute form | Shows the QGIS form (when enabled) with clean cancellation. |
| Provider defaults | `QgsVectorLayerUtils.createFeature` applies defaults and constraints. |
| Undo | The feature is created inside `beginEditCommand`/`endEditCommand`. |
| Invalid geometry | Asks whether to use it instead of silently fixing it. |
| Layer enablement | Only editable line/polygon vector layers. |
| Secondary button | Finishes the current stroke (like the original plugin). |
| `Esc` | Cancels the stroke; with no stroke it deactivates the tool. |
| No dependencies | No external Python packages; uses `qgis.PyQt`. |
| Languages | Spanish source UI with an English catalog; more catalogs can be added. |

### Parity with `freehandEditing`

The full comparison is in
[`docs/maintainer/FEATURE_PARITY.md`](docs/maintainer/FEATURE_PARITY.md).
Restored: persistent tolerance, `Ctrl` snapping, pencil cursor, attribute form,
provider defaults, undo commands, invalid-geometry prompt, layer CRS and
per-layer enablement. Reshape is a new feature, not part of the upstream plugin.

---

## Requirements

- **QGIS 3.28 or newer**, including QGIS 4.x (Qt6).
- No additional Python dependencies: QGIS provides PyQt, GDAL and GEOS.

## Installation

### From the ZIP

1. Download `dist/freehand_digitize.<version>.zip`.
2. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Enable **Freehand Digitize**.

### From the repository (development)

```bash
# Direct deployment into the QGIS 4 profile
uv run qgis-manage deploy --no-compile --qgis-version 4
```

You can also copy this folder to
`~/.local/share/QGIS/QGIS4/profiles/default/python/plugins/freehand_digitize`.

---

## Usage

1. Select a **line or polygon layer** and start editing. The actions are
   disabled until the layer is in edit mode.
2. Click **Dibujo a mano alzada** in the digitize toolbar or
   **Vector → Freehand Digitize**.
3. Drag with the left mouse button to draw.
4. Release to create the feature. If the attribute form is enabled, it opens
   before the feature is added.
5. Adjust the **tolerance** in the digitize toolbar spin box (0 = no
   simplification).

### Sampling settings

Open **Configuración de muestreo** (English: **Sampling settings**) from the
Digitize toolbar gear or **Vector → Freehand Digitize**. The dialog offers:

- **Pixels**: one vertex every N device pixels (the default, 1.5 px; independent
  of CRS and zoom).
- **Layer units**: one vertex every N layer units (metres/feet in projected CRS,
  **degrees** in geographic CRS).

The two units keep separate distances, so switching units does not reinterpret
`1.5` as `1.5°`. For a geographic layer the dialog warns that a degree of
longitude is not a constant length (it depends on latitude); use pixels for a
uniform on-screen density.

### Feature difference (cut)

1. Select the line/polygon layer and start editing.
2. Select exactly two features, **or** leave the selection as is and use the
   mouse pick flow.
3. Click **Diferencia de entidades** (English: **Feature difference**).
4. If two features are selected, the dialog opens; otherwise click the **target**
   and then the **cutter** on the map.
5. Choose/confirm target and cutter; press **Aplicar**.
6. The target becomes `target − cutter`; the cutter is untouched. One `Ctrl+Z`
   restores the target.

With a geographic CRS or mixed geometry types, the operation follows QGIS
`QgsGeometry.difference`; cross-layer difference is not supported in this
version.

### Reshaping an existing feature

1. Select a **line or polygon layer** and start editing if needed.
2. Optional: select one or more features to restrict the reshape to them.
3. Click **Reformar geometría** (English: **Reshape feature**) in the digitize
   toolbar or choose **Vector → Freehand Digitize**.
4. Draw a stroke that crosses the geometry; for lines and polygon boundaries the
   stroke must cross at least twice.
5. Release to apply. All features under the stroke are reshaped in one undo
   command; with a selection, only selected features are considered.

The full user guide is in [`docs/user/USER_GUIDE.md`](docs/user/USER_GUIDE.md).

### Shortcuts and mouse buttons

| Action | Effect |
| :--- | :--- |
| Left button + drag | Draws the stroke. |
| `Ctrl` (at start/end) | Snaps the first/last vertex to QGIS snapping targets. |
| Release any button | Finishes the stroke (secondary button halts it). |
| `Esc` with a stroke in progress | Cancels the stroke and keeps the tool active. |
| `Esc` with no stroke | Deactivates the tool. |

> `Ctrl` snapping respects the QGIS snapping configuration (tolerance, mode and
> layers). If no vertex is within tolerance, the free point is used.

---

## Architecture

```
freehand_digitize/
├── __init__.py              # classFactory
├── freehand_plugin.py       # action, spinbox, signals, lifecycle
├── core/                    # pure logic, no QGIS or Qt
│   ├── constants.py
│   ├── geometry_rules.py
│   ├── settings.py
│   └── stroke.py
├── gui/                     # PyQGIS / Qt
│   ├── cursor.py
│   ├── feature_creator.py
│   ├── freehand_tool.py
│   ├── geometry_factory.py
│   └── qt_compat.py
└── tests/                   # unit (no QGIS) and integration (real QGIS)
```

- `core/` does not import `qgis` or Qt; it receives plain values and is testable
  without QGIS.
- `gui/` contains the PyQGIS APIs and the PyQt5/PyQt6 shims.

See [`docs/ARCHITECTURE_EN.md`](docs/ARCHITECTURE_EN.md) for the full design.

---

## Development and QA

The development environment is managed with [`uv`](https://docs.astral.sh/uv/);
the plugin itself is not installed with `pip`.

```bash
uv sync --frozen            # development environment
make test                   # unit tests (no QGIS)
make test-qgis              # integration against the system QGIS
make lint                   # ruff
make flake8                 # flake8 (QGIS portal scope)
make mypy                   # core/ types
make docs-check             # relative documentation links
make i18n-check              # translation catalogs
make analyzer               # qgis-analyzer, CC <= 10
make agent-validate         # validate the agentic system
make qgis-validate          # metadata and structure
make zip                    # ZIP + artifact validation
```

The `uv` modernization guide is in
[`docs/maintainer/uv_modernization_guide.md`](docs/maintainer/uv_modernization_guide.md).

### CI

`.github/workflows/test.yml` runs:

- lint, formatting, flake8, mypy, docs links, `forge validate` and
  `qgis-manage validate`;
- unit tests without QGIS;
- Qt6/PyQt6 enum check (`pyqgis4-checker`);
- integration tests in a QGIS container.

---

## Documentation

- [User guide](docs/user/USER_GUIDE.md)
- [Architecture](docs/ARCHITECTURE_EN.md)
- [Change procedure (plan first)](docs/maintainer/CHANGE_PROCEDURE.md)
- [Reshape implementation plan](docs/maintainer/PLAN_RESHAPE.md)
- [Vertex sampling plan (proposed)](docs/maintainer/PLAN_VERTEX_SAMPLING.md)
- [Edit-session gating plan (proposed)](docs/maintainer/PLAN_EDIT_SESSION.md)
- [Feature-difference plan](docs/maintainer/PLAN_FEATURE_DIFFERENCE.md)
- [CI checkout fix plan](docs/maintainer/PLAN_CI_CHECKOUT.md)
- [Staged feature roadmap](docs/maintainer/PLAN_FEATURE_ROADMAP.md)
- [Deleted-layer lifecycle fix](docs/maintainer/PLAN_LAYER_LIFECYCLE.md)
- [Documentation style guide](docs/maintainer/DOCS_STYLE_GUIDE.md)
- [Commit guidelines](docs/maintainer/COMMIT_GUIDELINES.md)
- [User guide conventions](docs/maintainer/USER_GUIDE_CONVENTIONS.md)
- [Development log](docs/maintenance/DEVELOPMENT_LOG.md)
- [Parity report with freehandEditing](docs/maintainer/FEATURE_PARITY.md)
- [uv modernization guide](docs/maintainer/uv_modernization_guide.md)
- [i18n and translation workflow](scripts/i18n/README.md)

## License and attribution

GPL-2.0. The original **Freehand Editing** plugin is by Pavol Kapusta
(2010–2012) and Larry Shaffer (2013); this modern version keeps its ideas and
part of its behaviour (XPM cursor, event semantics, tolerance and form). See
[`LICENSE`](LICENSE).

The plugin is maintained at <https://github.com/geociencio/freehand-digitize>; `homepage`, `repository` and `tracker` in
`metadata.txt` point there. The original `freehandEditing` repository is kept as
attribution only. See <https://github.com/geociencio/freehand-digitize/issues> for bug reports.

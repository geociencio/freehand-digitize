# Freehand Digitize — Agent Guidelines

This is the **single source of truth** for agent configuration in this
repository (roles, skills, workflows and quality gates). The reusable
[Agentic Forge](https://codeberg.org/geociencio/agentic-forge) framework is
vendored under `.agent/` (Agentic Forge 1.4.2); project-owned state, overlay
skills and workflows live under `.agent-state/`. Paths are resolved through
`forge.toml` and `.agent/tools/forge_paths.py`.

---

## 🧑‍💻 Agent Roles

The agent adopts one of three roles depending on the task. Roles are registered
as subagents in `opencode.json` with a permission gradient:
`architect` (`edit: allow`), `qa_engineer` (`edit: ask`), `auditor`
(`edit: deny`).

### 🏗️ Senior Architect (@architect)

- **Role**: senior Python/QGIS architect.
- **Goal**: protect the `core/` ↔ `gui/` boundary and design small, testable
  features.
- **Constraint**: never put Qt/PyQGIS imports in `core/`; stop and present a
  technical plan before large refactors.
- **Skills**: [coding-standards](.agent/skills/coding-standards/SKILL.md),
  [documentation-standards](.agent/skills/documentation-standards/SKILL.md),
  [freehand-digitizing](.agent-state/skills/freehand-digitizing/SKILL.md).

### 🧪 QA & Automation Engineer (@qa_engineer)

- **Role**: testing, CI and stability specialist.
- **Goal**: zero-regression releases; every restored `freehandEditing` feature is
  covered by a unit or integration test.
- **Constraint**: focus on finding, fixing and validating; keep the suite green
  in both environments (uv without QGIS and the host QGIS).
- **Skills**: [testing-standards](.agent/skills/testing-standards/SKILL.md),
  [commit-standards](.agent/skills/commit-standards/SKILL.md),
  [qgis-migration-4x](.agent-state/skills/qgis-migration-4x/SKILL.md).

### 🕵️ Agent Auditor (@auditor)

- **Role**: independent technical auditor.
- **Goal**: verify plans and paths, detect hallucinations and standards drift.
- **Constraint**: no deviation from `ruff format`, `uv`, the QGIS API
  compatibility shims or the user-facing language policy; verify every file path
  before claiming success.
- **Skills**: [agentic-memory](.agent/skills/agentic-memory/SKILL.md),
  [project-context](.agent-state/skills/project-context/SKILL.md).

---

## 🧭 Workflow Commands

When the user types `/name`, read the corresponding workflow file and execute its
steps. Core workflows live in `.agent/workflows/name.md`; QGIS/project workflows
live in `.agent-state/workflows/name.md`.

<!-- WORKFLOWS_TABLE_START -->
| Command | Workflow file | Purpose |
| :--- | :--- | :--- |
| `/audit-plugin` | `.agent-state/workflows/audit-plugin.md` | Full or partial plugin audit with `qgis-analyzer`. |
| `/build-feature` | `.agent/workflows/build-feature.md` | Autonomous feature pipeline. |
| `/close-phase` | `.agent/workflows/close-phase.md` | Close a development phase with metrics and retro. |
| `/close-session` | `.agent/workflows/close-session.md` | End a session, update state and archive results. |
| `/create-commit` | `.agent/workflows/create-commit.md` | Clean conventional commit with quality validation. |
| `/fix-linting` | `.agent/workflows/fix-linting.md` | Auto-correct lint and format issues. |
| `/i18n-maintenance` | `.agent/workflows/i18n-maintenance.md` | Translation maintenance (out of scope for 2.0.0). |
| `/ia-critic` | `.agent/workflows/ia-critic.md` | Critical review of an implementation plan. |
| `/refactor-code` | `.agent/workflows/refactor-code.md` | Refactor with complexity validation. |
| `/release-plugin` | `.agent-state/workflows/release-plugin.md` | QGIS portal release flow for this plugin. |
| `/run-tests` | `.agent/workflows/run-tests.md` | Run the unit suite reliably. |
| `/run-tests-in-qgis` | `.agent-state/workflows/run-tests-in-qgis.md` | Integration tests against a real QGIS. |
| `/smoke-qgis4` | `.agent-state/workflows/smoke-qgis4.md` | Headless QGIS 4 smoke test (load, draw, create). |
| `/start-phase` | `.agent/workflows/start-phase.md` | Start a major phase. |
| `/start-session` | `.agent/workflows/start-session.md` | Standard session start. |
| `/verify-standards` | `.agent/workflows/verify-standards.md` | Audit agent-system consistency. |
<!-- WORKFLOWS_TABLE_END -->

Full index: `.agent/workflows/index.md` plus `.agent-state/workflows/`.

---

## 🚀 Build / Lint / Test Commands

```bash
# Environment
uv sync --frozen              # create the dev environment from uv.lock
uv lock --check               # lockfile is authoritative

# Tests
make test                     # unit tests, no QGIS required
make test-qgis                # integration tests against the host QGIS
make test-all                 # both
make docker-test              # integration tests in the QGIS container

# Quality
make lint                     # ruff check
make format                   # ruff format (writes)
make flake8                   # QGIS portal scope (packaged code)
make mypy                     # type-check core/ (follow-imports=silent)
make analyzer                 # qgis-analyzer --max-cc 10
make agent-validate           # Agentic Forge validator
make qgis-validate            # qgis-manage validate --strict
make security-scan            # qgis-manage security --portal
make qt6-check                # pyqgis4-checker (Docker)
make zip                      # package + validate the ZIP
make pre-release              # all blocking gates
```

Single test examples:

```bash
PYTHONPATH=.. uv run --frozen python -m unittest \
  tests.integration.test_freehand_tool.TestFreehandTool.test_ctrl_snaps_the_first_vertex -v
PYTHONPATH=.. uv run --frozen python -m unittest \
  tests.integration.test_feature_creator.TestFeatureCreator -v
```

> On constrained sandboxes set `UV_CACHE_DIR=$PWD/.uvcache`; the Makefile already
> exports it.

---

## 🏗️ Architecture

The plugin follows a strict **Core/GUI separation**:

```
core/   pure rules: constants, geometry decisions, stroke sampling, settings
gui/    PyQGIS/Qt: map tool, rubber band, cursor, feature creation, compat shims
freehand_plugin.py   wiring: action, tolerance spinbox, signals, lifecycle
```

### Data flow

1. `FreehandTool` records vertices with `toLayerCoordinates()` (layer CRS) and
   draws the rubber band in canvas coordinates.
2. On release it emits `geometryFinished(QgsGeometry, QgsVectorLayer)`.
3. `FeatureCreator` simplifies, validates, opens the attribute form and inserts
   the feature inside an undo command.
4. `FreehandDigitizePlugin` owns the action, spinbox, layer enablement and
   lifecycle.

### NEVER do this

```python
# ❌ core/ must not import QGIS or Qt
from qgis.core import QgsGeometry
from qgis.PyQt.QtCore import QObject
```

```python
# ❌ do not read the whole project CRS when drawing; use the layer CRS
point = event.mapPoint()  # project CRS, wrong for a layer with another CRS

# ✅ correct
point = self.toLayerCoordinates(layer, event.pos())
```

### ALWAYS

- Keep `core/` importable without QGIS (the unit suite proves it).
- Put PyQt5/PyQt6 differences in `gui/qt_compat.py`.
- Use `qgis.PyQt`, never `PyQt5`/`PyQt6` directly.
- Capture the layer at press time; finish the feature there even if the active
  layer changes mid-stroke.

---

## 📝 Code Style

- `from __future__ import annotations` in every module.
- Type annotations for function signatures; Google-style docstrings for public
  APIs (Ruff `D` rules).
- Ruff is the formatter and linter: 100 columns, double quotes, `py39` target
  syntax. `core/` is mypy-checked.
- Naming: `PascalCase` classes, `snake_case` functions, `UPPER_SNAKE` constants.
- **Language policy**: user-facing UI strings are Spanish (the plugin is
  Spanish-only in 2.0.0, with `MISSING_I18N` disabled in the analyzer profile);
  code, tests, docstrings, commits and technical docs are English.
- Errors in Qt callbacks are logged (`QgsMessageLog`) and surfaced via
  `iface.messageBar()`; never let an exception escape a canvas event.
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`,
  `chore:`.

---

## 🧪 Testing Standards

The suite uses the standard-library **`unittest`** framework in two layers:

| Layer | Location | Requires QGIS | Purpose |
| :--- | :--- | :---: | :--- |
| Unit | `tests/core/` | No | geometry rules, stroke sampling, settings, constants, Python 3.9 syntax |
| Integration | `tests/integration/` | Yes | map tool, snapping, feature creation, plugin lifecycle, Qt6 enums |

Rules:

1. **Mock-free core**: `tests/core/` must never import `qgis` or Qt.
2. **Graceful skip**: integration modules import QGIS only after
   `ensure_qgis_app()`; without QGIS they are reported as skipped, so
   `make test` works everywhere.
3. **Real API only**: the integration fakes (`tests/integration/fakes.py`)
   mirror the real `QgisInterface` methods used by the plugin; never invent a
   method to satisfy production code.
4. **Isolation**: each test creates its own memory layers, canvas and fake
   interface; `addCleanup` releases the QWidgets.
5. **Assertions**: `assertEqual`, `assertTrue`, `assertRaises`, `assertAlmostEqual`
   — no bare `assert`.
6. **QGIS teardown**: a 139 exit after an `OK` run is tolerated by the Makefile
   and CI; failures are never ignored.

Naming: `test_*.py`, `Test[Module]`, `test_[behavior]`.

---

## 🛡️ Quality Gates

Blocking (`make pre-release`):

- `ruff check` and `ruff format --check`;
- `flake8` on `core gui freehand_plugin.py __init__.py`;
- `mypy` on `core/`;
- `qgis-analyzer --max-cc 10` (no function > CC 10);
- `forge validate` with `strict_agent_system = true`;
- unit tests and QGIS integration tests;
- `qgis-manage validate --strict`.

Release-only:

- `make zip` → `qgis-manage package --repo-check` + `validate --zip`;
- `make security-scan` → no CRITICAL findings;
- `make qt6-check` → no Qt6/PyQt6 enum errors;
- `qgisMaximumVersion` stays `4.99` (QGIS 4 Ready); `supportsQt6` is deprecated
  and must not be re-added.

---

## 📊 Project Structure

```
freehand_plugin.py     # plugin entry/wiring
core/                  # QGIS-agnostic logic
gui/                   # PyQGIS/Qt layer
tests/core/            # unit tests (no QGIS)
tests/integration/     # real QGIS tests
tests/mocks/           # QGIS-free fakes
docs/maintainer/       # plan, parity report, uv guide
.agent/                # Agentic Forge framework (vendored)
.agent-state/          # project state, overlay skills/workflows
.github/workflows/     # CI
```

---

## 🛠️ Skills

Load only the relevant `SKILL.md` on demand.

| Skill | Description | When to use |
| :--- | :--- | :--- |
| [agentic-memory](.agent/skills/agentic-memory/SKILL.md) | Lessons, patterns and preferences | Session close; recurring errors |
| [changelog-generator](.agent/skills/changelog-generator/SKILL.md) | User-facing changelog from commits | Release notes |
| [coding-standards](.agent/skills/coding-standards/SKILL.md) | pathlib, docstrings, typing | Writing/refactoring code |
| [commit-standards](.agent/skills/commit-standards/SKILL.md) | Conventional commits | Before committing |
| [documentation-standards](.agent/skills/documentation-standards/SKILL.md) | Logs and project history | Updating docs/logs |
| [freehand-digitizing](.agent-state/skills/freehand-digitizing/SKILL.md) | Upstream parity, PyQGIS freehand traps | Any drawing/tool change |
| [i18n-standards](.agent/skills/i18n-standards/SKILL.md) | Translation standards | Only if i18n is reintroduced |
| [project-context](.agent-state/skills/project-context/SKILL.md) | Purpose and architecture | Session start; summaries |
| [qgis-core](.agent-state/skills/qgis-core/SKILL.md) | PyQGIS layers, CRS, tools | QGIS API work |
| [qgis-migration-4x](.agent-state/skills/qgis-migration-4x/SKILL.md) | Qt6/QGIS 4 readiness | Imports, enums, deprecations |
| [qgis-release](.agent-state/skills/qgis-release/SKILL.md) | Portal validation/submission | Before uploading a ZIP |
| [release-management](.agent/skills/release-management/SKILL.md) | Release process | Releases |
| [testing-standards](.agent/skills/testing-standards/SKILL.md) | unittest, mocks, CI | Writing/running tests |

---

## 📚 Key Resources

- **Plan**: `docs/maintainer/PLAN_FREEHAND_PARITY.md`
- **Parity report**: `docs/maintainer/FEATURE_PARITY.md`
- **uv guide**: `docs/maintainer/uv_modernization_guide.md`
- **Architecture notes**: `.ai-context/architecture_notes.md`
- **Agent state**: `.agent-state/` (`task.md`, `next_steps.md`, memory)
- **Upstream reference**: `freehandEditing/` (GPL-2, untracked, excluded from ZIP)

---

## ⚠️ Critical Reminders

1. **NEVER** import `qgis.gui` or Qt in `core/`.
2. **ALWAYS** draw in layer coordinates (`toLayerCoordinates`), not project
   coordinates.
3. **ALWAYS** keep the Qt5/Qt6 shims in `gui/qt_compat.py`.
4. **ALWAYS** test both environments: `make test` and `make test-qgis`.
5. **NEVER** re-add `supportsQt6`; QGIS 4 Ready is `qgisMaximumVersion >= 4.0`.
6. **KEEP** the UI in Spanish and the technical artifacts in English.
7. **RUN** `make pre-release` before claiming a task is complete.

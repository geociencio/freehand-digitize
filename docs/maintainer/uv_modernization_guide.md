# Modernizing a QGIS Plugin with `uv`

This guide describes how to migrate an existing QGIS plugin from
`pip`/`requirements.txt` to a reproducible [`uv`](https://docs.astral.sh/uv/)
environment. It targets QGIS 3.28–4.x (Qt5/Qt6) and a modern Python toolchain.

> **Scope**: `uv` manages the development environment and the lockfile. QGIS,
> Qt and the QGIS Python runtime are installed and updated separately (OSGeo4W,
> system packages, flatpak or the QGIS installers).

---

## 1. What `uv` does — and what it does not

`uv` handles:

- the project virtual environment (`.venv`);
- dependency resolution and `uv.lock`;
- Python version installation/pinning;
- running tools with the project environment (`uv run`).

`uv` does **not** install QGIS, PyQt or GDAL, and it does not make a QGIS plugin
pip-installable. A plugin is loaded by QGIS from its plugin directory; `uv` is a
development and packaging tool.

**Choose one packaging tool.** `qgis-manage` is the current recommendation for
compile, deploy, package, validation and security. `qgis-plugin-ci` is a valid
alternative, but do not make both mandatory in one project.

| Need | Recommended |
| :--- | :--- |
| Compile `.qrc`/`.ui`/translations | `qgis-manage compile` |
| Deploy to a QGIS profile | `qgis-manage deploy --no-compile --qgis-version 4` |
| Build the plugin ZIP | `qgis-manage package --repo-check` |
| Validate the built ZIP | `qgis-manage validate --zip` |
| Portal-compatible security scan | `qgis-manage security --portal` |
| Analysis, complexity, i18n | `qgis-plugin-analyzer` (dev only) |

---

## 2. Define the Python policy first

QGIS versions and Python versions are coupled:

- QGIS 3.28 ships Python **3.9**;
- newer QGIS releases ship newer Python versions (verify your target);
- QGIS 4 uses Qt 6 and a newer Python runtime.

There are two valid policies; document the one you choose.

### A. Runtime-oriented policy

Set `requires-python` to the minimum Python of the oldest supported QGIS and keep
the development tools compatible with it:

```toml
[project]
requires-python = ">=3.9"
```

Run CI on the oldest and newest supported versions:

```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.12"]
```

### B. Development-oriented policy

If the tooling needs a newer interpreter (for example, the project uses
`requires-python >=3.12`), state explicitly that the **plugin still targets the
QGIS runtime** and that compatibility is covered by tests/linting:

```toml
[project]
requires-python = ">=3.12"  # dev environment; plugin runtime compatibility is tested separately
```

Do not silently set `>=3.10` “because it is common”: it may exclude QGIS 3.28
users or misrepresent the plugin's real support.

Pin the development interpreter in `.python-version` and install it with:

```bash
uv python install
uv python pin 3.12
```

### This project's policy (Freehand Digitize)

The plugin must run on the Python 3.9 bundled with QGIS 3.28, but the QA tools
(`pre-commit` 4.x) require Python 3.11+. The project therefore uses policy **B**:

- `requires-python = ">=3.11"` describes the **development** environment only;
- `.python-version` pins 3.12;
- `tests/core/test_python_compat.py` parses every shipped module with
  `ast.parse(feature_version=(3, 9))`, so syntax newer than 3.9 fails CI;
- QGIS 4 is exercised by the integration suite and the Qt6 checker; the Qt5/Qt6
  compatibility shim lives in `gui/qt_compat.py`.

CI therefore runs 3.11 and 3.12, not 3.9.

---

## 3. Safe migration sequence

Do not start by deleting `requirements.txt`.

1. **Baseline the project**: run the test suite and record the green state.
2. **Create a branch** and keep the old environment files until the new one is
   validated.
3. **Create `pyproject.toml`**. For an existing tree, prefer a bare scaffold:
   ```bash
   uv init --bare
   ```
   `uv init` may create `main.py`, `.python-version` and opinionated metadata;
   review and remove what the plugin does not need.
4. **Declare dependencies**: runtime dependencies first, tooling in
   `[dependency-groups].dev`.
5. **Add tools**:
   ```bash
   uv add --group dev "ruff>=0.17" "mypy>=2.4" "pre-commit>=4.7"
   uv add --group dev "qgis-manage>=0.17.0"
   uv add --group dev "qgis-plugin-analyzer>=1.19.2"
   ```
6. **Generate and lock**:
   ```bash
   uv lock
   uv sync
   ```
7. **Migrate configuration** only where the tool supports `pyproject.toml`
   (Ruff, mypy, pytest, coverage).
8. **Keep tool-specific files** that have no `pyproject.toml` equivalent:
   `.flake8`, `.bandit`, `.secrets.baseline`, `.analyzerignore`, `.qgisignore`.
9. **Update the Makefile and CI** (sections 6 and 9).
10. **Verify in QGIS**: load the plugin, run a preview/export, and build the ZIP.
11. **Remove the old files** (`requirements*.txt`, `pytest.ini`, `ruff.toml`,
    `setup.cfg`) only after the new flow is green.

---

## 4. A minimal `pyproject.toml`

```toml
[project]
name = "my-plugin"
version = "1.0.0"
description = "QGIS plugin description"
readme = "README.md"
requires-python = ">=3.9"      # or your documented dev policy
dependencies = []              # see the warning below
license = { text = "GPL-2.0-or-later" }

[tool.uv]
package = false                # a QGIS plugin is not a pip-installable package
required-version = ">=0.12"    # fail early on an outdated uv

[dependency-groups]
dev = [
    "qgis-manage>=0.17.0",
    "qgis-plugin-analyzer>=1.19.2",
    "ruff>=0.17",
    "mypy>=2.4",
    "pre-commit>=4.7",
    "flake8>=7.0",
    "bandit>=1.7",
    "detect-secrets>=1.4",
]

[tool.qgis-manager]
qgis_version = 4
max_backups = 1
auto_compile = false
```

### Runtime dependencies

> **Do not add `PyQt5` or `PyQt6` to `dependencies`.** QGIS provides PyQt through
> `qgis.PyQt`, and the same plugin must work with Qt5 (QGIS 3) and Qt6 (QGIS 4).
> Import from `qgis.PyQt`, never from `PyQt5`/`PyQt6` directly.

Keep `dependencies = []` unless the plugin vendors a pure-Python library. If a
third-party library is unavoidable, declare it and document how users install it;
the QGIS plugin repository does not install Python packages for you.

### Groups vs extras

- `[dependency-groups].dev` is for local/CI tooling. `uv sync` installs it by
  default.
- `[project.optional-dependencies]` is for user-selectable extras. Do not use it
  for linters.
- `uv sync --all-groups` installs every group; `uv sync --no-dev` creates a
  runtime-only environment.

---

## 5. Tool configuration: centralize only what supports it

| Tool | Where to configure | Notes |
| :--- | :--- | :--- |
| Ruff | `[tool.ruff]` | lint and format; `target-version` should match the oldest supported Python |
| mypy | `[tool.mypy]` | type-check the QGIS-agnostic code; exclude generated files |
| pytest | `[tool.pytest.ini_options]` | only if the project actually uses pytest |
| Flake8 | `.flake8` | **does not read `pyproject.toml`**; keep the file |
| Bandit | `.bandit` or `[tool.bandit]` | verify the installed Bandit version supports the chosen location |
| detect-secrets | `.secrets.baseline` | keep the baseline in version control |
| analyzer | `.analyzerignore` + `[tool.qgis-analyzer]` | analysis scope and rule options |
| QGIS packaging | `.qgisignore` | controls what goes into the plugin ZIP |

Do not force every tool into `pyproject.toml`; a tool that ignores it will
silently use defaults.

---

## 6. Makefile: a thin, reproducible wrapper

Recipes **must use tabs**, not spaces.

```makefile
.PHONY: sync test test-qgis flake8 mypy analyzer agent-validate qgis-validate package

# Keep the cache inside the workspace when $HOME is read-only.
UV_CACHE_DIR ?= $(CURDIR)/.uvcache
export UV_CACHE_DIR

sync:
	uv lock --check
	uv sync --frozen

test:
	PYTHONPATH=.. uv run --frozen python -m unittest discover tests

test-qgis:
	QT_QPA_PLATFORM=offscreen PYTHONPATH=.. python3 \
		-m unittest discover -s tests/integration -t .

flake8:
	uv run --frozen flake8 core gui freehand_plugin.py __init__.py --config .flake8

mypy:
	uv run --frozen mypy --config-file pyproject.toml --follow-imports=silent core

analyzer:
	uv run --frozen qgis-analyzer analyze . --max-cc 10

agent-validate:
	uv run --frozen python .agent/tools/forge.py validate

qgis-validate:
	uv run --frozen qgis-manage validate --strict

ZIP ?= $(shell ls -t dist/*.zip 2>/dev/null | head -1)

package:
	uv run --frozen qgis-manage package --repo-check
	uv run --frozen qgis-manage validate --zip "$(ZIP)"
```

Notes:

- Use `uv run --frozen` in CI; locally `uv run` may sync the environment.
- The test command depends on the framework: this project uses `unittest`.
- `test` is QGIS-free (integration tests skip themselves when `qgis` cannot be
  imported); `test-qgis` uses the host QGIS and is the real GUI gate.
- `qgis-manage deploy` should use `--no-compile --qgis-version 4` when the
  Makefile already compiles resources.
- Do not build docs with a single `sphinx-build` if the project has multiple
  locales or an offline QGIS help bundle.

---

## 7. Tests and QGIS isolation

QGIS plugins usually combine two test layers:

1. **Mock-first unit tests** that do not need QGIS (fast, no display).
2. **Integration tests** that run inside QGIS or a QGIS container.

Recommended commands:

```bash
# unit tests (no QGIS; integration tests are skipped automatically)
PYTHONPATH=.. uv run --frozen python -m unittest discover tests

# integration tests against the host QGIS (skipped if qgis is not importable)
QT_QPA_PLATFORM=offscreen PYTHONPATH=.. python3 \
	-m unittest discover -s tests/integration -t .

# same suite inside the QGIS container
make docker-test
```

QGIS can segfault during teardown after a successful run (exit 139). The
Makefile and CI treat 139 as success **only** when the log ends in `OK` and
contains no `FAILED`/`ERROR` lines; never ignore a non-zero exit blindly.

Do not assume `uv run pytest` is valid. If the project uses `unittest`, `pytest`
is not installed and the command fails. Add pytest only if you are deliberately
migrating the suite, and run it through `uv run` with the correct test paths.

For QGIS-only checks, use a container rather than installing QGIS into the
host/CI runner ad hoc:

```yaml
container:
  image: ghcr.io/qgis/pyqgis4-checker:main-ubuntu
```

---

## 8. Documentation

Documentation dependencies are development dependencies. Either keep them in
`dev` or create an explicit group:

```toml
[dependency-groups]
docs = [
    "sphinx>=7",
    "sphinx-rtd-theme>=2",
    "sphinx-intl>=2.3",
    "myst-parser>=2",
]
```

Install and build explicitly:

```bash
uv sync --frozen --group docs
uv run sphinx-build -M html docs/source docs/build/html
```

If the project builds multiple languages and an offline QGIS help bundle, use
its script (for example `scripts/build_docs.sh`); the one-line `sphinx-build`
example does not cover locale selection or copying `help/html/<lang>/`.

---

## 9. CI with `uv`

Use `astral-sh/setup-uv` with a pinned version, let `uv` install Python, and make
the lockfile authoritative:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.12.23"
          enable-cache: true

      - run: uv python install
      - run: uv sync --frozen
      - run: uv lock --check
      - run: PYTHONPATH=.. uv run --frozen python -m unittest discover tests
```

Avoid these common mistakes:

- `actions/setup-python` plus `uv python install`: redundant; choose one.
- Hardcoding a Python version in CI that contradicts `requires-python` or
  `.python-version`.
- `uv run` without `--frozen` in CI: it can resolve a different environment.
- `sudo apt-get install qgis`: not reproducible and often unavailable; use the
  official QGIS repository or a QGIS container.
- Running `pytest` for a project whose suite is `unittest`.

For a compatibility matrix:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
steps:
  - run: uv python install ${{ matrix.python-version }}
  - run: uv sync --frozen
  - run: PYTHONPATH=.. uv run --frozen python -m unittest discover tests
```

---

## 10. Packaging and the QGIS plugin repository

A QGIS plugin ZIP is not a Python wheel. Keep the development environment out of
the artifact.

1. **Metadata**: `metadata.txt` must contain the required fields, a numeric
   `version`, `repository`, and `qgisMaximumVersion` (for example `4.99` for the
   QGIS 4 Ready listing).
2. **Icon**: use a PNG/JPEG referenced by `icon`; SVG is **not** a valid
   `metadata.txt` icon (keep SVG as the editable master and export a PNG).
3. **Exclusions**: `.qgisignore` must exclude `.venv`, `tests`, `docs`, `scripts`,
   `.agent`, `.agent-state`, `.ai-context`, `.uvcache`, caches, `dist`, local
   configuration and the untracked upstream reference clone (`freehandEditing/`).
4. **Build and audit**:
   ```bash
   uv run qgis-manage package --repo-check
   uv run qgis-manage validate --zip dist/my-plugin.X.Y.Z.zip
   ```
5. **Security parity**:
   ```bash
   uv run qgis-manage security --portal --fail-on critical
   ```
6. **Portal upload** is manual: upload the ZIP at
   <https://plugins.qgis.org/plugins/> and wait for validation/approval.

`validate --zip` checks the ZIP root, embedded metadata, `LICENSE`, size,
binaries, development files, permissions and icon. Do not duplicate this logic in
a custom script.

---

## 11. VS Code

For a `unittest` project:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.unittestEnabled": true,
  "python.testing.pytestEnabled": false,
  "python.testing.unittestArgs": ["-v", "-s", "tests", "-p", "test_*.py"],
  "python.analysis.typeCheckingMode": "basic"
}
```

On Windows the interpreter path is `.venv\\Scripts\\python.exe`. For `pytest`,
swap the two testing flags and set `python.testing.pytestArgs`.

Optional: install the Ruff and mypy extensions and point them at the same
interpreter.

---

## 12. Pre-commit

`pre-commit` is a development tool; install it with `uv`:

```bash
uv add --group dev pre-commit
uv run pre-commit install
uv run pre-commit run --all-files
```

Hooks run in their own isolated environments. Do **not** wrap individual hook
entries in `uv run`; let pre-commit manage the hook environment. Pin every
`rev` and update deliberately with `pre-commit autoupdate`.

A QGIS plugin usually benefits from:

- Ruff lint and format;
- Flake8 scoped to the packaged plugin code (the QGIS portal checker);
- trailing whitespace, end-of-file, YAML/TOML checks;
- large-file and merge-conflict checks;
- a conventional-commit message hook.

---

## 13. Security and lockfile hygiene

- Commit `uv.lock`; review lock diffs like code.
- CI: `uv lock --check` and `uv sync --frozen`.
- Use `uv pip check` to detect inconsistent installed packages.
- Add `pip-audit` if your policy requires vulnerability scanning:
  ```bash
  uv run pip-audit
  ```
- Keep runtime `dependencies` empty unless strictly required.
- Never commit `.venv`, credentials, `.env` files or local QGIS profiles.

A merge conflict in `uv.lock` is resolved by regenerating it, not by hand-editing:

```bash
uv lock
```

---

## 14. Troubleshooting

| Symptom | Cause / fix |
| :--- | :--- |
| `No module named qgis` | QGIS is not installed or the wrong Python is used; unit tests should mock QGIS, integration tests run in QGIS/container |
| `uv lock` cannot resolve | Check `requires-python`, platform markers and conflicting pins; run `uv lock --upgrade-package <name>` deliberately |
| CI installs different versions | Use `uv sync --frozen` and `uv lock --check`; do not run `uv lock` in CI |
| `uv run` re-resolves unexpectedly | It syncs by default; use `--frozen` in automation |
| QGIS plugin ZIP contains `.venv`/tests/docs | Fix `.qgisignore`; validate with `qgis-manage validate --zip` |
| Portal warns about permissions/icon | `package --repo-check` normalizes modes; export a PNG icon ≥32 px |
| Windows path errors | Use `.venv\\Scripts\\python.exe`; avoid Unix-only shell commands in hooks |
| `uv` fails with "Read-only file system" | The sandbox exposes a read-only `$HOME` cache; set `UV_CACHE_DIR=$PWD/.uvcache` (git-ignored) |
| `No module named PyQt5` | Import from `qgis.PyQt` only; the plugin must work on Qt5 and Qt6 |
| `ImportError: QgsRubberBand` from `qgis.core` | In QGIS 4 it lives in `qgis.gui`; `QgsSnappingUtils` lives in `qgis.core` |
| `QAction` import error | Import it from `qgis.PyQt.QtGui` in PyQt6, with a `QtWidgets` fallback for PyQt5 (`gui/qt_compat.py`) |
| `supportsQt6` warning | Deprecated by qgis-manage 0.17 for QGIS 4; `qgisMaximumVersion >= 4.0` marks QGIS 4 Ready |

---

## 15. Acceptance checklist

- [ ] Tests pass before and after the migration.
- [ ] `uv.lock` is committed and `uv lock --check` passes.
- [ ] `uv sync --frozen` creates the environment from scratch.
- [ ] `requires-python` and `.python-version` follow the documented policy.
- [ ] Runtime `dependencies` are empty or explicitly justified.
- [ ] Tool-specific config files are preserved where `pyproject.toml` is unsupported.
- [ ] Makefile uses tabs and runs through `uv`.
- [ ] CI uses `setup-uv` pinned, `--frozen`, and the real test command.
- [ ] QGIS is provided by a container/repository, not by `apt-get install qgis`.
- [ ] The plugin ZIP excludes development files and passes `validate --zip`.
- [ ] `make test-qgis` passes against a real QGIS (or `make docker-test`).
- [ ] `make agent-validate` passes with `strict_agent_system = true`.
- [ ] The plugin loads, previews and exports in the target QGIS version.

# Implementation Plan — Green CI on the Hyphenated Checkout

> **Status: IMPLEMENTED** — approved by the user on 2026-11-20; CI verification
> pending. No tag is created until GitHub Actions is green.
>
> Version: 2.0.0 (release blocker fix) | Date: 2026-11-20
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Goal

Make GitHub Actions green on the real checkout so `/release-plugin` can proceed.

The plugin code is green locally, but CI checks out the repository as
`freehand-digitize` (hyphen), while the Python package is
`freehand_digitize` (underscore). The local workspace is named
`freehand_digitize`, which is why `PYTHONPATH=..` works locally and fails on CI.

---

## 2. Evidence

GitHub run [44681312467](https://github.com/geociencio/freehand-digitize/actions/runs/44681312467)
on `main` (`1c17da3`):

| Job | Result | Cause |
| :--- | :--- | :--- |
| Qt6 enum check | ✅ success | — |
| Lint, types, agent system and metadata | ❌ failure | Ruff `N999` and import-sort differences caused by the `freehand-digitize` root name. |
| Unit tests (mock-free) | ❌ failure | `ModuleNotFoundError: No module named 'freehand_digitize'` from `tests/core/*` with `PYTHONPATH=..`. |
| Integration tests (QGIS) | ⏭ skipped | Depends on the failed quality job. |

Representative CI errors:

```text
N999 Invalid module name: 'freehand-digitize'
--> __init__.py:1:1

ModuleNotFoundError: No module named 'freehand_digitize'
File ".../freehand-digitize/freehand-digitize/tests/core/test_constants.py"
```

Ruff also reports `I001` in test modules because, without a first-party
declaration, `freehand_digitize` is sorted as a third-party import when the
checkout directory is hyphenated.

Local gates (`make pre-release`, `make zip`, `make portal-check`,
`make security-scan`, `make qt6-check`, `make docker-test`) are green; the failure
is specific to the CI checkout layout.

---

## 3. Scope and non-goals

### In scope

- A CI-only package exposure step:
  `$RUNNER_TEMP/plugin-root/freehand_digitize -> $GITHUB_WORKSPACE`.
- A configurable `TEST_PYTHONPATH` in the Makefile (default `..`, preserving
  local behavior) used by `test` and `test-qgis`.
- Ruff first-party configuration and an `N999` exception for `__init__.py`
  files (the hyphen is in the repository directory, not in a module name).
- Unit-test step in CI using the exposed path.
- Correct the stale release workflow notes (translation catalogs are shipped).

### Non-goals

- Renaming the GitHub repository or the plugin package.
- Changing the ZIP layout or the Docker integration layout (Docker already
  copies into `/app/freehand_digitize`).
- Product-code changes.
- QGIS 3.28 smoke test (separate release check).

---

## 4. Design

### Makefile

```make
TEST_PYTHONPATH ?= ..

test:
	PYTHONPATH=$(TEST_PYTHONPATH) $(UV_RUN) python -m unittest discover tests

test-qgis:
	@QT_QPA_PLATFORM=offscreen PYTHONPATH=$(TEST_PYTHONPATH) $(PYTHON) ...
```

Local default stays `..`; CI can override. `pre-release` continues to call
`test`/`test-qgis` with the same default.

### CI unit-test job

```yaml
- name: Expose the plugin package for the hyphenated checkout
  run: |
    mkdir -p "$RUNNER_TEMP/plugin-root"
    ln -sfn "$GITHUB_WORKSPACE" "$RUNNER_TEMP/plugin-root/freehand_digitize"

- run: PYTHONPATH="$RUNNER_TEMP/plugin-root" uv run --frozen python -m unittest discover tests
```

The symlink is inside `RUNNER_TEMP`, not in the repository; no tracked file is
added.

### Ruff

```toml
[tool.ruff.lint.isort]
known-first-party = ["freehand_digitize"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401", "D104", "N802", "N999"]
```

This makes import sorting identical locally and in CI and suppresses `N999` only
for package marker files whose parent directory is the repository name. It does
not suppress naming errors in code modules.

### Release workflow

Update `.agent-state/workflows/release-plugin.md`:

- remove “no translation catalogs in 2.0.0”;
- include `i18n/*.qm` in the expected ZIP contents;
- add “GitHub Actions green on `main`” to the release gates.

---

## 5. Verification

Local:

```bash
make test
make test-qgis
make pre-release
make zip
make portal-check
```

CI simulation (optional, no tracked files):

```bash
mkdir -p /tmp/plugin-root
ln -sfn "$PWD" /tmp/plugin-root/freehand_digitize
PYTHONPATH=/tmp/plugin-root uv run --frozen python -m unittest discover tests
```

Remote:

```bash
git push origin main
gh run watch
```

The release proceeds only when all GitHub Actions jobs are green.

---

## 6. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| Symlink not followed on a runner | `ln -sfn` and `PYTHONPATH` set explicitly; verify in CI. |
| Makefile change breaks local tests | Default `TEST_PYTHONPATH ?= ..` preserves the current behavior. |
| `N999` ignore hides a real naming error | Only `__init__.py` files are ignored; module files remain checked. |
| Import-sort flip-flop between local/CI | `known-first-party` makes both environments deterministic. |
| CI still red for an unrelated reason | Check `gh run view --log-failed`; do not tag until green. |
| Release workflow still claims no catalogs | Update it in the same change. |

---

## 7. Acceptance criteria

- [ ] `make test` and `make test-qgis` pass locally with the default.
- [ ] CI unit tests pass in the hyphenated checkout.
- [ ] CI Ruff passes with no `N999`/`I001`.
- [ ] CI integration job runs and passes.
- [ ] `make pre-release`, `make zip`, `make portal-check` still pass.
- [ ] Release workflow reflects catalogs and CI green.
- [ ] No tag/upload until the CI run is green.

---

## 8. Procedure

1. Update `pyproject.toml` Ruff config.
2. Update `Makefile` with `TEST_PYTHONPATH`.
3. Update `.github/workflows/test.yml` with the symlink + `PYTHONPATH`.
4. Update the release workflow notes.
5. Run local tests and the CI simulation.
6. Commit (`ci: make tests work on the hyphenated checkout`), push.
7. Wait for GitHub Actions; tag only after green.

---

## 9. Results

- Ruff: `known-first-party = ["freehand_digitize"]`; `N999` ignored only for
  `__init__.py`.
- Makefile: `TEST_PYTHONPATH ?= ..`; `test`/`test-qgis` use it. `mypy` uses
  `--explicit-package-bases` so the hyphenated checkout root is not treated as a
  package.
- CI unit job exposes `$RUNNER_TEMP/plugin-root/freehand_digitize` and sets
  `PYTHONPATH` to that root.
- Release workflow updated for `i18n/*.qm` and CI-green as a gate.
- Local hyphenated-checkout simulation: Ruff and 134 unit tests pass.
- `make pre-release` passes.
- Remote GitHub Actions verification pending.
- **Commit:** to be filled by the CI-fix commit.

---

## 10. Approval

The plan is **PROPOSED**. Implementation starts only after the user approves the
CI/Makefile changes.

Release status after approval:

1. Fix CI and get a green run.
2. Run the QGIS 3.28 smoke test (or raise `qgisMinimumVersion`).
3. Tag `v2.0.0` and publish the ZIP.

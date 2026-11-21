# Implementation Plan — QGIS Integration Test Gate

> **Status: IMPLEMENTED (2026-11-21)** — approved and implemented; no version
> bump.
>
> Type: QA/tooling patch (no plugin runtime change) | Date: 2026-11-21
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Problem

`make test-qgis` can report success while running **zero real integration tests**.

Reproduction on this machine:

```bash
PATH=$PWD/.venv/bin:$PATH make test-qgis
# Ran 81 tests ... OK (skipped=81)
# exit code 0
```

The virtualenv is first in `PATH`, so the Makefile's `PYTHON ?= python3` resolves
to `.venv/bin/python3`, which has no QGIS. Every integration module is decorated
with `@requires_qgis` and is skipped, but `unittest` still exits 0. The same
happens through:

```bash
uv run python .agent/tools/forge.py project test-full
# Ran 81 tests ... OK (skipped=81)
```

With the system interpreter the suite really runs:

```bash
/usr/bin/python3 -m unittest discover -s tests/integration -t .
# Ran 81 tests ... OK
```

This makes `make test-qgis` and `make pre-release` untrustworthy in a virtualenv:
a regression in the QGIS path can pass locally.

---

## 2. Goal

Guarantee that `make test-qgis`:

1. uses a Python interpreter that can import QGIS;
2. **fails** if QGIS is unavailable, instead of skipping the whole integration
   suite;
3. keeps `make test` working without QGIS (unit tests only);
4. behaves the same in Docker/CI.

No plugin runtime code changes. No version bump is required: Makefile, tests and
developer tooling are not shipped in the ZIP. (A release is optional and would be
a QA-only patch.)

---

## 3. Design

### 3.1 Interpreter resolution

Add `scripts/find_qgis_python.py`:

- If `QGIS_PYTHON` is set, test it first.
- Otherwise try, in order:
  `python3`, `/usr/bin/python3`, `/usr/local/bin/python3`, `python`,
  `python3.12`, `python3.11`, `python3.10`.
- For each candidate, run:
  `candidate -c "import qgis"` with a short timeout.
- Print the first working interpreter path; exit non-zero if none.

Makefile:

```make
QGIS_PYTHON ?= $(shell $(UV_RUN) python scripts/find_qgis_python.py 2>/dev/null)

test-qgis:
	@test -n "$(QGIS_PYTHON)" || \
	  (echo "❌ No QGIS Python found. Set QGIS_PYTHON=/path/to/qgis/python3."; exit 1)
	@QT_QPA_PLATFORM=offscreen REQUIRE_QGIS=1 \
	  PYTHONPATH=$(TEST_PYTHONPATH) $(QGIS_PYTHON) \
	  -m unittest discover -s tests/integration -t .
```

- The existing 139 exit tolerance stays.
- `QGIS_PYTHON` remains overridable.
- `make test` keeps using `TEST_PYTHONPATH` and no `REQUIRE_QGIS`.

### 3.2 Explicit gate test

Add `tests/integration/test_qgis_gate.py`:

```python
@unittest.skipUnless(
    os.environ.get("REQUIRE_QGIS") == "1",
    "integration gate only under make test-qgis",
)
class TestQGISGate(unittest.TestCase):
    def test_qgis_is_importable(self):
        import qgis  # noqa: F401
```

- `make test-qgis` sets `REQUIRE_QGIS=1`; if QGIS cannot be imported, this test
  fails and the target returns non-zero.
- `make test` does not set it; the gate is skipped, so the unit suite remains
  QGIS-free.
- Docker/CI sets `REQUIRE_QGIS=1` so the container also proves QGIS is present.

### 3.3 Docker/CI

- `Dockerfile`: add `ENV REQUIRE_QGIS=1` for the test image.
- `.github/workflows/test.yml`: no change needed for the Docker integration job;
  it runs the image command. Quality job keeps `make`/ruff as-is.
- `make docker-test`: pass `-e REQUIRE_QGIS=1` for clarity, or rely on the image
  env; the plan uses the image env and also passes it explicitly.

### 3.4 Developer documentation

- `AGENTS.md` / README command notes: explain `QGIS_PYTHON` and the
  `REQUIRE_QGIS=1` gate.
- Update `docs/maintainer/LOGGING_GUIDELINES.md` test counts if the gate test
  changes the skipped count.
- No CHANGELOG entry: developer tooling, not a user-facing plugin change.

---

## 4. Tests and verification

### Local

```bash
make test                         # unit only; QGIS gate skipped
make test-qgis                    # 82 tests: 81 integration + gate
PATH=$PWD/.venv/bin:$PATH make test-qgis
# must FAIL with "No QGIS Python found" or a QGIS import failure
/usr/bin/python3 -m unittest discover -s tests/integration -t .  # 81 OK
```

### Docker

```bash
make docker-test                  # 82 tests, REQUIRE_QGIS=1
```

### Static

```bash
make lint
make pre-release                  # must still pass with QGIS_PYTHON resolved
make zip
make security-scan
make qt6-check
```

### CI

The integration job builds the Docker image and runs the suite; it must be green.

---

## 5. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| `find_qgis_python.py` slow | It only runs when the Makefile expands `QGIS_PYTHON`; candidates are quick imports. |
| Windows/macOS paths differ | `QGIS_PYTHON` override is documented; candidates include `python`/`python3`. |
| `make pre-release` fails on a venv-only machine | Intended: it must not silently skip QGIS. The message tells the user to set `QGIS_PYTHON`. |
| Test count changes | Gate adds one skipped test to `make test` (139/82) and one executed test to `make test-qgis` (82). Update metrics/docs. |
| Container gate fails if QGIS import path differs | QGIS image already sets `PYTHONPATH`; verify in `make docker-test`. |
| QGIS teardown 139 | Keep the existing tolerance; the gate test itself runs before teardown issues. |

---

## 6. Acceptance criteria

- [ ] `make test-qgis` fails when QGIS is unavailable.
- [ ] `make test-qgis` passes with QGIS and runs 82 tests (81 + gate).
- [ ] `PATH=.venv/bin:$PATH make test-qgis` fails clearly; no false green.
- [ ] `make test` remains QGIS-free and green.
- [ ] `make docker-test` runs the gate with QGIS.
- [ ] `make pre-release`, `make zip`, security and Qt6 still pass.
- [ ] `QGIS_PYTHON` override is documented.

---

## 7. Procedure

1. Add `scripts/find_qgis_python.py` and the gate test.
2. Update the Makefile `test-qgis` target and Docker env.
3. Verify the false-green case fails and the real case passes.
4. Update docs/state; run `make pre-release`, `make docker-test`, `make zip`.
5. Commit (`test: fail when QGIS integration tests are skipped`), push, verify CI.
6. No version bump or portal upload required.

---

## 8. Out of scope

- Guarding the residual deleted-layer paths in `FeatureCreator`,
  `ReshapeCreator` and `FreehandTool` (separate P1 plan).
- Refactoring `FreehandDigitizePlugin`.
- A QGIS 3.28/Qt5 smoke test.

---

## 9. Results

- Added `scripts/find_qgis_python.py` (auto-detect + `QGIS_PYTHON` override).
- `make test-qgis` sets `REQUIRE_QGIS=1` and selects the QGIS interpreter.
- Added `tests/integration/test_qgis_gate.py`; the gate fails if QGIS is absent.
- Dockerfile and `make docker-test` set `REQUIRE_QGIS=1`.
- `make test`: 139 tests (57 unit + 82 skipped).
- `make test-qgis` / `forge test-full`: 82 tests OK.
- `QGIS_PYTHON=.venv/bin/python3 make test-qgis` fails explicitly.
- `make docker-test`: 82 OK; `make pre-release`: OK.
- **Commit:** to be filled by the gate commit.

---

## 10. Approval

The plan is **PROPOSED**. Implementation starts only after the user approves:

1. Auto-detect the QGIS interpreter with `QGIS_PYTHON` override (recommended),
   or require the user to set `QGIS_PYTHON` explicitly?
2. Add the gate test (recommended) or only preflight `import qgis` in the
   Makefile?

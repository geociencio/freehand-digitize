# Implementation Plan — Versioned Release Notes

> **Status: IMPLEMENTED (2026-11-22)** — notes, validator and workflow updated;
> no plugin version bump.
>
> Type: docs/release process | Plugin version: unchanged (**2.0.2**)
> Date: 2026-11-22 | Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Current state

Freehand Digitize has **no `docs/releases/` directory** and no
`RELEASE_NOTES_vX.Y.Z.md` files.

Release notes currently exist only:

- in the GitHub Release body, passed inline with `gh release create --notes`;
- summarized in `CHANGELOG.md` and `metadata.txt` → `changelog=`.

The release workflow (`.agent-state/workflows/release-plugin.md`) does not
create or validate a release-note file, and Phase 5 publishes without
`--notes-file`.

`sec_interp` has the mature convention:

```text
docs/releases/notes/vX.Y.Z.md
```

with a workflow step, a `release-management` skill rule and
`gh release create --notes-file ...`.

---

## 2. Goal

Make every Freehand release have a versioned, reviewable note:

```text
docs/releases/
  README.md
  RELEASE_NOTES_TEMPLATE.md
  notes/
    v2.0.0.md
    v2.0.1.md
    v2.0.2.md
    v2.1.0.md        # only when the release gate opens
```

The note is the GitHub Release body; `CHANGELOG.md` remains the compact
changelog and `metadata.txt` the portal summary.

No plugin runtime change and **no version bump**. This is process/documentation
work, except for the small validation script and its test.

---

## 3. Design

### 3.1 Directory and naming

- Current convention only: `docs/releases/notes/vX.Y.Z.md`.
- Do **not** add the legacy `docs/releases/RELEASE_NOTES_vX.Y.Z.md` naming.
- File names use the exact numeric version, no `v` duplication:
  `notes/v2.0.2.md` for tag `v2.0.2`.
- Release notes are **English** (user-facing), matching README/CHANGELOG.

### 3.2 Template

`docs/releases/RELEASE_NOTES_TEMPLATE.md`:

```markdown
# Freehand Digitize vX.Y.Z — Short title

**Release date:** YYYY-MM-DD
**Compatibility:** QGIS 3.28–4.x (Qt5/Qt6), Python 3.9+
**Artifacts:** `freehand_digitize.X.Y.Z.zip`, `.sha256`

## Highlights

- ...

## Changes

### Added

- ...

### Fixed

- ...

### Changed

- ...

## Verification

- Tests: N (unit + integration).
- Gates: pre-release, Docker, security, Qt6.
- CI run: ...

## Upgrade notes

- ...

## Links

- Repository: ...
- Changelog: ...
```

### 3.3 Backfill

Create three historical notes from the existing GitHub releases/CHANGELOG:

| File | Content |
| :--- | :--- |
| `notes/v2.0.0.md` | Full parity, reshape, sampling, edit-session gating, feature difference, i18n catalog. |
| `notes/v2.0.1.md` | Deleted-layer lifecycle fix (`sip` + `destroyed`), unload and pick-tool cleanup. |
| `notes/v2.0.2.md` | P1 deleted-layer guards in creators/tool/callbacks, tests, and the pre-i18n state; 2.0.2 was released before the i18n change. |

Do **not** create `v2.1.0.md` yet: 2.1.0 is implemented but release-gated by the
portal sequence.

### 3.4 Validation script

Add `scripts/check_release_notes.py`:

```bash
python scripts/check_release_notes.py --version 2.0.2
# default: read version from metadata.txt
```

Checks:

1. `docs/releases/notes/v<version>.md` exists.
2. First `#` heading contains `Freehand Digitize v<version>`.
3. Required sections: `## Highlights`, `## Verification`.
4. No placeholders: `TODO`, `TBD`, `{version}`, `YYYY-MM-DD`, `pendiente`.
5. Compatibility line mentions QGIS.
6. Version in the heading matches the requested/metadata version.

Exit non-zero with a concrete message. It does not need QGIS.

Add `make release-notes-check` and include it in `pre-release` so a version
cannot be released without its note.

Add `tests/test_release_notes.py` (unit, no QGIS), covering:

- valid note passes;
- missing note fails;
- placeholder fails;
- version mismatch fails.

Expected suite: **~150 tests** (61 unit + 89 integration); exact count recorded
after implementation.

### 3.5 Workflow update

`.agent-state/workflows/release-plugin.md`:

- Phase 2 table: add `docs/releases/notes/vX.Y.Z.md` as a required release file.
- Phase 2 prose: use `changelog-generator`, write the note, run
  `make release-notes-check`.
- Phase 5: replace inline notes with
  `gh release create vX.Y.Z --notes-file docs/releases/notes/vX.Y.Z.md ...`.
- Update the stale ZIP list (`i18n/freehand_digitize_en.qm` → all six `.qm`
  catalogs; no `i18n/*.ts`).

`docs/releases/README.md`:

- naming convention and template;
- command to validate;
- command to publish;
- “do not edit the GitHub body by hand” rule.

Update `AGENTS.md` key resources and README docs index.

### 3.6 Release sequencing

Unchanged:

1. 2.0.1 portal approval.
2. Upload the **existing GitHub 2.0.2 ZIP** to the portal.
3. 2.0.2 portal approval.
4. 2.1.0 bump/tag/release and `notes/v2.1.0.md`.

This plan does not create a tag, release, ZIP or portal upload.

---

## 4. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| Notes drift from the actual release | Validator checks version/headings; note committed before tag. |
| Two competing naming conventions | Only `notes/vX.Y.Z.md`; README forbids legacy `RELEASE_NOTES_v*`. |
| `pre-release` fails during development | Backfill 2.0.2 before wiring the check; future versions create the note before bumping. |
| Duplicate sources of truth | Release note = GitHub body; `CHANGELOG.md` = compact history; `metadata.changelog` = portal summary. |
| Backfilled notes invented | Derive from GitHub releases and CHANGELOG; label historical verification accurately. |
| Test count churn | Unit tests for the checker; update metrics after implementation. |
| ZIP includes notes | `.qgisignore` already excludes `docs/`; verify in the next release ZIP. |

---

## 5. Acceptance criteria

- [ ] `docs/releases/README.md` and template exist.
- [ ] `notes/v2.0.0.md`, `v2.0.1.md`, `v2.0.2.md` exist and are accurate.
- [ ] `scripts/check_release_notes.py` passes for 2.0.2 and catches failures.
- [ ] `make release-notes-check` works and is part of `make pre-release`.
- [ ] Release workflow uses `--notes-file` and lists all six `.qm` catalogs.
- [ ] Tests pass (expected ~150); Docker/pre-release green.
- [ ] No plugin version bump, tag or portal upload.
- [ ] `v2.1.0.md` is not created until the release gate opens.

---

## 6. Procedure

1. Create `docs/releases/` README/template and backfill the three notes.
2. Add the checker and unit tests.
3. Add the Makefile target and pre-release dependency.
4. Update the release workflow, AGENTS and README index.
5. Run `make release-notes-check`, `make test`, `make pre-release`.
6. Commit `docs: add versioned release notes`; no tag.

---

## 7. Results

- Added `docs/releases/README.md`, `RELEASE_NOTES_TEMPLATE.md` and notes
  `v2.0.0`, `v2.0.1`, `v2.0.2`.
- Added `scripts/check_release_notes.py` and `make release-notes-check`
  (included in `pre-release`).
- Added four unit tests for the validator (150 tests total: 61 unit + 89
  integration).
- Updated the release workflow to use `--notes-file`, list all six `.qm`
  catalogs and run the note check.
- Added `tests/run_integration.py` to flush Qt `DeferredDelete` objects before
  exit; `make test-qgis` and the Docker/CI command use it (10/10 stable local
  runs).
- No plugin version bump, tag, ZIP or portal upload.
- **Commit:** `176f25c chore(release): add versioned notes and stable test runner`.

---

## 8. Approval

The plan is **PROPOSED**. Implementation starts only after approval.

1. Adopt `docs/releases/notes/vX.Y.Z.md` only (recommended).
2. Backfill 2.0.0, 2.0.1 and 2.0.2.
3. Add the validator and wire it into `pre-release`.
4. Keep the 2.1.0 release gate unchanged.

Do you approve this plan?

# Session 2026-11-22 — Repository Analysis and Two Plans

> Internal session record. No plugin code changed. The two plans remain
> **PROPOSED** and await explicit approval.

## Scope

- Analyzed the attached SecInterp docs guide against Freehand's real structure.
- Researched QGIS plugin publication, QGIS Cookbook, GitHub Actions security,
  Keep a Changelog, Diátaxis and OpenSSF Scorecard.
- Reviewed the manual code-review findings (terminal snapping, negative/zero
  FIDs, no-overlap difference, display labels).
- Created:
  - `docs/maintainer/PLAN_SNAPPING_PICK_FIXES.md`
  - `docs/maintainer/PLAN_DOCS_CI_HARDENING.md`
- No code, tests, CI, metadata or catalogs changed.

## Key recommendations

- Do not copy SecInterp's Sphinx/mirrors/doc-i18n; adapt principles only.
- Fix the two user-visible bugs before 2.1.0.
- Harden CI (permissions, pinned actions, release-note gate).
- Ship `.ts` catalogs, add sample data, verify QGIS 3.28.
- Update the stale docs style guide and add a docs index plus
  contribution/security/support files.

## Verification

| Gate | Result |
| :--- | :--- |
| `make docs-check` | 39 documents at plan creation |
| `make test` | 150 |
| `make test-qgis` | 89 |
| `make pre-release` | pending final close run |
| CI | previous code run green |

## Decisions and gates

- No plugin version bump: still **2.0.2**.
- No tag, ZIP or portal upload.
- Portal: 2.0.0 approved; 2.0.1 pending; 2.0.2 GitHub-only.
- 2.1.0 remains gated until 2.0.2 is public in the portal.
- The two plans need explicit approval before implementation.

## Commits of note

- `61898d3` — add the two proposed plans.
- Previous: `089d51f` — close session i18n_release_notes.

## Pending

- Approve/adjust the plans.
- Portal 2.0.1/2.0.2 sequence.
- QGIS 3.28 smoke test.

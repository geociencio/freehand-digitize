# Session 2026-11-22 — English i18n Base and Release Notes

> Internal session record. Plugin version stays **2.0.2**; the i18n work is
> unreleased and the portal sequence is unchanged.

## Scope

- Inverted the UI source language to English and shipped `es`, `pt_BR`, `fr`,
  `de`, `it` and `id` catalogs.
- Preserved the previous Spanish wording exactly from the old English catalog.
- Added the versioned release-notes system and backfilled 2.0.0–2.0.2.
- Added a validator, four unit tests and the `release-notes-check` gate.
- Stabilized QGIS teardown with `tests/run_integration.py` (`DeferredDelete`).

## Verification

| Gate | Result |
| :--- | :--- |
| `make test` | 150 (61 unit + 89 integration skipped) |
| `make test-qgis` | 89 OK; 10/10 stable runs |
| `make docker-test` | 89 OK |
| `make pre-release` | OK |
| Release-note validator | 2.0.0, 2.0.1, 2.0.2 pass |
| CI | run 45030146512 green |

## Artifacts and decisions

- Version remains **2.0.2**; no tag, ZIP or portal upload for i18n.
- `docs/releases/notes/v2.0.0.md`, `v2.0.1.md`, `v2.0.2.md`.
- `v2.1.0.md` is not created until 2.0.2 is public in the portal.
- Portal: 2.0.0 approved; 2.0.1 pending; 2.0.2 GitHub-only.

## Commits of note

- `1cf3165` — English i18n source + six catalogs.
- `9e624a6` — i18n implementation record.
- `7bf5a60` — release-notes plan.
- `176f25c` — release notes + stable runner.
- `a492694` — release-notes implementation record.

## Pending

- 2.0.1 portal approval; upload 2.0.2 with the original GitHub artifact.
- 2.1.0 release gate; create `v2.1.0.md` at that point.
- Documentation drift; roadmap Stage 1; QGIS 3.28 smoke.

# Session 2026-11-20 — Release 2.0.0 and Portal Submission

> Internal session record (Spanish allowed). Release status: **uploaded to
> plugins.qgis.org, approval pending**.

## Scope

- Finished the 2.0.0 feature set: reshape, vertex sampling (pixels/layer units),
  edit-session gating and feature difference (selection or mouse picking).
- Fixed GitHub Actions on the hyphenated checkout.
- Released `v2.0.0`: tag, GitHub Release, ZIP and portal upload.
- Approved the staged 2.1.0/2.2.0/2.3.0 roadmap; no stage started.

## Verification

| Gate | Result |
| :--- | :--- |
| `make test` | 134 tests (57 unit; 77 integration skipped without QGIS) |
| `make test-qgis` | 77 tests OK (QGIS 4.2.2/Qt6) |
| `make docker-test` | 77 tests OK (QGIS 3.99/Qt5) |
| `make pre-release` | OK |
| `make security-scan` | 0 findings |
| `make qt6-check` | 0 enum errors |
| CI | run 44684907873 green (quality, unit, Qt6, integration) |

## Release artifacts

- Tag: `v2.0.0` (`f35f090`).
- ZIP: `dist/freehand_digitize.2.0.0.zip`.
- SHA256: `2faa4a4542f8bb041e1c1823e5eff7f22227671bb6b000a06bb297c60ef37b5d`.
- GitHub Release: <https://github.com/geociencio/freehand-digitize/releases/tag/v2.0.0>.
- Portal: <https://plugins.qgis.org/plugins/freehand_digitize/> — uploaded,
  **pending approval**.

## Commits of note

- `dcfb191` sampling + edit-session gating.
- `28baa15` feature difference.
- `0d6e0ae`, `99adabe` CI fixes.
- `f35f090` author update.
- `4768264` staged roadmap approved.

## Pending

- Portal approval (external).
- Optional QGIS 3.28 smoke test; the ZIP declares 3.28.
- Start Stage 1 (Backspace) only after an explicit kickoff.

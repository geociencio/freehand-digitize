# Session 2026-11-21 — Layer Lifecycle Fix and 2.0.1

> Internal session record. Portal status: **2.0.0 approved; 2.0.1 published on
> GitHub but not uploaded to the portal**.

## Scope

- Fixed `RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been
  deleted` when the active layer was removed.
- Added `sip.isdeleted` guards, cleared the editing reference before
  disconnecting signals, and connected the layer `destroyed` signal.
- Released and deployed **2.0.1**.
- Confirmed **2.0.0** is approved and public on plugins.qgis.org (plugin ID 7091).

## Verification

| Gate | Result |
| :--- | :--- |
| `make test` | 138 tests (57 unit; 81 integration) |
| `make test-qgis` | 81 OK (QGIS 4.2.2/Qt6) |
| `make docker-test` | 81 OK (QGIS 3.99/Qt5) |
| Agent framework tests | 37 passed (ephemeral pytest) |
| `make pre-release` | OK |
| CI | green on the 2.0.1 fix/docs commits |

## Artifacts

- Tag: `v2.0.1`.
- ZIP: `dist/freehand_digitize.2.0.1.zip`.
- SHA256: `63c6d36e39aee87bec850f9b871643263215bf9401628e540b1f1fbf5d492fdb`.
- GitHub Release: <https://github.com/geociencio/freehand-digitize/releases/tag/v2.0.1>.
- Portal: <https://plugins.qgis.org/plugins/freehand_digitize/> — 2.0.0 approved;
  2.0.1 pending manual upload.

## Commits of note

- `bd6bc35` — lifecycle fix.
- `687b441` — 2.0.1 release record.
- `5820b0a` — portal approval record.

## Pending

- Upload 2.0.1 to plugins.qgis.org.
- Optional QGIS 3.28 smoke test.
- Feature roadmap approved; no stage started.

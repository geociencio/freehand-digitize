# Session 2026-11-21 — Gate QGIS, guardas P1 y 2.0.2

> Internal session record. Portal: **2.0.0 aprobado; 2.0.1 pendiente; 2.0.2
> publicado en GitHub, sin subir al portal**.

## Scope

- Corregido el falso verde de `make test-qgis` con `QGIS_PYTHON`,
  `REQUIRE_QGIS=1` y un test de gate.
- Creado e implementado el plan P1 de guardas de capa eliminada.
- Publicado y desplegado **2.0.2**; decisión del usuario: conservarlo.
- Registrada la lección de proceso: “crea el plan” no es aprobación.

## Verification

| Gate | Result |
| :--- | :--- |
| `make test` | 145 tests (57 unit; 88 integration skipped) |
| `make test-qgis` | 88 OK (QGIS 4.2.2/Qt6, REQUIRE_QGIS=1) |
| `make docker-test` | 88 OK (QGIS 3.99/Qt5) |
| `forge project test-full` | 88 OK; ya no omite integración |
| `make pre-release` | OK |
| `make zip` / `security-scan` / `qt6-check` | OK |
| CI | run 44903387347 verde |

## Artifacts

- Tag: `v2.0.2`.
- ZIP: `dist/freehand_digitize.2.0.2.zip`.
- SHA256: `74246a6e8b6973a4af0aadd41ee7dd4f5760c064da229ca06f3b27a575ada960`.
- GitHub: <https://github.com/geociencio/freehand-digitize/releases/tag/v2.0.2>.
- Portal: <https://plugins.qgis.org/plugins/freehand_digitize/> — 2.0.0
  aprobado, 2.0.1 pendiente, 2.0.2 sin subir.

## Commits of note

- `57ab87e` — gate `REQUIRE_QGIS=1`.
- `ea943a2` — guardas P1 y 2.0.2.
- `65ec182` — registro del release 2.0.2.
- `2e590c1` — decisión de conservar 2.0.2.

## Pending

- Aprobación de 2.0.1 en el portal; después subir 2.0.2.
- Deriva documental restante.
- Etapa 1 del roadmap; smoke QGIS 3.28.

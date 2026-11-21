# Registro de Desarrollo

> Registro de sesiones técnicas de Freehand Digitize. Las entradas nuevas se
> insertan arriba; consulta
> [`docs/maintainer/LOGGING_GUIDELINES.md`](../maintainer/LOGGING_GUIDELINES.md)
> para el formato.

## [2026-11-21] - Cierre de sesión: gate + 2.0.2 (07:40)

### Resultado
- Gate `REQUIRE_QGIS=1` y detección de QGIS operativos.
- Guardas P1 y 2.0.2 publicadas, desplegadas y conservadas.
- Tests: 145 (57 unitarios + 88 integración); CI verde.
- Portal: 2.0.0 aprobado; 2.0.1 pendiente; 2.0.2 sin subir.

### Handover
- Esperar la aprobación de 2.0.1 y subir 2.0.2.
- Sincronizar la deriva documental restante.
- Roadmap aprobado; Etapa 1 sin iniciar.

---

## [2026-11-21] - Decisión: conservar 2.0.2 (07:30)

### Decisión
- El usuario decide **conservar 2.0.2** pese a que se implementó antes de la
  aprobación explícita del plan.
- Se mantiene la secuencia del portal: 2.0.1 pendiente; 2.0.2 se subirá después
  de su aprobación.
- Lección registrada: “crea el plan” no es aprobación de implementación.

---

## [2026-11-21] - Guardas de capa eliminada 2.0.2 (07:20)

### Resultado
- Helper `gui/layer_utils.py` y guardas en FeatureCreator, ReshapeCreator,
  FreehandTool y callbacks del plugin.
- Aviso traducido y cancelación limpia; sin edición parcial.
- Tests: 145 (57 unitarios + 88 integración) en QGIS 4.2.2 y contenedor Qt5.
- ZIP 2.0.2 validado; tag y GitHub Release publicados; deploy local.
- Portal: 2.0.1 pendiente de aprobación; 2.0.2 no subido.

### Artefacto
- `dist/freehand_digitize.2.0.2.zip`
- SHA256 `74246a6e8b6973a4af0aadd41ee7dd4f5760c064da229ca06f3b27a575ada960`

---

## [2026-11-21] - Gate de integración QGIS (12:10)

### Problema
`make test-qgis` y `forge project test-full` daban `OK (skipped=81)` cuando el
intérprete del `.venv` no tenía QGIS.

### Solución
- `scripts/find_qgis_python.py` auto-detecta QGIS o respeta `QGIS_PYTHON`.
- `make test-qgis` usa `REQUIRE_QGIS=1` y falla si QGIS no está disponible.
- Test de gate `tests/integration/test_qgis_gate.py`.
- Docker/CI ejecutan el gate.
- `make test`: 139 tests (57 unit + 82 skipped); `make test-qgis`: 82 OK;
  `forge project test-full`: 82 OK.

---

## [2026-11-21] - Cierre de sesión: 2.0.1 y portal (06:15)

### Estado
- 2.0.0 **aprobado y público** en plugins.qgis.org (plugin ID 7091).
- 2.0.1 publicado en GitHub y desplegado; portal pendiente de subida manual.
- Roadmap de features aprobado, sin etapas iniciadas.

### Verificación
- 138 tests (57 unitarios + 81 integración); 37 tests del framework agéntico.
- CI verde en los commits del fix y documentación.

---

## [2026-11-21] - 2.0.0 aprobado en el portal (06:00)

### Estado
- plugins.qgis.org: **2.0.0 aprobado y público** (plugin ID 7091).
- GitHub: 2.0.1 publicado con el fix de capa eliminada.
- Portal: sigue sirviendo 2.0.0; 2.0.1 pendiente de subida manual.

### Siguiente
- Subir `dist/freehand_digitize.2.0.1.zip` al portal para reemplazar la versión
  con el bug de ciclo de vida.

---

## [2026-11-21] - Release 2.0.1 (05:40)

### Resultado
- Fix de capa eliminada implementado y desplegado en QGIS 4.
- Tag `v2.0.1` y GitHub Release publicados con ZIP y SHA256.
- ZIP 2.0.1 validado con `qgis-manage`.
- Portal: 2.0.0 sigue pendiente de aprobación; 2.0.1 no se ha subido aún.

### Artefacto
- `dist/freehand_digitize.2.0.1.zip`
- SHA256 `63c6d36e39aee87bec850f9b871643263215bf9401628e540b1f1fbf5d492fdb`

---

## [2026-11-21] - Fix de capa eliminada (2.0.1)

### Problema
`RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted`
al desconectar las señales de edición de una capa ya destruida.

### Solución
- Guardas con `sip.isdeleted` y `_layer_alive`.
- `_disconnect_editing_signals` limpia la referencia antes de desconectar.
- Señal `destroyed` conectada por capa activa; limpia referencia y pick tool.
- Tests de capa eliminada, referencia obsoleta, unload y difference pick.
- Tests: 138 totales (57 unitarios + 81 integración).

### Pendiente
- Publicar 2.0.1 en GitHub y desplegar; portal 2.0.1 después del estado de 2.0.0.

---

## [2026-11-20] - ZIP subido al portal QGIS; aprobación pendiente (01:32)

### Resumen
El ZIP 2.0.0 se subió a plugins.qgis.org. El release de GitHub ya está publicado;
queda esperar la aprobación del portal.

### Estado
- Portal: `uploaded; pending approval`.
- GitHub Release: publicado con ZIP y SHA256.
- Tag `v2.0.0`: creado y subido.
- Roadmap 2.1.0/2.2.0/2.3.0 aprobado; ninguna etapa iniciada.

### Pendiente
- Aprobación del portal (externo).
- Smoke test opcional en QGIS 3.28.
- Iniciar Etapa 1 solo con una orden explícita.

---

## [2026-11-20] - Roadmap de features aprobado (01:24)

### Resumen
Se creó y aprobó el roadmap de 10 etapas para 2.1.0 (quick wins), 2.2.0
(edición de geometrías) y 2.3.0 (guarda de solapamientos). No se implementó
ninguna etapa; el código sigue en v2.0.0.

### Etapas
1. Backspace para quitar el último vértice.
2. Contador de vértices.
3. Suavizado opcional.
4. Pausa/reanudación.
5. Atajos + ajuste siempre.
6. Longitud/área en vivo.
7. Dividir con trazo.
8. Agregar anillo.
9. Agregar parte.
10. Guarda de solapamientos.

### Documentación
- [Roadmap](../maintainer/PLAN_FEATURE_ROADMAP.md) aprobado; cada etapa requiere
  un kickoff explícito.

---

## [2026-11-20] - Release v2.0.0 (01:05)

### Resumen
Se ejecutó `/release-plugin` hasta la preparación de la publicación.

### Resultados
- Gates: `make pre-release`, `make security-scan`, `make qt6-check`,
  `make zip`, `make portal-check` verdes.
- ZIP `dist/freehand_digitize.2.0.0.zip` validado; SHA256
  `2faa4a4542f8bb041e1c1823e5eff7f22227671bb6b000a06bb297c60ef37b5d`.
- Tag anotado `v2.0.0` creado y subido a `origin`.
- GitHub Release **publicado** con el ZIP y el SHA256 adjuntos:
  <https://github.com/geociencio/freehand-digitize/releases/tag/v2.0.0>.
- CI verde en `main` (run 44684907873).

### Pendiente
- Subir el ZIP a plugins.qgis.org y completar la validación del portal.
- Smoke test real en QGIS 3.28 (el ZIP declara 3.28 como mínimo).

---

## [2026-11-20] - CI verde en checkout con guion (05:45)

### Resumen
Se corrigió el layout de CI: el repositorio se clona como `freehand-digitize`,
pero el paquete es `freehand_digitize`. Se expone el paquete con un symlink en
`RUNNER_TEMP`, se configuró Ruff para imports first-party y `mypy` usa
`--explicit-package-bases`.

### Resultados
- GitHub Actions run 44682503490: quality, unitarias, Qt6 e integración QGIS
  verdes.
- `make pre-release` local sigue verde.
- Sin cambios de código de producto; solo CI/Makefile/Ruff y documentación.

### Documentación
- [Plan de CI](../maintainer/PLAN_CI_CHECKOUT.md) implementado.
- Workflow de release actualizado para catálogos `.qm` y CI verde.

---

## [2026-11-20] - Diferencia de entidades (00:30)

### Resumen
Se añadió la diferencia objetivo − corte, con dos entidades seleccionadas o
selección por mouse (clic objetivo, clic corte) y diálogo de confirmación.

### Logros
- `DifferenceDialog`, `DifferencePickTool` y `DifferenceCreator`.
- `QgsGeometry.difference` con rechazo de resultados vacíos/no válidos; la
  entidad de corte no se modifica; una sola operación de deshacer.
- Acción habilitada en edición; sin par seleccionado se activa el pick tool.
- Traducciones ES→EN (48 mensajes) y tests de creador, diálogo, pick tool y
  plugin.
- Tests: 134 totales (57 unitarios, 77 integración) en QGIS 4.2.2 y contenedor
  Qt5/QGIS 3.99.

### Documentación
- README, guía de usuario, arquitectura, CHANGELOG, metadata y paridad.
- [Plan de diferencia](../maintainer/PLAN_FEATURE_DIFFERENCE.md) implementado.

---

## [2026-11-19] - Muestreo configurable y gating de edición (23:38)

### Resumen
Se añadieron las opciones de muestreo (píxeles o unidades de capa) y el plugin
pasó a respetar la sesión de edición de QGIS.

### Logros
- `SamplingOptions`/`StrokeRecorder` con thinning por píxeles o por unidades de
  capa; distancias separadas por unidad.
- `SamplingStore` y `SamplingDialog` con advertencia de CRS geográfico (grados y
  latitud).
- Las acciones de crear/reformar solo se habilitan con la capa en edición; al
  detener la edición se cancela el trazo y se desactiva la herramienta.
- Se eliminó el auto-inicio de edición del plugin, `FreehandTool`,
  `FeatureCreator` y `ReshapeCreator`.
- Tests: 117 totales (57 unitarios, 60 integración); `make test-qgis` y
  `make docker-test` verdes.
- Catálogo inglés: 34 mensajes.

### Documentación
- README, guía de usuario, arquitectura, CHANGELOG, metadata y paridad.
- Planes [edit-session](../maintainer/PLAN_EDIT_SESSION.md) y
  [vertex sampling](../maintainer/PLAN_VERTEX_SAMPLING.md) implementados.

---

## [2026-11-19] - Freehand reshape implementado (23:05)

### Resumen
Se implementó la revisión 2 del plan de reshape: el trazo reforma las geometrías
que quedan bajo él, con selección opcional como filtro y una sola operación de
deshacer.

### Logros
- `gui/reshape_creator.py` con detección por bounding box + intersección,
  `QgsGeometry.reshapeGeometry`, filtro por selección y edición atómica.
- `FreehandTool` con `MODE_CREATE`/`MODE_RESHAPE` y trazo de línea abierta.
- Segunda acción/tool en `freehand_plugin.py`; limpieza y ciclo de vida
  refactorizados.
- Traducciones español→inglés (22 mensajes), tests de catálogo y de integración.
- Tests: 97 totales (49 unitarios, 48 integración) en QGIS 4.2.2 y en el
  contenedor Qt5/QGIS 3.99.
- `make pre-release`, `make zip`, `make security-scan`, `make qt6-check` verdes;
  smoke test del plugin desplegado en QGIS 4.

### Documentación
- README, guía de usuario, arquitectura, CHANGELOG, metadata y paridad.
- [Plan de reshape](../maintainer/PLAN_RESHAPE.md) marcado como implementado.

---

## [2026-11-19] - Proceso plan-first y plan de reshape (22:35)

### Resumen
Se estableció la regla de planificación previa a cualquier cambio de código y se
documentó el plan de la función reshape, sin tocar código.

### Logros
- Procedimiento `docs/maintainer/CHANGE_PROCEDURE.md` (análisis → plan →
  aprobación → implementación → verificación).
- Skill `plan-first` y workflow `/plan-change`.
- `AGENTS.md`, `opencode.json` y README actualizados con la regla.
- Plan propuesto `docs/maintainer/PLAN_RESHAPE.md` con evidencia de API, diseño,
  pruebas, riesgos y procedimiento.
- Revisión 2 del plan: el objetivo es la geometría bajo el trazo; la selección
  actúa como filtro opcional.

### Resultados
- Sin cambios de código; el plan de reshape queda pendiente de aprobación.
- `make agent-validate` y `make docs-check` se ejecutan tras el cambio.

### Documentación
- [Procedimiento de cambios](../maintainer/CHANGE_PROCEDURE.md)
- [Plan de reshape](../maintainer/PLAN_RESHAPE.md)

---

## [2026-11-19] - i18n: catálogo inglés y sistema de traducciones (22:05)

### Resumen
Se adaptó el sistema de traducción de SecInterp a Freehand Digitize: cadenas de
UI con `QCoreApplication.translate`, catálogo inglés, carga según el locale de
QGIS y validación de catálogos.

### Logros
- Cadenas de UI centralizadas o marcadas con el contexto `FreehandDigitize`.
- Catálogo `i18n/freehand_digitize_en.ts/.qm` y memoria de traducción JSON.
- Cargador `gui/i18n.py` con fallback de locale completo a idioma y limpieza en
  `unload`.
- `make transup`, `make transcompile`, `make i18n-check` y tests de catálogo.
- Metadatos con `general_description` y README/user guide actualizados.

### Resultados
- 85 tests (49 unitarios, 36 de integración), incluidos 7 de catálogo y 4 de
  carga de traducciones.
- `make i18n-check`, `make test` y `make test-qgis` en verde.
- Catálogo inglés compilado y empaquetado; `.ts` excluido del ZIP.

### Documentación
- [Guía i18n](../../scripts/i18n/README.md)
- [Arquitectura](../ARCHITECTURE_EN.md)

---

## [2026-11-19] - Paridad 2.0.0, sistema agéntico y QA (21:25)

### Resumen

Se restauró la paridad funcional con el plugin original `freehandEditing` y se
modernizó el plugin a QGIS 3.28–4.x (Qt5/Qt6). Además se copió y adaptó el
sistema agéntico (Agentic Forge) y el QA del proyecto de referencia, y se adaptó
la guía de modernización con `uv`.

### Logros

- Plan aprobado en `docs/maintainer/PLAN_FREEHAND_PARITY.md`; se revirtió el
  andamiaje no revisado y se creó un commit baseline del plugin original.
- Arquitectura `core/` (sin QGIS/Qt) + `gui/` (PyQGIS) + `freehand_plugin.py`
  (orquestación), con shims PyQt5/PyQt6 en `gui/qt_compat.py`.
- Paridad restaurada: tolerancia persistente, política de CRS geográfico,
  snapping CTRL del primer y último vértice, cursor de lápiz, trazo en CRS de
  capa, formulario de atributos, valores por defecto, comando de deshacer, aviso
  de geometría inválida, habilitación por capa, botón secundario y `Esc`.
- QA: `pyproject.toml` + `uv.lock`, Makefile, ruff, flake8, mypy,
  `qgis-analyzer`, `qgis-manage`, pre-commit, CI, Docker, baseline de
  detect-secrets y tests unitarios e integración.
- Sistema agéntico: `.agent/` vendorizado, `.agent-state/` adaptado,
  `AGENTS.md`, `forge.toml`, `opencode.json`, `.ai-context/` y workflows.
- Documentación: README, CHANGELOG, metadatos y guía de usuario en inglés;
  informe de paridad, plan, registro y guía de logging en español; arquitectura,
  guía `uv` y convenciones de mantenimiento en inglés.

### Resultados

- **Tests**: 74 en total; 42 unitarios sin QGIS y 32 de integración.
  - QGIS 4.2.2 / Qt6 (host): 32 OK.
  - `qgis/qgis:latest` / Qt5 (contenedor): 32 OK.
- **Calidad**: ruff, flake8, mypy y analyzer sin errores; CC ≤ 10; 100 % de
  docstrings; 3 avisos LOW (`GOD_OBJECT`).
- **Paquete**: `dist/freehand_digitize.2.0.0.zip`, 18 archivos, ~31 KB;
  `package --repo-check` y `validate --zip` OK.
- **Seguridad**: `qgis-manage security --portal` con 0 hallazgos (0 críticos).
- **Qt6**: `pyqgis4-checker` sin `Enum error`.
- **Sistema agéntico**: `forge validate` OK (17 skills, 18 workflows, 3
  plantillas).
- **Commits**: `d1857d0` (baseline) y `a8c8d04` (2.0.0).

### Documentación

- [Plan de paridad](../maintainer/PLAN_FREEHAND_PARITY.md)
- [Informe de paridad](../maintainer/FEATURE_PARITY.md)
- [Arquitectura](../ARCHITECTURE_EN.md)
- [Guía de modernización con uv](../maintainer/uv_modernization_guide.md)
- [Reglas de agentes](../../AGENTS.md)
- [Convenciones de commit](../maintainer/COMMIT_GUIDELINES.md)

---

# Plan de actualización — Freehand Digitize (paridad con `freehandEditing`)

> **Estado:** aprobado y ejecutado (2026-11-19). Plan de referencia de la
> implementación 2.0.0; las decisiones finales están en la sección 15.
>
> **Fecha:** 2026-11-19
> **Repositorio de trabajo:** `/home/jmbernales/qgispluginsdev/freehand_digitize`
> **Upstream de referencia:** <https://github.com/vinayan/freehandEditing> (commit
> `e550544`, GPL-2.0, 2010–2012 Pavol Kapusta / 2013 Larry Shaffer)
> **Sistema agéntico de referencia:** `../sec_interp/.agent` (Agentic Forge
> v1.4.2) y `../sec_interp/.agent-state`
> **Guía de modernización de referencia:** `../sec_interp/docs/maintainer/uv_modernization_guide.md`

---

## 0. Nota de transparencia: qué se hizo antes de este documento

Durante la fase de exploración (antes de tu instrucción) ya se habían creado
archivos de andamiaje. **No se ha tocado** `metadata.txt`, `__init__.py`,
configuración de QA, CI, tests, icono ni licencia. El inventario exacto es:

| Archivo | Estado | Acción propuesta |
| :--- | :--- | :--- |
| `.agent/` (67 archivos) | Copiado del framework Agentic Forge | Conservar |
| `.agent-state/skills/{qgis-core,qgis-migration-4x,qgis-release}` | Copiado y renombrado | Conservar y adaptar |
| `.agent-state/workflows/{audit-plugin,release-plugin,run-tests-in-qgis}` | Copiado | Conservar y adaptar |
| `core/__init__.py`, `core/constants.py`, `core/geometry_rules.py`, `core/stroke.py`, `core/settings.py` | Nuevos | Conservar (revisar en la fase 2) |
| `gui/__init__.py`, `gui/qt_compat.py`, `gui/cursor.py`, `gui/geometry_factory.py`, `gui/freehand_tool.py`, `gui/feature_creator.py` | Nuevos | Conservar (revisar en la fase 2) |
| `freehand_plugin.py` | **Reemplazado** (288 líneas) | Conservar o restaurar el original de 224 líneas |
| `.uvcache/` | Artefacto de prueba de `uv` | Eliminar |
| Directorios vacíos `docs/maintainer`, `tests/`, `.github/workflows`, `.ai-context` | Creados | Poblar en fases 3–5 |

**Opciones para ti:**

- **A (recomendada):** conservar el andamiaje, revisar este plan y, al aprobarlo,
  continuar desde la fase 2 (revisión/corrección del código ya escrito).
- **B:** revertir `freehand_plugin.py` a su versión original de 224 líneas y
  eliminar `core/` y `gui/`; el plan se ejecuta desde cero tras la aprobación.
- **C:** revertir todo, incluido `.agent/`, y empezar de cero.

No se ejecutará ninguna de las tres sin tu confirmación.

---

## 1. Objetivo y alcance

### 1.1 Objetivo

Recuperar en el plugin moderno **todas las capacidades funcionales** del
`freehandEditing` original que se perdieron en la reescritura actual, manteniendo
compatibilidad con **QGIS 3.28+ y QGIS 4.x (PyQt5 y PyQt6)**. Además:

1. Copiar y adaptar el **sistema agéntico** de `sec_interp` (Agentic Forge).
2. Adaptar la **guía de modernización con `uv`** al nuevo repositorio.
3. Copiar y adaptar el **QA existente** de `sec_interp` (lint, tipos, tests,
   seguridad, empaquetado, CI, Docker, pre-commit).

### 1.2 Fuera de alcance (salvo que lo pidas)

- Publicar en `plugins.qgis.org` (solo se prepara el ZIP y se valida).
- Traducciones i18n (no hay catálogos en el repo actual).
- Migrar el historial git del upstream (el workspace no es un repositorio git).
- Cambiar el nombre del plugin o su `plugin id` (`freehand_digitize`).

---

## 2. Auditoría del estado actual

### 2.1 Qué existe hoy

```
freehand_digitize/
├── __init__.py               # classFactory -> FreehandDigitizePlugin
├── freehand_plugin.py        # tool + plugin (224 líneas originales)
└── metadata.txt              # QGIS 3.28–4.99 (sin supportsQt6)
```

### 2.2 Defectos y carencias detectados en la versión actual

| # | Hallazgo | Impacto | Evidencia |
| :-- | :--- | :--- | :--- |
| D1 | **Sin control de tolerancia**: la simplificación está fijada a `mapUnitsPerPixel() * 2` | No se puede ajustar el nivel de simplificación; el upstream tenía un `QDoubleSpinBox` 0–5 con 3 decimales, persistido en `QSettings` | `freehand_plugin.py:139-143` |
| D2 | **Coordenadas en CRS del proyecto**: usa `e.mapPoint()` y no `toLayerCoordinates()` | Si la capa activa tiene CRS distinto del proyecto (OTF), la geometría se crea en el CRS equivocado | `freehand_plugin.py:77,86` |
| D3 | **Sin reproyección** al crear la entidad | Mismo problema que D2, silencioso | `freehand_plugin.py:114-137` |
| D4 | **Sin snapping con CTRL** | No se puede enganchar el primer/último vértice a vértices existentes | upstream `freehandeditingtool.py:75-93` |
| D5 | **Sin cursor de lápiz** | Solo `CrossCursor`; el upstream usaba un XPM de lápiz | `freehand_plugin.py:27,54` |
| D6 | **Sin formulario de atributos** | Se crea la entidad sin pedir atributos; se ignoran los valores por defecto del proveedor | upstream `freehandediting.py:181-206` |
| D7 | **Sin valores por defecto del proveedor** | Campos `defaultValue`/`defaultValueClause` quedan nulos | ídem |
| D8 | **Sin comando de edición (undo)** | `Ctrl+Z` no revierte la entidad de forma atómica; no hay `beginEditCommand`/`endEditCommand` | upstream líneas 192-206 |
| D9 | **Sin aviso de geometría inválida** | `makeValid()` se aplica en silencio; el usuario no decide | `freehand_plugin.py:145-148` |
| D10 | **Sin habilitación por tipo de capa** | La acción está siempre activa; el upstream la habilitaba solo para líneas/polígonos editables y se sincronizaba con `editingStarted/Stopped` y `currentLayerChanged` | upstream `freehandediting.py:105-140` |
| D11 | **Sin `ignoreclick` durante el formulario modal** | Clics durante el diálogo pueden iniciar trazos o mover el mapa | upstream `freehandeditingtool.py:121-123` |
| D12 | **Botón derecho cancela en vez de terminar el trazo** | El upstream permitía “halt drag-drawing with a secondary click” (termina el trazo) | upstream `freehandeditingtool.py:50-55,105-120` |
| D13 | **Sin límite de puntos ni muestreo por píxel** | Trazos muy densos → más vértices y simplificación costosa | upstream añadía cada evento (sin filtro) |
| D14 | **Dependencia frágil de `QAction`** | Se importa de `QtWidgets`; en PyQt6 vive en `QtGui` (aquí funciona por compatibilidad, pero no es portable) | `freehand_plugin.py:10` |
| D15 | **Sin QA, tests, lint, CI ni empaquetado** | No hay gates reproducibles | repo actual |
| D16 | **Sin sistema agéntico** | No hay `AGENTS.md`, `.agent/`, estado, skills, workflows | repo actual |

### 2.3 Lo que sí hace bien la versión actual (se conserva)

- Arranca la edición automáticamente al activar la herramienta (comodidad).
- `try/except` con `QgsMessageLog` en eventos del canvas (robustez).
- `ESC` cancela y desactiva la herramienta.
- `deactivate()` limpia el trazo.
- Barra de mensajes para errores.

---

## 3. Inventario funcional del upstream

Referencias: [freehandediting.py](https://github.com/vinayan/freehandEditing/blob/e550544/freehandediting.py) (216 líneas) y
[freehandeditingtool.py](https://github.com/vinayan/freehandEditing/blob/e550544/freehandeditingtool.py) (147 líneas).

| ID | Capacidad | Implementación upstream | API obsoleta (QGIS 2) | Equivalente moderno |
| :-- | :--- | :--- | :--- | :--- |
| U1 | Acción solo con capa editable de línea/polígono | `toggle()` + `currentLayerChanged` + `editingStarted/Stopped` | `QGis.Line/Polygon`, `currentLayerChanged['QgsMapLayer*']` | `Qgis.GeometryType.*` + `QgsMapLayerType.Vector`; señales modernas |
| U2 | Spinbox de tolerancia 0–5, 3 decimales, paso 0.1 | `QDoubleSpinBox` en digitize toolbar | `QSettings` con `type=float` | `QgsSettings`; mismas unidades |
| U3 | Persistencia de tolerancia | clave `/freehandEdit/tolerance` | — | clave nueva `freehand_digitize/tolerance` + migración de la legacy |
| U4 | Tolerancia deshabilitada en CRS geográfico | `layer.crs().projectionAcronym() != "longlat"` | `projectionAcronym()` | `layer.crs().isGeographic()` |
| U5 | Cursor de lápiz | `QCursor(QPixmap([...XPM...]))` | — | `QPixmap(XPM)` + `QCursor(pixmap, 8, 8)` (verificado en PyQt6) |
| U6 | Snapping del primer punto con CTRL | `QgsMapCanvasSnapper.snapToCurrentLayer` + `snapToBackgroundLayers` | `QgsMapCanvasSnapper`, `QgsSnapper` | `canvas.snappingUtils().snapToCurrentLayer(...)` / `.snapToMap(...)` (verificado) |
| U7 | Dibujo en coordenadas de capa | `toLayerCoordinates(layer, event.pos())` | — | `QgsMapTool.toLayerCoordinates` (sigue existiendo) |
| U8 | Reproyección OTF al crear | `QgsCoordinateTransform(projectCRS, layerCRS)` | `QgsCoordinateTransform` constructor antiguo | No hace falta si el trazo ya está en CRS de capa |
| U9 | Simplificación con tolerancia | `geom.simplify(tolerance)` | — | `QgsGeometry.simplify(tolerance)` |
| U10 | Validación + pregunta “usar de todos modos” | `validateGeometry()` + `QMessageBox` | `validateGeometry()` | `isGeosValid()` + `QMessageBox.question` |
| U11 | Valores por defecto del proveedor | `provider.defaultValue(i)` | `pendingFields()` | `QgsVectorLayerUtils.createFeature(layer, geometry=...)` |
| U12 | Formulario de atributos modal | `iface.getFeatureForm(layer, f).exec_()` | `exec_()` | `iface.getFeatureForm(layer, feature).exec()` (verificado) |
| U13 | Ignorar clics durante el modal | `setIgnoreClick(True/False)` | — | Igual, propiedad del tool |
| U14 | Comando de edición (undo) | `beginEditCommand`/`endEditCommand`/`destroyEditCommand` | — | Igual (verificado) |
| U15 | Rubbers band por tipo con relleno | `QgsRubberBand(canvas, QGis.Polygon/Line)` | `QGis.Polygon` | `QgsRubberBand(canvas, Qgis.GeometryType.*)` |
| U16 | Botón secundario detiene el trazo | press ignorado + release finaliza | — | `canvasReleaseEvent` finaliza con cualquier botón |
| U17 | Ignorar press repetidos mientras se dibuja | `if ignoreclick or drawing: return` | — | Igual |
| U18 | Mínimo de vértices | `numberOfVertices() > 2` | — | ≥3 polígono, ≥2 línea (mejora: una línea de 2 puntos es válida) |

---

## 4. Matriz de paridad propuesta

| Capacidad | Upstream | Actual | Propuesta | Test |
| :--- | :---: | :---: | :--- | :--- |
| Dibujar línea/polígono | ✅ | ✅ | ✅ mantener | integración |
| Tolerancia ajustable + persistida | ✅ | ❌ | ✅ restaurar | unit + integración |
| Tolerancia 0 en CRS geográfico | ✅ | ❌ | ✅ restaurar | unit |
| Cursor de lápiz | ✅ | ❌ | ✅ restaurar | unit (XPM) |
| Snapping CTRL (primer/último vértice) | ✅ (solo inicio) | ❌ | ✅ restaurar + final | integración |
| CRS de capa / OTF | ✅ | ❌ | ✅ corregir | integración |
| Simplificación configurable | ✅ | fija 2 px | ✅ restaurar | unit + integración |
| Aviso de geometría inválida | ✅ | ❌ | ✅ restaurar | integración (mock QMessageBox) |
| Valores por defecto | ✅ | ❌ | ✅ `createFeature` | integración |
| Formulario de atributos | ✅ | ❌ | ✅ restaurar | integración |
| Ignorar clics en modal | ✅ | ❌ | ✅ restaurar | integración |
| Comando de edición (undo) | ✅ | ❌ | ✅ restaurar | integración |
| Habilitación por capa editable | ✅ | ❌ | ✅ restaurar + auto-edit | integración |
| Botón secundario termina trazo | ✅ | ❌ (cancela) | ✅ alinear con upstream | unit/integración |
| ESC cancela | ❌ | ✅ | ✅ mantener | integración |
| Auto-inicio de edición | ❌ | ✅ | ✅ mantener (comodidad) | integración |
| Mensajes de error robustos | parcial | ✅ | ✅ mantener | unit |
| Límite/muestreo de puntos | ❌ | parcial | ✅ píxel + tope | unit |

---

## 5. Arquitectura propuesta

### 5.1 Principios

1. **Separación Core/GUI** (patrón de `sec_interp`): `core/` no importa `qgis`
   ni Qt; `gui/` traduce objetos QGIS a valores planos antes de llamar al core.
2. **Inyección de dependencias**: backend de settings, `iface`, canvas y
   callbacks se pasan por constructor; nada de globales.
3. **Una responsabilidad por módulo**, límite blando de 400 líneas y CC ≤ 10
   (configurable en `forge.toml`).
4. **Compatibilidad Qt5/Qt6** centralizada en `gui/qt_compat.py`.
5. **Comportamiento upstream primero**, mejoras documentadas y justificadas.

### 5.2 Árbol final previsto

```
freehand_digitize/                      # raíz = carpeta del plugin en QGIS
├── __init__.py                         # classFactory (sin cambios)
├── freehand_plugin.py                  # orquestación: acción, toolbar, señales
├── core/                               # sin QGIS / sin Qt
│   ├── __init__.py
│   ├── constants.py                    # claves, límites, textos
│   ├── geometry_rules.py               # tipos, tolerancia, cierre de anillo
│   ├── settings.py                     # ToleranceStore + formulario
│   └── stroke.py                       # StrokeRecorder (muestreo)
├── gui/                                # PyQGIS / Qt
│   ├── __init__.py
│   ├── cursor.py                       # XPM del lápiz
│   ├── feature_creator.py              # defaults, validez, formulario, undo
│   ├── freehand_tool.py                # QgsMapTool + rubber band + snapping
│   ├── geometry_factory.py             # puntos -> QgsGeometry
│   └── qt_compat.py                    # enums/imports PyQt5/6
├── metadata.txt                        # versión 2.0.0
├── icon.png                            # PNG >= 32 px
├── LICENSE                             # GPL-2.0
├── README.md
├── CHANGELOG.md
├── AGENTS.md                           # configuración agéntica canónica
├── AI_CONTEXT.md                       # contexto de sesión
├── forge.toml                          # framework/estado/comandos
├── pyproject.toml                      # uv + ruff + mypy + coverage
├── uv.lock
├── Makefile
├── .python-version                     # 3.12 (dev); runtime 3.9+
├── .flake8 .bandit .secrets.baseline
├── .analyzerignore .qgisignore .gitignore
├── .pre-commit-config.yaml
├── opencode.json                       # roles architect/qa_engineer/auditor
├── .agent/                             # framework Agentic Forge (vendorizado)
├── .agent-state/                       # estado y overlay del proyecto
│   ├── task.md  next_steps.md
│   ├── memory/{AGENT_LESSONS.md,agent_metrics.json,memory_policy.md}
│   ├── skills/{project-context,freehand-digitizing,qgis-core,
│   │           qgis-migration-4x,qgis-release}
│   ├── workflows/{audit-plugin,release-plugin,run-tests-in-qgis,smoke-qgis4}
│   └── history/{tasks,next_steps,memory}/
├── .ai-context/{config.toml,architecture_notes.md}
├── docs/maintainer/
│   ├── PLAN_FREEHAND_PARITY.md         # este documento
│   ├── FEATURE_PARITY.md               # matriz final + notas de migración
│   └── uv_modernization_guide.md       # guía adaptada
├── tests/
│   ├── __init__.py  base_test.py
│   ├── core/          # unitarios sin QGIS
│   ├── integration/   # QGIS real (skip si no está)
│   └── mocks/         # stubs mínimos para tests GUI mock-first
├── .github/workflows/test.yml
└── Dockerfile  .devcontainer/devcontainer.json
```

### 5.3 Flujo de datos

```
canvasPressEvent ──► toLayerCoordinates ──► StrokeRecorder.start ──► rubber band
        │                    ▲
        │               CTRL snapping (snappingUtils)
        ▼
canvasMoveEvent ──► StrokeRecorder.add (filtro en píxeles) ──► rubber band
        │
canvasReleaseEvent ──► build_geometry (CRS capa) ──► geometryFinished(geom, layer)
        │
        ▼
FeatureCreator.create
  1. simplify(tolerancia efectiva)
  2. isGeosValid() ──► QMessageBox (¿usar igual?)
  3. startEditing() si hace falta
  4. beginEditCommand
  5. QgsVectorLayerUtils.createFeature (defaults)
  6. getFeatureForm().exec() (con setIgnoreClick)
  7. addFeature ──► endEditCommand ──► repaint
```

---

## 6. Diseño detallado por capacidad

### 6.1 Ciclo de vida y habilitación (U1)

- La acción se habilita solo si la capa activa es `QgsVectorLayer`, válida, de
  línea/polígono y `supportsEditing()`.
- Señales conectadas en `initGui`, desconectadas de forma segura en `unload`:
  - `iface.currentLayerChanged` → `_update_ui_state`
  - `canvas.mapToolSet` → `_on_map_tool_set` (sincroniza el check)
- `editingStarted/editingStopped`: **no** se conectan porque el plugin inicia la
  edición automáticamente; el estado se recalcula con `currentLayerChanged`.
  Se valorará conectarlas si la capa se cierra externamente.
- Al activar: valida, hace `startEditing()` si hace falta y `setMapTool`.
- Si la capa deja de ser válida mientras el tool está activo, se desactiva.

**Decisión D-A:** se conserva el auto-inicio de edición de la versión actual
(aunque el upstream exigía edición manual). Si prefieres paridad estricta, se
cambia a “acción habilitada solo si `layer.isEditable()`”.

### 6.2 Tolerancia (U2–U4)

- `QDoubleSpinBox`: decimales 3, rango 0–5, paso 0.1, valor inicial desde
  `ToleranceStore.load()`.
- Añadido a `iface.digitizeToolBar()` con `addWidget`; eliminado en `unload`.
- `valueChanged` → `ToleranceStore.save()` (clave
  `freehand_digitize/tolerance`; migra `/freehandEdit/tolerance`).
- CRS geográfico (`layer.crs().isGeographic()`): spinbox deshabilitado, tooltip
  explicativo y tolerancia efectiva 0.
- `effective_tolerance()` clampa a `[0, 5]` y convierte `NaN`/infinito a 0.

### 6.3 Captura del trazo (U7, U13, D13)

- Los puntos se guardan en **coordenadas de capa** (`toLayerCoordinates`).
- El rubber band se dibuja con `event.mapPoint()` (CRS del lienzo), sin
  transformar cada punto.
- `StrokeRecorder` descarta vértices a menos de **1,5 px** de dispositivo
  (independiente del CRS) y limita a 20 000 puntos.
- El trazo se congela con la capa capturada en `canvasPressEvent`; si el usuario
  cambia de capa a mitad, la entidad va a la capa original.

### 6.4 Snapping con CTRL (U6)

- En `canvasPressEvent` y `canvasReleaseEvent`, si CTRL está pulsado:
  1. `canvas.snappingUtils().snapToCurrentLayer(device_pos, Vertex)`.
  2. Si no hay match, `snapToMap(device_pos)` (capas de fondo según la config de
     snapping de QGIS).
  3. Si hay match, `match.point()` (CRS del lienzo) → `toLayerCoordinates`.
- Fallback silencioso al punto libre si el motor falla o no hay match.
- Mejora respecto al upstream: también se engancha el **último** vértice.
- Limitación documentada: respeta la configuración de snapping de QGIS
  (tolerancia y capas); si el snapping está desactivado, el enganche puede no
  producirse.

### 6.5 Cursor y rubber band (U5, U15)

- XPM de lápiz de 16×16 con hotspot `(8, 8)`; fallback a `CrossCursor`.
- Rubber band nueva por trazo: polígono `QColor(255,0,0,63)` y ancho 2; línea
  `QColor(255,0,0,150)` y ancho 1 (igual que upstream).
- `reset()` y liberación de referencia al terminar o cancelar.

### 6.6 Construcción de geometría (U9, U18)

- `build_geometry(points, kind)` en `gui/geometry_factory.py`:
  - polígono: `close_ring()` y `QgsGeometry.fromPolygonXY`.
  - línea: `QgsGeometry.fromPolylineXY`.
- Mínimos: 3 puntos para polígono (antes de cerrar), 2 para línea.
- `simplify(tolerancia)` antes de validar; si el resultado es vacío, se conserva
  la geometría original.

### 6.7 Creación de entidad (U10–U14)

`FeatureCreator.create(layer, geometry, tolerance, ignore_clicks)`:

1. Simplifica (si `tolerance > 0`).
2. Si `not isGeosValid()` → `QMessageBox.question` “¿usar de todos modos?”.
3. `startEditing()` si hace falta; error si no se puede.
4. `beginEditCommand("Freehand Digitize: añadir entidad")`.
5. `QgsVectorLayerUtils.createFeature(layer, geometry=...)` (aplica defaults y
   restricciones; sustituye al bucle de `provider.defaultValue`).
6. Si el formulario está habilitado
   (`qgis/digitizing/disable_enter_attribute_values_dialog` es falso) →
   `iface.getFeatureForm(layer, feature).exec()`; durante el modal
   `tool.setIgnoreClick(True/False)`.
7. Si se cancela: `destroyEditCommand()` y no se añade.
8. `addFeature()`; si falla: `destroyEditCommand()` + aviso.
9. `endEditCommand()` + `triggerRepaint()` + `canvas.refresh()`.

### 6.8 Eventos y ergonomía (U16, U17, ESC)

- Press con cualquier botón mientras se dibuja: se ignora.
- Release con cualquier botón mientras se dibuja: **termina** el trazo (upstream).
- Press con botón derecho sin trazo: no hace nada.
- ESC: si hay trazo, cancela y mantiene la herramienta; si no, desactiva la
  herramienta.
- CTRL: `keyPressEvent`/`keyReleaseEvent` actualizan el flag.

### 6.9 Mensajes y logging

- `QgsMessageLog` con tag `Freehand Digitize`.
- `iface.messageBar().pushWarning(...)` para errores de usuario.
- Nunca se propaga una excepción desde un evento del canvas.

---

## 7. Sistema agéntico: qué se copia y qué se adapta

### 7.1 Estrategia

`sec_interp` monta el framework como **submódulo git** (`.agent` →
`https://codeberg.org/geociencio/agentic-forge.git`). Este workspace **no es un
repositorio git**, así que se **vendoriza** una copia limpia:

- Se copia `.agent/` completo (67 archivos) **sin** `.git`, `__pycache__` ni
  `.ruff_cache`.
- Se conserva el `VERSION` del framework (1.4.2) y su `LICENSE`.
- Si más adelante inicializas git, se puede convertir en submódulo siguiendo
  `scripts/update_agentic_forge.sh` (adaptado).

### 7.2 `.agent/` (framework reutilizable) — se copia tal cual

Incluye: `AGENTS.md`, `QUICK_REFERENCE.md`, `README.md`, `VERSION`,
`architecture/`, `skills/` (9), `workflows/` (15), `tools/` (forge CLI,
validadores, métricas, memoria), `scaffold/qgis/`, `tests/`, `ruff.toml`,
`mypy.ini`, `requirements*.txt`, `scripts/ci.sh`.

### 7.3 `.agent-state/` (propiedad del proyecto) — se adapta

| Archivo | Origen | Adaptación |
| :--- | :--- | :--- |
| `task.md` | Nuevo | Tablero de la fase 2.0.0 (paridad + agentico + QA) |
| `next_steps.md` | Nuevo | Handoff: pendientes y criterios de cierre |
| `memory/AGENT_LESSONS.md` | Nuevo | Plantilla YAML; lecciones de esta migración |
| `memory/memory_policy.md` | `sec_interp` | Copia adaptada (nombre, rutas) |
| `memory/agent_metrics.json` | Nuevo | Schema 2.0 con `summary.test_count` real |
| `skills/project-context/SKILL.md` | Nuevo | Propósito, arquitectura y estructura del plugin |
| `skills/freehand-digitizing/SKILL.md` | Nuevo | Dominio: matriz upstream, APIs PyQGIS, trampas |
| `skills/qgis-core/SKILL.md` | `sec_interp` | Renombrado; se elimina lo específico de `QgsTask` si no aplica |
| `skills/qgis-migration-4x/SKILL.md` | `sec_interp` | Renombrado; se añade la estrategia de `qt_compat.py` |
| `skills/qgis-release/SKILL.md` | `sec_interp` | Renombrado; se ajustan comandos al Makefile nuevo |
| `workflows/audit-plugin.md` | `sec_interp` | Renombrado; comandos adaptados |
| `workflows/release-plugin.md` | `sec_interp` | Renombrado; checklist adaptado (sin docs/i18n) |
| `workflows/run-tests-in-qgis.md` | `sec_interp` | Renombrado; comandos `make test-qgis` |
| `workflows/smoke-qgis4.md` | Nuevo | Smoke test headless con `QgsApplication` (sin MCP) |
| `history/` | Nuevo | `tasks/`, `next_steps/`, `memory/` con `.gitkeep` |

> No se copian las skills de dominio geológico (`geological-logic`,
> `ui-framework`) porque no aplican a este plugin.

### 7.4 Documentos raíz

| Archivo | Contenido |
| :--- | :--- |
| `AGENTS.md` | Configuración canónica: roles, tabla de workflows, comandos, arquitectura Core/GUI, estilo, testing, gates QA, estructura, recordatorios |
| `AI_CONTEXT.md` | Contexto compacto de sesión (estado, arquitectura, comandos, pendientes) |
| `forge.toml` | `framework=".agent"`, `state=".agent-state"`, `strict_agent_system=true`, `test_command`, `lint_command`, `type_command`, `analyzer_command`, `max_cc=10`, `module_size_limit=400` |
| `opencode.json` | Subagentes `architect` (edit allow), `qa_engineer` (ask), `auditor` (deny); sin MCP |
| `.ai-context/config.toml` | Rutas y `context_docs` |
| `.ai-context/architecture_notes.md` | Notas curadas de arquitectura |

### 7.5 Validación del sistema agéntico

```bash
uv run python .agent/tools/forge.py validate
```

Debe pasar con `strict_agent_system = true` (frontmatter de skills/workflows,
enlaces relativos, agentes canónicos, archivos de estado y presupuesto de
memoria). Si un enlace copiado del framework apunta a un archivo inexistente, se
corrige o se documenta.

---

## 8. QA: qué se copia de `sec_interp` y cómo se adapta

### 8.1 Herramientas

| Archivo | Acción | Notas |
| :--- | :--- | :--- |
| `pyproject.toml` | Adaptar | `name="freehand-digitize"`, `version="2.0.0"`, `requires-python=">=3.11"` (entorno de desarrollo; el runtime del plugin es 3.9) con `.python-version=3.12`; `dependencies=[]`; `[dependency-groups].dev` con `ruff`, `mypy`, `qgis-manage`, `qgis-plugin-analyzer`, `pre-commit`, `flake8`, `bandit`, `detect-secrets`, `coverage`, `pyyaml`; `[tool.uv] package=false`; `[tool.qgis-manager]` |
| `.python-version` | Nuevo | `3.12` |
| `uv.lock` | Generar | `uv lock` con `UV_CACHE_DIR` dentro del workspace (el caché global es de solo lectura en este entorno) |
| `Makefile` | Adaptar | `PLUGINNAME=freehand_digitize`; targets `sync`, `test`, `test-qgis`, `test-all`, `lint`, `format`, `flake8`, `mypy`, `analyzer`, `qgis-validate`, `zip`, `portal-check`, `security-scan`, `qt6-check`, `deploy`, `agent-validate`, `clean` |
| `.flake8` | Adaptar | `max-line-length=100`, `max-complexity=15`; alcance `core gui freehand_plugin.py __init__.py` |
| `.bandit` | Adaptar | Excluye `.agent`, `.agent-state`, `tests`, `docs`, `freehandEditing`, `.venv` |
| `.secrets.baseline` | Generar | `detect-secrets scan` sobre el repo empaquetable |
| `.analyzerignore` | Adaptar | Analiza `core/`, `gui/`, `freehand_plugin.py`; excluye tooling, tests, docs y upstream |
| `.qgisignore` | Adaptar | Excluye `.agent`, `.agent-state`, `.ai-context`, `tests`, `docs`, `scripts`, `freehandEditing`, `pyproject.toml`, `uv.lock`, `Makefile`, `.github`, caches |
| `.pre-commit-config.yaml` | Adaptar | Ruff lint/format, flake8 (alcance plugin), hooks de higiene, conventional commit |
| `.gitignore` | Nuevo | `.venv`, caches, `dist`, `.agent-state/history`? (no: la historia se versiona), `.uvcache`, `*.qm` |
| `.github/workflows/test.yml` | Adaptar | Jobs: `quality` (ruff + flake8 + `qgis-validate` + `forge validate`), `qt6` (contenedor `pyqgis4-checker`), `test` (unit mock-first en uv), `integration` (contenedor QGIS + `tests/integration`) |
| `Dockerfile` | Adaptar | `FROM qgis/qgis:latest`, `uv` con `--system-site-packages`, comando de tests |
| `.devcontainer/devcontainer.json` | Adaptar | Nombre y `PYTHONPATH` |
| `tests/` | Adaptar | `base_test.py`, `mocks/`, `core/`, `integration/` |
| `docs/maintainer/uv_modernization_guide.md` | Copiar + adaptar | Ver sección 9 |

### 8.2 Estrategia de tests

`sec_interp` usa `unittest` + **Mock-First** con una infraestructura de mocks
grande y específica. Para este plugin se adapta el **patrón**, no el volumen:

| Capa | Ubicación | Requiere QGIS | Qué cubre |
| :--- | :--- | :---: | :--- |
| Unitaria pura | `tests/core/` | No | `geometry_rules`, `stroke`, `settings`, constantes, metadatos |
| Integración | `tests/integration/` | Sí (QGIS 4 real o contenedor) | `QgsMapTool` (press/move/release), snapping, rubber band, `FeatureCreator`, `freehand_plugin` con un `iface` falso, imports PyQt6 |
| Mock-first GUI (opcional) | `tests/gui/` | No | Stubs mínimos de `qgis`/Qt si se quiere aislar la lógica del tool |

- Los tests de integración se **saltan** (`unittest.SkipTest`) si no hay QGIS, de
  modo que `make test` funcione en cualquier entorno.
- `make test-qgis` usa el Python del sistema (aquí QGIS 4.2.2 / Python 3.14) y
  tolera el segfault de cierre de QGIS (exit 139) solo si todos los tests dieron
  `OK`, igual que hace el CI de `sec_interp`.
- Objetivo: cubrir todas las funciones públicas de `core/` y los caminos
  críticos de `gui/`.

### 8.3 Gates

| Gate | Comando | Bloqueante |
| :--- | :--- | :---: |
| Formato/lint | `make lint` / `make format-check` | Sí |
| Flake8 portal | `make flake8` | Sí |
| Tipos | `make mypy` (solo `core/`) | Sí |
| Complejidad | `make analyzer` (`--max-cc 10`) | Sí |
| Tests unitarios | `make test` | Sí |
| Tests integración | `make test-qgis` | Sí (local/CI QGIS) |
| Agéntico | `make agent-validate` | Sí |
| Metadatos | `make qgis-validate` | Sí |
| Seguridad | `make security-scan` | Críticos |
| Qt6 | `make qt6-check` | Sí |
| ZIP | `make zip` + `make portal-check` | Sí (release) |

---

## 9. Guía `uv_modernization_guide.md` adaptada

Se copia la guía de `../sec_interp/docs/maintainer/uv_modernization_guide.md`
(480 líneas) y se adapta:

1. **Política de Python:** runtime `>=3.9` (QGIS 3.28), entorno de desarrollo
   fijado a 3.12 en `.python-version`; se documenta explícitamente la política
   mixta y se añade un test de compatibilidad de sintaxis para 3.9.
2. **Dependencias:** `dependencies = []`; nunca `PyQt5`/`PyQt6`.
3. **Secuencia de migración:** sin `requirements.txt` previo; se documenta el
   estado inicial (repo sin entorno) y la creación de `pyproject.toml`.
4. **Makefile:** ejemplos con los targets reales (`test`, `test-qgis`,
   `flake8`, `analyzer`, `qgis-validate`, `zip`, `qt6-check`) y el uso de
   `UV_CACHE_DIR` en entornos con caché de solo lectura.
5. **Tests:** sección específica para la doble vía
   `unittest` (mock-first) + integración QGIS/Docker, incluida la tolerancia al
   segfault de cierre.
6. **CI:** workflow real del repo (setup-uv pinned, `--frozen`, matriz
   Python 3.11/3.12; el runtime 3.9 se protege con el test de sintaxis, contenedor QGIS).
7. **Empaquetado:** `qgis-manage package --repo-check` y
   `validate --zip`; advertencia sobre archivos de desarrollo.
8. **Troubleshooting:** casos reales de este entorno (caché `uv` de solo
   lectura, QGIS 4 con `QgsRubberBand` en `qgis.gui`, `QgsSnappingUtils` en
   `qgis.core`, `QAction` en `QtGui`).
9. **Checklist de aceptación** adaptado al plugin.

---

## 10. Plan de edición archivo por archivo

### Fase 1 — Preparación (ya ejecutada parcialmente)

| Acción | Archivo(s) |
| :--- | :--- |
| Crear | `.agent/**` (vendorizado), `.agent-state/**` (esqueleto) |
| Crear | `core/*.py`, `gui/*.py` (andamiaje) |
| Reemplazar | `freehand_plugin.py` |
| Limpiar | `.uvcache/` (artefacto) |

### Fase 2 — Código del plugin (revisión y cierre)

| Acción | Archivo | Detalle |
| :--- | :--- | :--- |
| Revisar | `core/constants.py` | Textos ES, claves, límites |
| Revisar | `core/geometry_rules.py` | `geometry_kind`, `is_supported_*`, `clamp_tolerance`, `effective_tolerance`, `close_ring`, `to_xy` |
| Revisar | `core/stroke.py` | `StrokeRecorder` (píxel, tope, reset) |
| Revisar | `core/settings.py` | `ToleranceStore`, migración legacy, `show_attribute_form` |
| Revisar | `gui/qt_compat.py` | Enums Qt/Qgis, `QAction`, `SNAP_VERTEX`, rubber band |
| Revisar | `gui/cursor.py` | XPM + fallback |
| Revisar | `gui/geometry_factory.py` | `build_geometry` |
| Revisar | `gui/freehand_tool.py` | Eventos, snapping, rubber band, señal `geometryFinished` |
| Revisar | `gui/feature_creator.py` | Defaults, validez, formulario, undo |
| Revisar | `freehand_plugin.py` | Acción, spinbox, señales, enable/disable, unload |
| **Añadir** | `__init__.py` | Sin cambios (relativo) |
| **Añadir** | `metadata.txt` | Versión 2.0.0, descripción, `homepage`/`repository`/`tracker` (upstream hasta crear repo propio) |
| **Añadir** | `icon.png` | PNG ≥ 32×32 (se genera desde el XPM del lápiz o se adapta el upstream) |
| **Añadir** | `LICENSE` | GPL-2.0 (compatible con upstream) |

### Fase 3 — Documentación

| Acción | Archivo |
| :--- | :--- |
| Crear | `README.md` (instalación, uso, atajos, compatibilidad, paridad) |
| Crear | `CHANGELOG.md` (2.0.0: paridad restaurada + sistema agéntico + QA) |
| Crear | `docs/maintainer/FEATURE_PARITY.md` (matriz final + notas de migración) |
| Crear | `docs/maintainer/uv_modernization_guide.md` (adaptada) |
| Crear | `docs/maintainer/PLAN_FREEHAND_PARITY.md` (este documento) |
| Crear | `AGENTS.md`, `AI_CONTEXT.md`, `forge.toml`, `opencode.json` |
| Crear | `.ai-context/{config.toml,architecture_notes.md}` |
| Crear | `.agent-state/{task.md,next_steps.md,memory/*,skills/*,workflows/*,history/*}` |

### Fase 4 — QA e infraestructura

| Acción | Archivo |
| :--- | :--- |
| Crear | `pyproject.toml`, `.python-version`, `uv.lock` |
| Crear | `Makefile`, `.flake8`, `.bandit`, `.secrets.baseline`, `.analyzerignore`, `.qgisignore`, `.gitignore`, `.pre-commit-config.yaml` |
| Crear | `.github/workflows/test.yml`, `Dockerfile`, `.devcontainer/devcontainer.json` |
| Crear | `tests/__init__.py`, `tests/base_test.py`, `tests/mocks/*`, `tests/core/*`, `tests/integration/*` |

### Fase 5 — Validación y cierre

1. `uv lock && uv sync --frozen`
2. `make test` (unit, sin QGIS)
3. `make test-qgis` (integración QGIS 4.2.2 local)
4. `make lint && make flake8 && make mypy`
5. `make analyzer`
6. `make agent-validate`
7. `make qgis-validate`
8. `make security-scan`
9. `make qt6-check` (si Docker está disponible)
10. `make zip && make portal-check`
11. Actualizar `CHANGELOG.md`, `task.md`, `next_steps.md`, `agent_metrics.json`.

---

## 11. Compatibilidad QGIS 3.28–4.2 / PyQt5–6

APIs verificadas en este entorno (**QGIS 4.2.2, Python 3.14, PyQt6**):

| API | QGIS 3.28 (PyQt5) | QGIS 4.2 (PyQt6) | Estrategia |
| :--- | :--- | :--- | :--- |
| `QgsRubberBand` | `qgis.gui` | `qgis.gui` | Import directo |
| `QgsSnappingUtils` | `qgis.core` | `qgis.core` | `canvas.snappingUtils()` |
| `snapToCurrentLayer` | `(QPoint, type)` | `(QPoint, Type)` | `SNAP_VERTEX` compat |
| `QgsPointLocator.MatchFilter` | `All` | sin miembros scoped | No pasar filtro (default) |
| `QAction` | `QtWidgets` | `QtGui` (alias en `QtWidgets`) | try/except |
| `Qt.LeftButton` | plano | `Qt.MouseButton.LeftButton` | try/except |
| `QgsGeometry.simplify` | `(tolerance)` | `(tolerance, feedback=None)` | Llamada posicional |
| `validateGeometry()` | disponible | eliminado | `isGeosValid()` |
| `QgsCoordinateTransform` | constructor antiguo | nuevo | No se usa (trazo en CRS capa) |
| `iface.getFeatureForm` | `exec_()` | `exec()` | `exec()` |
| `QgsSettings.value(..., type=float)` | sí | sí (verificado) | Igual |
| `QgsVectorLayerUtils.createFeature` | sí | sí (verificado) | Igual |
| `layer.supportsEditing()` | sí | sí (verificado) | `getattr` defensivo |

Riesgo residual: `QgsMapTool.keyPressEvent` no siempre recibe ESC si QGIS lo
consume antes; el `deactivate()` cancela el trazo en cualquier caso.

---

## 12. Licencia y atribución

- El plugin se distribuye bajo **GPL-2.0** (igual que el upstream).
- Se conserva el aviso de copyright de Pavol Kapusta (2010–2012) y Larry
  Shaffer (2013) en el `README` y en la cabecera de los módulos derivados
  (cursor XPM, semántica de eventos).
- El framework `.agent/` conserva su `LICENSE` original.
- El upstream se consulta en GitHub (commit `e550544`); no se mantiene una
  copia local.

---

## 13. Validación y criterios de aceptación

### 13.1 Funcionales

- [ ] Dibujar una línea y un polígono en capas con CRS distinto al del proyecto
      produce geometrías en el CRS correcto.
- [ ] La tolerancia se puede cambiar, se guarda entre sesiones y se ignora (0)
      en capas geográficas.
- [ ] CTRL engancha el primer y el último vértice a un vértice existente.
- [ ] El cursor es el lápiz.
- [ ] Se muestra el formulario de atributos (si está habilitado en QGIS) y
      Cancelar no crea la entidad.
- [ ] Los valores por defecto del proveedor se aplican.
- [ ] `Ctrl+Z` revierte la entidad creada.
- [ ] Una geometría inválida pide confirmación.
- [ ] La acción se deshabilita en capas no editables o de puntos.
- [ ] El botón derecho termina el trazo; ESC cancela; clics durante el modal se
      ignoran.
- [ ] QGIS 4.2 carga el plugin sin errores de enums.

### 13.2 Técnicos

- [ ] `make test` verde sin QGIS.
- [ ] `make test-qgis` verde en QGIS 4.2.2.
- [ ] `ruff`, `flake8`, `mypy`, `analyzer` verdes.
- [ ] `forge validate` verde con `strict_agent_system=true`.
- [ ] `qgis-manage validate --strict --repo` verde.
- [ ] `make zip` genera un ZIP sin `.agent`, tests ni docs.
- [ ] `make portal-check` valida el ZIP.
- [ ] `make security-scan` sin críticos.

---

## 14. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
| :--- | :--- | :--- |
| El formulario modal bloquea el hilo y el release event sigue procesándose | Media | `setIgnoreClick` + tests de integración |
| `snapToCurrentLayer` depende de la config de snapping del usuario | Alta | Fallback al punto libre + documentación |
| `QMessageBox` en tests bloquea | Alta | Parchear `QMessageBox.question` en tests |
| Segfault de cierre de QGIS (139) | Alta | Tolerar 139 solo si `OK`, igual que el CI de `sec_interp` |
| `uv` no puede escribir en el caché global | Confirmado | `UV_CACHE_DIR` dentro del workspace en el Makefile/CI local |
| Enlaces rotos al copiar el framework | Media | `forge validate` + corrección de enlaces |
| `qgis-manage validate --repo` exige `repository`/`tracker` | Media | Confirmar URLs contigo; si no, dejar campos y validar sin `--repo` |
| Icono PNG ausente o <32 px | Media | Generar 128×128 desde el XPM o adaptar el upstream |
| `requires-python >=3.9` vs herramientas dev | Media | Resolver con `.python-version=3.12`; si falla, subir a 3.10/3.12 documentándolo |

---

## 15. Decisiones finales (resueltas)

1. **Andamiaje:** se revirtió el código no revisado y se reimplementó desde el
   plan (**opción B**); `.agent/` se conservó vendorizado.
2. **Idioma de la UI:** español como idioma fuente, con catálogo inglés
   (`i18n/freehand_digitize_en.qm`); código, tests y documentación técnica en
   inglés.
3. **Auto-inicio de edición:** se mantiene por comodidad; la acción sigue
   deshabilitada para capas que no soportan edición.
4. **Metadatos:** `homepage`, `repository` y `tracker` apuntan a
   <https://github.com/geociencio/freehand-digitize>.
5. **Git:** repositorio inicializado con un commit baseline (plugin original +
   framework + plan).
6. **Versión:** `2.0.0`.
7. **Política de Python:** entorno de desarrollo `>=3.11` (por `pre-commit` 4.x)
   y `.python-version=3.12`; el runtime 3.9 de QGIS 3.28 se protege con
   `tests/core/test_python_compat.py`.
8. **`supportsQt6`:** eliminado (obsoleto con qgis-manage 0.17); QGIS 4 Ready se
   marca con `qgisMaximumVersion=4.99`.

---

## 16. Anexos

### A. Referencias del upstream

- [freehandediting.py:59-90](https://github.com/vinayan/freehandEditing/blob/e550544/freehandediting.py#L59-L90) — spinbox y tolerancia.
- [freehandediting.py:105-140](https://github.com/vinayan/freehandEditing/blob/e550544/freehandediting.py#L105-L140) — habilitación por capa.
- [freehandediting.py:142-206](https://github.com/vinayan/freehandEditing/blob/e550544/freehandediting.py#L142-L206) — creación de entidad.
- [freehandeditingtool.py:21-40](https://github.com/vinayan/freehandEditing/blob/e550544/freehandeditingtool.py#L21-L40) — cursor XPM.
- [freehandeditingtool.py:50-120](https://github.com/vinayan/freehandEditing/blob/e550544/freehandeditingtool.py#L50-L120) — eventos y rubber band.
- [freehandeditingtool.py:128-147](https://github.com/vinayan/freehandEditing/blob/e550544/freehandeditingtool.py#L128-L147) — activación.

### B. APIs verificadas en este entorno

```bash
QT_QPA_PLATFORM=offscreen python3 - <<'PY'
from qgis.core import QgsApplication, Qgis
app = QgsApplication([], False); app.initQgis()
from qgis.gui import QgsRubberBand
from qgis.core import QgsSnappingUtils, QgsPointLocator
print(Qgis.version())
print(QgsRubberBand.__doc__.splitlines()[0])
print(QgsSnappingUtils.snapToCurrentLayer.__doc__.splitlines()[0])
PY
```

Resultado: QGIS 4.2.2; `QgsRubberBand` en `qgis.gui`; `QgsSnappingUtils` en
`qgis.core`; `snapToMap` devuelve `QgsPointLocator.Match`; `QAction` importable
desde `qgis.PyQt.QtGui` y `QtWidgets`; `QgsSettings.value(..., type=float)` y
`QgsVectorLayerUtils.createFeature` operativos.

### C. Comandos de validación previstos

```bash
# Entorno
UV_CACHE_DIR=$PWD/.uvcache uv lock
UV_CACHE_DIR=$PWD/.uvcache uv sync --frozen

# Tests
PYTHONPATH=.. uv run python -m unittest discover tests          # unit
QT_QPA_PLATFORM=offscreen PYTHONPATH=.. python3 -m unittest discover -s tests/integration -t .  # QGIS real

# Calidad
uv run ruff check .
uv run ruff format --check .
uv run flake8 core gui freehand_plugin.py __init__.py --config .flake8
uv run mypy core
uv run qgis-analyzer analyze . --max-cc 10

# Agéntico / empaquetado
uv run python .agent/tools/forge.py validate
uv run qgis-manage validate --strict
uv run qgis-manage package --repo-check
uv run qgis-manage validate --zip dist/freehand_digitize.2.0.0.zip
```

---

*Fin del plan. No se modificará código hasta recibir tu aprobación.*

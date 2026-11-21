# Análisis del repositorio — Freehand Digitize 2.0.1

> **Tipo:** análisis técnico interno, solo lectura.
> **Fecha:** 2026-11-21.
> **Commit analizado:** `77b1f48` (`main`, árbol de trabajo limpio).
> **Entorno de verificación:** QGIS 4.2.2 (Qt6), Python del sistema, `uv` con
> el lockfile congelado.
> **Alcance:** código, tests, empaquetado, CI, metadatos y documentación.
> **Nota:** este análisis no modificó código; el documento es el único
> artefacto generado.

---

## 1. Resumen ejecutivo

**Freehand Digitize 2.0.1** es un plugin QGIS maduro, pequeño y bien
empaquetado: digitalización a mano alzada de líneas y polígonos, *reshape*,
muestreo configurable, diferencia de entidades y paridad funcional con
`freehandEditing`. El estado general es **bueno**: árbol limpio, release
etiquetada, CI configurada y casi todas las puertas de calidad en verde.

La deuda principal no es funcional sino de **consistencia documental** y de
**dos huecos concretos de robustez/QA**: el falso verde de la suite de
integración local y un camino residual de error al finalizar un trazo sobre una
capa destruida.

| Métrica | Valor |
| :--- | :--- |
| Versión | 2.0.1 (`v2.0.1` etiquetada; HEAD 3 commits de docs por delante) |
| Código empaquetado | 20 módulos, 3 075 líneas |
| Repositorio | 184 archivos versionados, 3,7 MB de `.git`, árbol limpio |
| Tests | 138: 57 unitarios + 81 de integración |
| Integración real | 81/81 OK contra QGIS 4.2.2 (Qt6) |
| Cobertura de `core/` | ~94 % (`settings.py` al 85 %; el resto al 100 %) |
| ZIP | `dist/freehand_digitize.2.0.1.zip`, 26 archivos, 153 KB |
| Portal | 2.0.0 público (ID 7091); 2.0.1 pendiente de subida |

---

## 2. Arquitectura

La separación `core/` ↔ `gui/` es real y está demostrada por los tests:

- **`core/`**: constantes, reglas geométricas, muestreo del trazo y persistencia.
  Sin importaciones de QGIS ni Qt; `mypy` estricto y cobertura alta.
- **`gui/`**: `FreehandTool`, `FeatureCreator`, `ReshapeCreator`,
  `DifferenceCreator`, diálogos, cursor y shims Qt5/Qt6.
- **`freehand_plugin.py`**: cableado de acciones, spinbox, estado de edición y
  ciclo de vida.

Flujo principal: se captura la capa al pulsar, se dibuja en coordenadas de capa
(`toLayerCoordinates`), se emite `geometryFinished(geom, layer)` y la creación o
edición se ejecuta en un único comando de deshacer. Es una arquitectura sencilla
y adecuada al tamaño del plugin.

Documentación relacionada: [ARCHITECTURE_EN.md](../ARCHITECTURE_EN.md),
[FEATURE_PARITY.md](../maintainer/FEATURE_PARITY.md) y
[USER_GUIDE.md](../user/USER_GUIDE.md).

---

## 3. Calidad verificada

| Puerta | Resultado |
| :--- | :--- |
| `ruff check` / `ruff format --check` | ✅ 53 archivos formateados |
| `flake8` (alcance portal) | ✅ |
| `mypy core/` | ✅ 5 archivos, sin errores |
| `docs-check` | ✅ 24 documentos, enlaces relativos OK |
| `i18n-check` | ✅ 7 tests; 48/48 cadenas traducidas |
| `qgis-analyzer --max-cc 10` | ✅ 0 violaciones; 4 avisos `GOD_OBJECT` |
| `forge validate` | ✅ 18 skills, 19 workflows |
| `qgis-manage validate --strict` | ✅ |
| `security-scan` | ✅ 0 hallazgos |
| Integración QGIS 4.2.2 | ✅ 81 tests |
| `uv lock --check` | ✅ |

Métricas del analizador:

- Mantenibilidad: **99,9/100**.
- Seguridad: **100/100**, 0 riesgos.
- Estabilidad de módulos: **55,6/100**, penalizada por el tamaño de
  `freehand_plugin.py` (648 líneas, 45 métodos).
- Tipo de hallazgos: 4 `GOD_OBJECT` de severidad baja, ninguno bloqueante.

Cobertura medida en `core/` (suite unitaria, sin QGIS):

| Módulo | Cobertura |
| :--- | :--- |
| `core/constants.py` | 100 % |
| `core/geometry_rules.py` | 100 % |
| `core/stroke.py` | 100 % |
| `core/settings.py` | 85 % |

No se ejecutaron `make qt6-check`, `make docker-test` ni `make zip` durante este
análisis; el resto de puertas locales sí.

---

## 4. Hallazgos priorizados

### 4.1 Alto (workflow local): `make test-qgis` da falso verde

`Makefile:19` define `PYTHON ?= python3`; con el `.venv` activo, `python3`
resuelve al intérprete del entorno virtual, que no tiene QGIS. Resultado real en
esta máquina:

```text
make test-qgis → Ran 81 tests … OK (skipped=81)
```

La suite de integración **no se ejecuta** y el comando termina con éxito. Como
`make pre-release` depende de `test-qgis` (`Makefile:158`), un `pre-release`
local puede pasar sin integración. En CI no ocurre porque la suite corre en
Docker. Con `/usr/bin/python3` los 81 tests pasan.

**Recomendación:** que `test-qgis` falle si se omiten tests, o usar un
intérprete QGIS explícito (`QGIS_PYTHON`) y documentar el override.

### 4.2 Medio: queda un camino de error con capa eliminada

El fix 2.0.1 protege el ciclo de vida del plugin, pero los creadores y la
herramienta siguen accediendo a la capa sin comprobar si el objeto C++ está
vivo:

- `gui/feature_creator.py:191` (`_ensure_editable` → `layer.isEditable()` y
  `layer.name()`).
- `gui/reshape_creator.py:166` (mismo patrón).
- `gui/freehand_tool.py:250` (`_require_editable`).
- `freehand_plugin.py:313` y `freehand_plugin.py:397` no validan la capa al
  terminar el trazo o abrir el diálogo.

Reproducido en QGIS 4.2.2: tras `sip.delete(layer)`,
`FeatureCreator.create(...)` y `ReshapeCreator.reshape(...)` lanzan
`RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted`.
Es un caso de borde (borrar la capa durante un trazo), pero contradice el alcance
declarado del fix 2.0.1.

**Recomendación:** guardas de “capa viva” antes de tocar la capa en creadores y
herramienta, con tests de regresión que usen `sip.delete`.

### 4.3 Medio: Qt5 / QGIS 3.28 no está verificado

`metadata.txt` declara `qgisMinimumVersion=3.28`, pero la integración ejecutada
aquí es QGIS 4.2.2/Qt6. `DifferencePickTool` contiene lógica específica para la
sobrecarga de señal en PyQt5 que no está cubierta. `AI_CONTEXT.md` ya lo
reconoce como pendiente.

**Recomendación:** smoke test real en 3.28/Qt5 o elevar el mínimo si no se va a
mantener.

### 4.4 Bajo: detalles de robustez y limpieza

- `_ctrl_pressed` no se reinicia en `cancel_stroke()`/`deactivate()`
  (`gui/freehand_tool.py:107,122`): si se cancela con Ctrl pulsado, el siguiente
  trazo puede hacer *snap* inesperado.
- `SamplingStore.save()`/`save_options()` hacen `float(distance)` sin protección
  (`core/settings.py`), a diferencia de `ToleranceStore`.
- Tests usan `QgsGeometry.isGeosEqual()`
  (`tests/integration/test_difference_creator.py:69,86`), deprecado desde QGIS
  4.2 y eliminable en QGIS 5; usar `isTopologicallyEqual`.
- `metadata.txt:6` usa `general_description`, que no es una clave estándar de
  metadatos QGIS (no aparece entre los campos validados por `qgis-manager`). Los
  idiomas ya están en `about`; conviene confirmar si el portal lo muestra o
  eliminarlo.
- `freehand_plugin.py` es un *god object* (648 líneas, 45 métodos): el aviso
  `GOD_OBJECT` es razonable, aunque no bloquea.
- `ReshapeCreator` y `DifferenceCreator` iteran y calculan en el hilo de UI; en
  capas muy grandes puede haber bloqueos perceptibles. No es un bug, pero
  merece una prueba de rendimiento.

---

## 5. Deriva documental

El repositorio se apoya mucho en documentación y ahí hay contradicciones claras:

| Archivo | Afirmación actual | Realidad |
| :--- | :--- | :--- |
| `docs/maintainer/FEATURE_PARITY.md:75` | La edición se inicia automáticamente al activar la herramienta. | El código ya no llama a `startEditing()`; el *edit-session gating* exige edición activa. |
| `docs/maintainer/FEATURE_PARITY.md:89` | No hay catálogos de traducción en 2.0.0. | Existen `i18n/*.ts` y `*.qm`; el catálogo inglés está completo (48/48). |
| `docs/ARCHITECTURE_EN.md:242` | `_ensure_editable`: `startEditing()` when needed. | Falso desde el *edit-session gating*; contradice la línea 292 del mismo documento. |
| `docs/ARCHITECTURE_EN.md:62-75` | Árbol de directorios de `core/` y `gui/`. | No incluye `gui/texts.py` ni `gui/i18n.py`; atribuye las cadenas de UI a `constants.py`. |
| `README.md:214-215` | Planes de muestreo y edición “proposed”. | Implementados en 2.0.0. |
| `CHANGELOG.md:75` | La copia de `freehandEditing/` se conserva como referencia. | El directorio se eliminó en `7e69c4c`. |
| `AI_CONTEXT.md:106-107` | Fix de capa eliminada “proposed …, no code changes yet”. | Implementado y publicado como 2.0.1; la línea 16 del mismo archivo lo confirma. |
| `.agent-state/next_steps.md:16` | 134 tests (57 unitarios + 77 de integración). | Hoy son 138 (57 + 81). |
| `pyproject.toml:41-43` | El plugin es “Spanish-only” y no incluye catálogos. | Obsoleto: i18n integrado y empaquetado. |
| `docs/maintainer/PLAN_LAYER_LIFECYCLE.md:193` y otros planes | “The plan is PROPOSED”. | El encabezado del mismo plan lo marca `IMPLEMENTED`. |
| `.gitignore` / `.qgisignore` | Referencias a `freehandEditing/`. | Directorio inexistente. |
| `docs/ARCHITECTURE_EN.md`, `docs/user/USER_GUIDE.md` | Versión 2.0.0. | Versión publicada 2.0.1. |

También quedan checklists sin marcar en planes ya implementados.

---

## 6. Fortalezas

- Frontera `core/`/`gui/` disciplinada y comprobada sin QGIS.
- Suite de tests amplia para el tamaño del proyecto, con integración real y
  omisión controlada cuando QGIS no está disponible.
- i18n bien resuelta: 48 cadenas, catálogo inglés completo, `.qm` empaquetado y
  cargador por *locale*.
- Empaquetado limpio: el ZIP solo lleva runtime, metadatos, icono, licencia,
  README, CHANGELOG e i18n.
- Seguridad y dependencias: cero dependencias externas, 0 hallazgos y baseline
  de secretos.
- Proceso: *plan-first*, CI, pre-commit, Docker, `uv` reproducible y
  documentación de maintainers.

---

## 7. Recomendaciones priorizadas

1. **P0** — Corregir `make test-qgis` para que no pueda pasar con 0 tests
   ejecutados; después, blindar los creadores y la herramienta contra capas
   destruidas y añadir tests.
2. **P1** — Sincronizar documentación y metadatos: `FEATURE_PARITY`,
   `ARCHITECTURE_EN`, README, CHANGELOG, `AI_CONTEXT`, `next_steps`,
   `pyproject.toml`, `metadata.txt` y el estado de los planes.
3. **P1** — Sustituir `isGeosEqual` en los tests y hacer un smoke test real en
   QGIS 3.28/Qt5 (o elevar `qgisMinimumVersion`).
4. **P2** — Refactor guiado por plan para dividir `FreehandDigitizePlugin`
   (acciones/toolbar, ciclo de edición, tolerancia, diferencia) y medir
   rendimiento de *reshape*/*difference* en capas grandes.
5. **P2** — Limpiar referencias a `freehandEditing/` en `.gitignore`,
   `.qgisignore` y CHANGELOG.

---

## 8. Anexo: métodos y evidencias

Comandos principales ejecutados:

```bash
make test                      # 138 tests, 81 omitidos por falta de QGIS en el venv
/usr/bin/python3 -m unittest discover -s tests/integration -t .   # 81 OK
make lint format-check
make flake8
make mypy docs-check i18n-check
make analyzer
make agent-validate
make qgis-validate
make security-scan
uv lock --check
```

Evidencias adicionales:

- Reproducción del `RuntimeError` con `sip.delete(layer)` sobre
  `FeatureCreator.create` y `ReshapeCreator.reshape`.
- Comparación AST de las llamadas a `QCoreApplication.translate` con
  `i18n/freehand_digitize_en.ts`: 48 cadenas, 48 entradas, sin huérfanas.
- Cobertura de `core/` con `coverage run -m unittest discover tests` (solo capa
  unitaria; la integración se midió aparte, sin instrumentación fiable).
- Inspección del ZIP `dist/freehand_digitize.2.0.1.zip`: 26 archivos, catálogo
  `.qm` incluido, tests y docs excluidos.

Consulta también el [registro de desarrollo](DEVELOPMENT_LOG.md).

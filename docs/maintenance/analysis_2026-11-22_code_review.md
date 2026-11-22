# Análisis de Código y Revisión Manual — Freehand Digitize 2.0.2

> **Tipo:** análisis técnico interno, revisión manual de código y auditoría de calidad.
> **Fecha:** 2026-11-22.
> **Commit analizado:** `9e624a6` (`main`).
> **Entorno de verificación:** QGIS 4.2.2 (Qt6), Python 3.12, `uv` (entorno dev congelado).
> **Alcance:** `core/`, `gui/`, `freehand_plugin.py`, suite de tests e integración.
> **Nota:** este análisis se realizó en modo lectura; el documento es el registro técnico de los hallazgos y propuestas de mejora.

---

## 1. Resumen ejecutivo

Se ha llevado a cabo una auditoría manual exhaustiva del código fuente del plugin **Freehand Digitize** (versión 2.0.2). El plugin presenta una base sólida con estricta separación entre lógica geométrica (`core/`) y la interfaz de QGIS (`gui/`), alta cobertura de pruebas y verificación de tipos.

No obstante, la revisión manual línea a línea ha descubierto **dos defectos críticos de comportamiento en campo** que pasaban desapercibidos en los tests automatizados:

1. **El snapping del vértice final con `Ctrl` falla silenciosamente cuando el cursor se detiene**: la lógica de adelgazamiento por muestreo (`StrokeRecorder.add`) descarta el punto ajustado si el evento de soltar ratón ocurre a menos de `1.5 px` del último movimiento.
2. **`DifferencePickTool` no puede seleccionar entidades recién digitalizadas (`fid < 0`) ni registros con `fid == 0`**: la condición `if feature_id <= 0: return` ignora por completo los IDs negativos asignados por el búfer de edición de QGIS a entidades aún no confirmadas.

Adicionalmente, se identificaron áreas de mejora en la operación de diferencia sin intersección, redundancias en la reversión de comandos de edición y desalineaciones menores entre la documentación y el comportamiento real del bloqueo de edición.

---

## 2. Arquitectura y Fortalezas del Diseño

### 2.1. Desacoplamiento Core / GUI

- **`core/`** (`constants.py`, `geometry_rules.py`, `settings.py`, `stroke.py`):
  - 100 % libre de importaciones de QGIS y Qt.
  - Testeable de forma instantánea sin entorno de ventanas ni ejecutables GIS.
  - Tipado estricto con `mypy` pasando sin errores.
- **`gui/`** (`freehand_tool.py`, `feature_creator.py`, `reshape_creator.py`, `difference_creator.py`, etc.):
  - Centraliza el manejo de la API de QGIS y Qt.
  - Abstracción de compatibilidad Qt5/Qt6 en `gui/qt_compat.py` (normalización de enums y `exec()`).
- **`freehand_plugin.py`**:
  - Orquesta el ciclo de vida del plugin (`initGui`, `unload`).
  - Sincroniza dinámicamente las acciones y el spinbox según el estado de edición y CRS de la capa activa.

### 2.2. Manejo de CRS y coordenadas

- El trazo se captura directamente en coordenadas de la capa activa (`toLayerCoordinates`), eliminando distorsiones o incompatibilidades al trabajar con reproyección al vuelo (*on-the-fly CRS*).
- El muestreo de trazo (`StrokeRecorder`) opera en píxeles de pantalla como predeterminado, haciendo que la densidad del lápiz sea uniforme sin importar la escala o el CRS de la capa.

### 2.3. Transaccionalidad y Robustez

- Todas las operaciones de modificación de geometrías están envueltas en comandos de edición atómicos (`beginEditCommand` y `endEditCommand`), lo que permite revertir cambios con un solo `Ctrl+Z`.
- Implementación de `is_layer_alive` con `sip.isdeleted` para evitar caídas del proceso C++ por capas eliminadas mientras el plugin las referencia.

---

## 3. Hallazgos Críticos

### 3.1. Falla silenciosa del snapping en el último vértice (`FreehandTool`)

- **Archivos:** `gui/freehand_tool.py` (líneas 237–250) y `core/stroke.py` (líneas 90–110).
- **Mecanismo del error:**
  1. Durante el arrastre con el ratón, `canvasMoveEvent` registra puntos a medida que se mueven más de `1.5 px`.
  2. Al llegar al destino final, el usuario detiene el cursor sobre el vértice objetivo, pulsa `Ctrl` y suelta el botón.
  3. `canvasReleaseEvent` detecta `_ctrl_pressed` y ejecuta `_add_release_point`:

     ```python
     device = event.pos()
     layer_point = self.toLayerCoordinates(layer, device)
     layer_point, map_point = self._snapped_point(layer, device, layer_point, event.mapPoint())
     if self._recorder.add(
         (layer_point.x(), layer_point.y()),
         (device.x(), device.y()),
     ):
         self._rubber.addPoint(map_point)
     ```

  4. En `StrokeRecorder.add`, se evalúa la distancia en pantalla:

     ```python
     dx = device[0] - self._last_device[0]
     dy = device[1] - self._last_device[1]
     if dx * dx + dy * dy < distance * distance:
         return False
     ```

  5. Como el cursor se detuvo antes de soltar el botón, `device` es idéntico a `_last_device`. La distancia es `0`, la función retorna `False` y el punto ajustado **nunca se agrega al trazo**.
- **Impacto:** La geometría se genera con el último punto libre del movimiento y se ignora el snapping que el usuario intentó forzar con `Ctrl`.
- **Causa en los tests:** `test_ctrl_snaps_the_first_vertex` solo validaba el primer vértice, no el vértice final tras un arrastre previo.

---

### 3.2. Incapacidad de seleccionar entidades temporales con `DifferencePickTool`

- **Archivo:** `gui/difference_pick_tool.py` (línea 48).
- **Mecanismo del error:**

  ```python
  def _on_feature_identified(self, feature: Any) -> None:
      try:
          feature_id = feature.id() if isinstance(feature, QgsFeature) else int(feature)
      except (AttributeError, TypeError, ValueError):
          return
      if feature_id <= 0:
          return
  ```

  En la arquitectura de edición de QGIS:
  - Las entidades recién digitalizadas en el búfer de edición que aún no han sido guardadas en disco reciben **IDs negativos** (`-1, -2, -3...`).
  - En ciertos formatos de archivo (como Shapefile), el primer registro tiene `fid == 0`.
- **Impacto:** Si un usuario digitaliza dos polígonos usando Freehand Digitize y luego activa la herramienta de corte para restar uno de otro, **ningún clic sobre las geometrías recién creadas responde**. El usuario percibe la herramienta como bloqueada o rota.
- **Solución propuesta:** Validar `feature.isValid()` y que el ID no sea nulo (`feature_id is not None`), eliminando el filtro arbitrario `feature_id <= 0`.

---

## 4. Oportunidades de Mejora y Casos Borde

### 4.1. Operación de diferencia sin solapamiento (`DifferenceCreator`)

- **Archivo:** `gui/difference_creator.py`.
- **Detalle:** Cuando la entidad cortadora no intersecta a la entidad objetivo, el motor GEOS retorna la geometría objetivo intacta. `DifferenceCreator` actualmente considera esto un éxito, abre un comando de edición, actualiza la capa (sin cambios reales) y notifica: *"Diferencia de entidad aplicada"*.
- **Mejora:** Comprobar si `target.geometry().intersects(cutter.geometry())` antes de operar. Si no intersectan, emitir un mensaje informativo avisando que no hay solapamiento y evitar crear una entrada vacía en la pila de deshacer.

### 4.2. Reversión redundante en `ReshapeCreator`

- **Archivo:** `gui/reshape_creator.py` (líneas 142–153).
- **Detalle:** Si falla una geometría durante una reforma múltiple, el código invoca `self._restore(layer, originals, changed)` antes de `layer.destroyEditCommand()`. En QGIS, `destroyEditCommand()` ya descarta atómicamente todos los cambios producidos dentro del comando. Restaurar manualmente antes de destruir el comando es redundante y puede generar eventos adicionales en el búfer.

### 4.3. Etiquetas de entidades en `DifferenceDialog`

- **Archivo:** `gui/difference_dialog.py` (función `_feature_label`).
- **Detalle:** La etiqueta se construye buscando el primer campo con un valor de texto no nulo. En capas con claves primarias o campos internos, esto puede mostrar identificadores poco significativos.
- **Mejora:** Utilizar la expresión o campo de visualización configurado en la capa (`layer.displayExpression()` o `layer.displayField()`) y usar el primer campo no vacío solo como respaldo.

---

## 5. Deuda Técnica y Documentación

### 5.1. Desfase en la documentación de la sesión de edición

- En `docs/maintainer/FEATURE_PARITY.md` (filas 41 y 74–77) y en los docstrings de `_activate_tool` / `_activate_reshape_tool` en `freehand_plugin.py`, se indica que la herramienta *"inicia automáticamente la sesión de edición al activarse"*.
- Conforme a `docs/maintainer/PLAN_EDIT_SESSION.md`, el comportamiento fue modificado para exigir de forma estricta que la capa ya se encuentre en edición (`layer.isEditable()`). La documentación y docstrings deben actualizarse para reflejar la realidad del código.

### 5.2. Advertencias de deprecación en QGIS 4.2+

- En `tests/integration/test_difference_creator.py` se utiliza `QgsGeometry.isGeosEqual()`, lo cual genera advertencias de deprecación en QGIS 4.2+ en favor de `isTopologicallyEqual()`.

---

## 6. Recomendaciones y Hoja de Ruta

Conforme al procedimiento obligatorio **Plan-First** (`docs/maintainer/CHANGE_PROCEDURE.md`), cualquier modificación de código requerirá la aprobación explícita de un plan técnico.

### Prioridad Inmediata (Corrección de Bugs)

1. **Crear `PLAN_SNAPPING_AND_PICK_FIXES.md`**:
   - Resolver la omisión del snapping terminal en `FreehandTool._add_release_point`.
   - Permitir la selección de FIDs negativos y cero en `DifferencePickTool`.
   - Incorporar pruebas unitarias y de integración específicas para ambos escenarios.

### Prioridad Media (Refinamiento UX)

1. **Validación previa en `DifferenceCreator`**:
   - Evitar transacciones vacías si no hay intersección entre las geometrías.
2. **Alineación documental**:
   - Actualizar `FEATURE_PARITY.md` y docstrings en `freehand_plugin.py` para coincidir con la política de edición estricta.

### Evolución Funcional (v2.1.0+)

1. **Implementar Etapa 1 del Roadmap (`PLAN_FEATURE_ROADMAP.md`)**:
   - Deshacer el último vértice en tiempo real con la tecla `Backspace` durante el trazo a mano alzada.

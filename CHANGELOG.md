# Changelog

## 2.0.0 — 2026-11-19

Reescritura moderna del plugin con paridad funcional respecto a
[`freehandEditing`](https://github.com/vinayan/freehandEditing) y soporte
QGIS 3.28–4.x (Qt5/Qt6).

### Añadido

- Tolerancia de simplificación ajustable (0–5, 3 decimales) en la barra de
  digitalización, persistida en `QgsSettings` con migración de la clave
  heredada `/freehandEdit/tolerance`.
- Snapping con `Ctrl` del primer y último vértice usando el motor de snapping
  de QGIS.
- Cursor de lápiz (XPM) con respaldo a cruz.
- Formulario de atributos de QGIS, con supresión de clics mientras es modal.
- Valores por defecto del proveedor mediante
  `QgsVectorLayerUtils.createFeature`.
- Comandos de edición (`beginEditCommand`/`endEditCommand`) para deshacer la
  entidad como una sola operación.
- Aviso ante geometrías no válidas (¿usar de todos modos?).
- Habilitación de la acción solo para capas vectoriales de línea/polígono
  editables, sincronizada con la capa activa y el cambio de herramienta.
- Arquitectura `core/` (sin QGIS) y `gui/` (PyQGIS), con shims PyQt5/PyQt6.
- Sistema agéntico (Agentic Forge), tests unitarios y de integración, CI,
  pre-commit y empaquetado con `qgis-manage`.

### Cambiado

- El trazo se guarda en coordenadas de capa (`toLayerCoordinates`), no en el
  CRS del proyecto; se elimina el riesgo de geometrías en el CRS equivocado.
- El muestreo del trazo usa distancia en píxeles de dispositivo, no
  `mapUnitsPerPixel` sobre coordenadas de capa.
- El botón secundario termina el trazo (comportamiento del original), en lugar
  de cancelarlo; `Esc` sigue cancelando.
- La simplificación ya no está fijada a 2 px: usa la tolerancia configurada.
- Las geometrías inválidas ya no se corrigen en silencio: se pregunta.

### Corregido

- Entidades creadas en el CRS del proyecto cuando la capa usaba otro CRS.
- Falta de valores por defecto y de formulario de atributos.
- Ausencia de comando de deshacer para la entidad creada.
- Acción siempre habilitada sobre capas de puntos o no editables.
- `QAction` importado de forma no portable entre PyQt5/PyQt6.

### Eliminado

- Dependencia del código PyQt4/QGIS 2 del upstream; se conserva como referencia
  en `freehandEditing/` (excluido del ZIP).
- `supportsQt6` en `metadata.txt` (obsoleto con qgis-manage 0.17; QGIS 4 Ready
  se marca con `qgisMaximumVersion >= 4.0`).

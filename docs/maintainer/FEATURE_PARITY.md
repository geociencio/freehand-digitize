# Paridad funcional con `freehandEditing`

Comparación entre el plugin original
[`vinayan/freehandEditing`](https://github.com/vinayan/freehandEditing) (commit
`e550544`, GPL-2.0, 2010–2012 Pavol Kapusta / 2013 Larry Shaffer) y esta versión
2.0.0 para QGIS 3.28–4.x.

- Fuente original conservada como referencia en `freehandEditing/` (sin
  seguimiento en git y excluida del ZIP).
- Implementación nueva: `core/`, `gui/` y `freehand_plugin.py`.

---

## 1. Matriz de paridad

| # | Capacidad | Original | 1.0.0 (reescritura) | 2.0.0 | Dónde |
| :-- | :--- | :---: | :---: | :---: | :--- |
| 1 | Dibujar líneas y polígonos arrastrando | ✅ | ✅ | ✅ | `gui/freehand_tool.py` |
| 2 | Cursor de lápiz | ✅ | ❌ | ✅ | `gui/cursor.py` |
| 3 | Tolerancia 0–5, 3 decimales, paso 0.1 | ✅ | ❌ | ✅ | `freehand_plugin.py` |
| 4 | Persistencia de la tolerancia | ✅ | ❌ | ✅ | `core/settings.py` |
| 5 | Tolerancia 0 en CRS geográfico | ✅ | ❌ | ✅ | `core/geometry_rules.py` |
| 6 | Snapping del primer vértice con `Ctrl` | ✅ | ❌ | ✅ | `gui/freehand_tool.py` |
| 7 | Snapping del último vértice con `Ctrl` | ❌ | ❌ | ✅ (mejora) | `gui/freehand_tool.py` |
| 8 | Trazo en coordenadas de capa | ✅ | ❌ | ✅ | `gui/freehand_tool.py` |
| 9 | Reproyección al vuelo | ✅ | ❌ | ✅ (implícita) | `toLayerCoordinates` |
| 10 | Simplificación con la tolerancia | ✅ | fija 2 px | ✅ | `gui/feature_creator.py` |
| 11 | Aviso de geometría no válida | ✅ | ❌ | ✅ | `gui/feature_creator.py` |
| 12 | Valores por defecto del proveedor | ✅ | ❌ | ✅ | `gui/feature_creator.py` |
| 13 | Formulario de atributos modal | ✅ | ❌ | ✅ | `gui/feature_creator.py` |
| 14 | Ignorar clics durante el modal | ✅ | ❌ | ✅ | `gui/freehand_tool.py` |
| 15 | Comando de edición / deshacer | ✅ | ❌ | ✅ | `gui/feature_creator.py` |
| 16 | Solo capas editables de línea/polígono | ✅ | ❌ | ✅ | `freehand_plugin.py` |
| 17 | Botón secundario detiene el trazo | ✅ | ❌ | ✅ | `gui/freehand_tool.py` |
| 18 | Ignorar `press` repetidos al dibujar | ✅ | ❌ | ✅ | `gui/freehand_tool.py` |
| 19 | Rubber band con relleno en polígonos | ✅ | ❌ | ✅ | `gui/freehand_tool.py` |
| 20 | Mínimo de vértices | >2 | ≥3 | ✅ (3 polígono, 2 línea) | `core/geometry_rules.py` |
| 21 | Muestreo por píxel de dispositivo | ❌ | parcial | ✅ | `core/stroke.py` |
| 22 | Límite de puntos por trazo | ❌ | ❌ | ✅ | `core/stroke.py` |
| 23 | `Esc` cancela el trazo | ❌ | ✅ | ✅ | `gui/freehand_tool.py` |
| 24 | Auto-inicio de edición | ❌ | ✅ | ✅ (decisión) | `freehand_plugin.py` |
| 25 | Mensajes de error robustos | parcial | ✅ | ✅ | `freehand_tool.py`, `feature_creator.py` |

Leyenda: ✅ implementado · ❌ ausente · “mejora/decisión” = desviación
deliberada documentada abajo.

---

## 2. Defectos de la reescritura 1.0.0 que se corrigieron

| Defecto | Consecuencia | Corrección |
| :--- | :--- | :--- |
| `e.mapPoint()` en lugar de `toLayerCoordinates()` | Entidad en el CRS del proyecto, no en el de la capa | Trazo almacenado en coordenadas de capa |
| Simplificación fija `mapUnitsPerPixel() * 2` | Sin control del usuario; el valor depende del zoom | Spinbox + `QgsGeometry.simplify(tolerance)` |
| Sin formulario de atributos | Entidades sin atributos ni defaults | `iface.getFeatureForm()` + `QgsVectorLayerUtils.createFeature` |
| `makeValid()` silencioso | El usuario no sabe que la geometría era inválida | `QMessageBox` de confirmación |
| Sin `beginEditCommand` | Deshacer no revierte la entidad de forma atómica | Comando de edición |
| Acción siempre habilitada | Se puede activar en puntos o capas no editables | `_is_drawable()` + señales de capa |
| `QAction` desde `QtWidgets` | No portable a PyQt6 puro | `gui/qt_compat.py` |
| Botón derecho cancela | No reproduce el “halt drag” del original | Release de cualquier botón termina |
| Muestreo sobre coordenadas de capa | Umbral incorrecto con CRS distintos | Distancia en píxeles de dispositivo |
| Sin `setIgnoreClick` | Clics durante el modal pueden iniciar trazos | Callback durante el formulario |

---

## 3. Decisiones y desviaciones documentadas

1. **Auto-inicio de edición.** El original exigía que la capa ya estuviera en
   edición; aquí se inicia automáticamente al activar la herramienta (se
   conserva la comodidad de la versión 1.0.0). La acción sigue deshabilitada
   para capas que no soportan edición.
2. **Línea con dos puntos.** El original exigía `> 2` vértices incluso para
   líneas; una línea recta de dos puntos es válida, así que se permiten 2. Los
   polígonos siguen necesitando 3 puntos distintos antes de cerrar el anillo.
3. **Snapping del último vértice.** Mejora sobre el original, que solo ajustaba
   el primero. Respeta la configuración de snapping de QGIS; si no hay match,
   usa el punto libre.
4. **Geometría inválida.** Se pregunta “¿usar de todos modos?” en lugar de
   aplicar `makeValid()` en silencio, igual que el original.
5. **Botón secundario.** Se mantiene la semántica del original: termina el
   trazo; `Esc` es el mecanismo de cancelación.
6. **Idioma.** La UI está en español (como la versión 1.0.0); el código, los
   tests y la documentación técnica están en inglés. No hay catálogos de
   traducción en 2.0.0.

---

## 4. Migración de APIs (QGIS 2 → QGIS 3.28/4)

| Original (QGIS 2) | 2.0.0 |
| :--- | :--- |
| `QGis.Line` / `QGis.Polygon` | `Qgis.GeometryType.Line` con fallback a `Qgis.Line` |
| `QgsMapCanvasSnapper` + `QgsSnapper` | `canvas.snappingUtils().snapToCurrentLayer/snapToMap` |
| `validateGeometry()` | `isGeosValid()` |
| `pendingFields()` + `provider.defaultValue(i)` | `QgsVectorLayerUtils.createFeature()` |
| `exec_()` | `exec()` con fallback a `exec_()` |
| `QgsCoordinateTransform(project, layer)` | No hace falta: el trazo ya está en CRS de capa |
| `QAction` en `QtWidgets` | `QtGui.QAction` con fallback |
| `Qt.LeftButton` | `Qt.MouseButton.LeftButton` con fallback |
| `currentLayerChanged['QgsMapLayer*']` | `iface.currentLayerChanged` |
| `editingStarted`/`editingStopped` como control de habilitación | `self.iface.activeLayer()` + `supportsEditing()` |

---

## 5. Verificación

Los comportamientos de la matriz están cubiertos por:

- `tests/integration/test_freehand_tool.py` — trazo de línea/polígono, cierre de
  anillo, trazo corto, botón secundario, `Esc`, `setIgnoreClick`, capa de puntos,
  snapping con `Ctrl`.
- `tests/integration/test_feature_creator.py` — valores por defecto, deshacer,
  formulario aceptado/cancelado, geometría inválida (sí/no), simplificación,
  geometría vacía, inicio de edición.
- `tests/integration/test_plugin.py` — habilitación por capa, CRS geográfico vs
  proyectado, activación, extremo a extremo y descarga.
- `tests/core/` — reglas de geometría, muestreo, tolerancia, settings, sintaxis
  Python 3.9.

Comandos:

```bash
make test        # unitarios (sin QGIS)
make test-qgis   # integración con QGIS 4
make test-all
```

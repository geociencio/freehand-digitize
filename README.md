# Freehand Digitize

Digitalización a mano alzada de **líneas y polígonos** en QGIS, con las
funciones del clásico plugin [`freehandEditing`](https://github.com/vinayan/freehandEditing)
recuperadas y adaptadas a **QGIS 3.28–4.x** (Qt5 y Qt6).

Arrastra con el botón izquierdo sobre el mapa y al soltar se crea la entidad en
la capa activa. El trazo se guarda en el **CRS de la capa** (con reproyección al
vuelo) y se simplifica con la tolerancia configurable.

---

## Funciones

| Función | Detalle |
| :--- | :--- |
| Dibujo libre | Líneas y polígonos; el polígono se cierra automáticamente. |
| Tolerancia de simplificación | `QDoubleSpinBox` 0–5, 3 decimales, paso 0.1; se guarda entre sesiones. |
| CRS geográfico | La tolerancia se desactiva y se aplica 0 (los grados no son metros). |
| Snapping con `Ctrl` | Ajusta el primer y el último vértice a vértices existentes (motor de snapping de QGIS). |
| Cursor de lápiz | Cursor XPM específico, con `CrossCursor` como respaldo. |
| Formulario de atributos | Se muestra el formulario de QGIS (si está habilitado) con cancelación limpia. |
| Valores por defecto | `QgsVectorLayerUtils.createFeature` aplica defaults y restricciones del proveedor. |
| Deshacer | La entidad se crea dentro de un `beginEditCommand`/`endEditCommand`. |
| Geometría no válida | Se pregunta si usarla igualmente en lugar de corregirla en silencio. |
| Habilitación por capa | Solo capas vectoriales de línea/polígono editables. |
| Botón secundario | Termina el trazo en curso (como el plugin original). |
| `Esc` | Cancela el trazo; si no hay trazo, desactiva la herramienta. |
| Sin dependencias | No requiere paquetes Python externos; usa `qgis.PyQt`. |

### Paridad con `freehandEditing`

La comparación completa está en
[`docs/maintainer/FEATURE_PARITY.md`](docs/maintainer/FEATURE_PARITY.md). Se
recuperaron: tolerancia persistente, snapping con `Ctrl`, cursor de lápiz,
formulario de atributos, valores por defecto, comandos de deshacer, aviso de
geometría inválida, CRS de capa y habilitación por tipo de capa.

---

## Requisitos

- **QGIS 3.28 o superior**, incluido QGIS 4.x (Qt6).
- Sin dependencias Python adicionales: QGIS aporta PyQt, GDAL y GEOS.

## Instalación

### Desde el ZIP

1. Descarga `dist/freehand_digitize.<versión>.zip`.
2. En QGIS: **Complementos → Administrar e instalar complementos → Instalar a
   partir de ZIP**.
3. Activa **Freehand Digitize**.

### Desde el repositorio (desarrollo)

```bash
# Despliegue directo en el perfil de QGIS 4
uv run qgis-manage deploy --no-compile --qgis-version 4
```

También puedes copiar esta carpeta a
`~/.local/share/QGIS/QGIS4/profiles/default/python/plugins/freehand_digitize`.

---

## Uso

1. Selecciona una **capa de línea o polígono** y ponla en edición (la
   herramienta también puede iniciar la edición).
2. Pulsa **Dibujo a mano alzada** en la barra de digitalización o en
   **Vector → Freehand Digitize**.
3. Arrastra con el botón izquierdo para dibujar.
4. Suelta para crear la entidad. Si el formulario de atributos está habilitado,
   se abrirá antes de añadirla.
5. Ajusta la **tolerancia** en el cuadro de la barra de digitalización (0 = sin
   simplificación).

### Atajos y botones

| Acción | Efecto |
| :--- | :--- |
| Botón izquierdo + arrastrar | Dibuja el trazo. |
| `Ctrl` (al empezar/terminar) | Ajusta el primer/último vértice al snapping de QGIS. |
| Soltar cualquier botón | Termina el trazo (el secundario lo detiene). |
| `Esc` con trazo en curso | Cancela el trazo y mantiene la herramienta. |
| `Esc` sin trazo | Desactiva la herramienta. |

> El snapping con `Ctrl` respeta la configuración de snapping de QGIS
> (tolerancia, modo y capas). Si no hay ningún vértice dentro de la tolerancia,
> se usa el punto libre.

---

## Arquitectura

```
freehand_digitize/
├── __init__.py              # classFactory
├── freehand_plugin.py       # acción, spinbox, señales, ciclo de vida
├── core/                    # lógica pura, sin QGIS ni Qt
│   ├── constants.py
│   ├── geometry_rules.py
│   ├── settings.py
│   └── stroke.py
├── gui/                     # PyQGIS / Qt
│   ├── cursor.py
│   ├── feature_creator.py
│   ├── freehand_tool.py
│   ├── geometry_factory.py
│   └── qt_compat.py
└── tests/                   # unitarios (sin QGIS) e integración (QGIS real)
```

- `core/` no importa `qgis` ni Qt; recibe valores planos y es testeable sin QGIS.
- `gui/` concentra las APIs de PyQGIS y los shims PyQt5/PyQt6.

---

## Desarrollo y QA

El entorno de desarrollo se gestiona con [`uv`](https://docs.astral.sh/uv/); el
plugin en sí no se instala con `pip`.

```bash
uv sync --frozen            # entorno de desarrollo
make test                   # tests unitarios (sin QGIS)
make test-qgis              # integración contra el QGIS del sistema
make lint                   # ruff
make flake8                 # flake8 (alcance del portal QGIS)
make mypy                   # tipos de core/
make analyzer               # qgis-analyzer, CC <= 10
make agent-validate         # valida el sistema agéntico
make qgis-validate          # metadata y estructura
make zip                    # ZIP + validación del artefacto
```

La guía de modernización con `uv` está en
[`docs/maintainer/uv_modernization_guide.md`](docs/maintainer/uv_modernization_guide.md).

### CI

`.github/workflows/test.yml` ejecuta:

- lint, formato, flake8, mypy, `forge validate` y `qgis-manage validate`;
- tests unitarios sin QGIS;
- comprobación de enums Qt6/PyQt6 (`pyqgis4-checker`);
- tests de integración en un contenedor QGIS.

---

## Documentación

- [Arquitectura](docs/ARCHITECTURE_EN.md)
- [Guía de estilo de documentación](docs/maintainer/DOCS_STYLE_GUIDE.md)
- [Convenciones de commit](docs/maintainer/COMMIT_GUIDELINES.md)
- [Convenciones de la guía de usuario](docs/maintainer/USER_GUIDE_CONVENTIONS.md)
- [Registro de desarrollo](docs/maintenance/DEVELOPMENT_LOG.md)
- [Informe de paridad con freehandEditing](docs/maintainer/FEATURE_PARITY.md)
- [Guía de modernización con uv](docs/maintainer/uv_modernization_guide.md)

## Licencia y atribución

GPL-2.0. El plugin original **Freehand Editing** es obra de Pavol Kapusta
(2010–2012) y Larry Shaffer (2013); esta versión moderna conserva sus ideas y
parte de su comportamiento (cursor XPM, semántica de eventos, tolerancia y
formulario). Consulta [`LICENSE`](LICENSE).

Los metadatos apuntan al repositorio original de `freehandEditing`; si publicas
esta versión en un repositorio propio, actualiza `homepage`, `repository` y
`tracker` en `metadata.txt` antes de subirla a <https://plugins.qgis.org/>.

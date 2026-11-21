# Guía del Registro de Desarrollo

> Versión 2.0.0 | Última actualización: 2026-11-19
>
> Adaptada de la guía de SecInterp para el registro
> [`docs/maintenance/DEVELOPMENT_LOG.md`](../maintenance/DEVELOPMENT_LOG.md).

El registro de desarrollo conserva la memoria técnica de las sesiones. Todas las
personas (y agentes) que lo actualicen deben seguir estas reglas.

## 1. Orden cronológico inverso

Las entradas **nuevas** se insertan siempre en la **parte superior**, justo
debajo del título y la introducción del archivo:

- lo más reciente arriba;
- lo más antiguo abajo.

## 2. Formato del encabezado

Cada sesión empieza con un encabezado de nivel 2 con fecha y título:

```markdown
## [AAAA-MM-DD] - Título de la sesión (HH:MM)
```

La hora es la de cierre de la sesión (zona horaria local del equipo).

## 3. Secciones estándar

| Sección | Contenido |
| :--- | :--- |
| `### Resumen` | Objetivo de la sesión en uno o dos párrafos. |
| `### Logros` | Lista de tareas completadas, con archivos o módulos afectados. |
| `### Resultados` | Métricas reales: tests, gates, ZIP, hallazgos. |
| `### Documentación` | Enlaces a planes, informes de paridad, guías y commits. |

No inventes métricas: copia los resultados de las herramientas ejecutadas en la
sesión. Si un gate no se ejecutó, indícalo explícitamente.

## 4. Separadores

Usa tres guiones `---` entre sesiones para una separación visual clara.

## 5. Contenido prohibido

- Secretos, credenciales, tokens o rutas locales de usuario.
- Volcados de stack traces completos (resume el error y enlaza el archivo).
- Más de cinco líneas de código seguidas (enlaza al archivo).
- Métricas estimadas o inventadas.

## 6. Ejemplo

```markdown
## [2026-11-19] - Paridad 2.0.0 y sistema agéntico (21:25)

### Resumen
Se restauró la paridad funcional con freehandEditing y se adaptó el sistema
agéntico y el QA del proyecto de referencia.

### Logros
- Arquitectura core/gui con shims PyQt5/PyQt6.
- Tests unitarios e integración QGIS 4 y Qt5.

### Resultados
- 145 tests (57 unitarios, 88 de integración).
- `make zip`: artefacto validado, 0 hallazgos críticos.

### Documentación
- Plan: `docs/maintainer/PLAN_FREEHAND_PARITY.md`.
- Paridad: `docs/maintainer/FEATURE_PARITY.md`.

---
```

## 7. Cierre de sesión

Al cerrar una sesión:

1. añade la entrada al registro;
2. actualiza `.agent-state/task.md` y `.agent-state/next_steps.md`;
3. ejecuta `make pre-release` (o registra qué gates no se pudieron ejecutar);
4. si hay lecciones reutilizables, añádelas a
   `.agent-state/memory/AGENT_LESSONS.md`.

Consulta también [COMMIT_GUIDELINES.md](COMMIT_GUIDELINES.md) para el formato de
los commits y [DOCS_STYLE_GUIDE.md](DOCS_STYLE_GUIDE.md) para la documentación.

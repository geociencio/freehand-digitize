# Registro de Desarrollo

> Registro de sesiones técnicas de Freehand Digitize. Las entradas nuevas se
> insertan arriba; consulta
> [`docs/maintainer/LOGGING_GUIDELINES.md`](../maintainer/LOGGING_GUIDELINES.md)
> para el formato.

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

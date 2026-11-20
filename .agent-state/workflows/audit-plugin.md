---
description: Full or partial plugin audit with qgis-plugin-analyzer and the repository QA gates.
agent: auditor
skills: [project-context, coding-standards, qgis-migration-4x]
validation: |
  - qgis-analyzer reports no function above CC 10
  - ruff, flake8 and mypy are clean
  - PyQt5 usage is none and no Qt6 enum error is reported
---

# Workflow: Plugin Audit

Static audit of the plugin code. The analyzer is the source of truth for
complexity, docstrings, architecture and security; the QGIS portal gates are
covered by `make flake8` and `make qgis-validate`.

## Steps

1. **Complexity and architecture** (blocking):

   ```bash
   make analyzer
   ```

   Review `analysis_results/` and fail the audit if any function exceeds CC 10 or
   the module-size gate fails.

2. **Lint, format and types** (blocking):

   ```bash
   make format-check
   make lint
   make flake8
   make mypy
   ```

3. **Qt5/Qt6 and QGIS 4 readiness**:

   ```bash
   make qt6-check   # requires Docker
   ```

   Expected: no `Enum error` in `pyqt6_checker.log`, and no
   `PyQt5`/`PyQt6` imports outside `qgis.PyQt`.

4. **Security** (release scope):

   ```bash
   make security-scan
   ```

   Expected: no CRITICAL Bandit/detect-secrets finding.

5. **Metadata and artifact**:

   ```bash
   make qgis-validate
   make zip
   ```

6. **Internationalization note**: this plugin's UI is Spanish-only in 2.0.0 and
   ships no catalogs, so `MISSING_I18N` is disabled in the analyzer profile. Do
   not report it as a regression; revisit only if i18n is reintroduced.

## Expected result

- A short report listing: analyzer score, CC gate, lint/types status, security
  status and artifact status.
- No blocking finding without a linked fix or an explicit follow-up task in
  `.agent-state/next_steps.md`.

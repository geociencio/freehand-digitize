---
description: Mandatory plan-first procedure before any code change.
agent: architect
skills: [plan-first, project-context, documentation-standards]
validation: |
  - An implementation plan exists under docs/maintainer/PLAN_<TOPIC>.md
  - The plan contains goal, scope, API evidence, design, tests, i18n, risks, procedure and rollback
  - The user explicitly approved the plan before code edits
  - The plan is updated to IMPLEMENTED with verification results at close
---

# Workflow: Plan Change

Use this workflow for every code, UI, test, metadata, CI, packaging or
translation-catalog change. Docs-only changes may skip it.

Full procedure: [CHANGE_PROCEDURE.md](../../docs/maintainer/CHANGE_PROCEDURE.md).

## Steps

1. **Triage**
   State whether the request touches code. If it does, announce:
   “No code changes until the implementation plan is approved.”

2. **Analyze (read-only)**
   - Read the affected modules and tests; cite real paths.
   - Verify APIs in the target QGIS/PyQt version and record the evidence.
   - Prototype only in ephemeral files; do not edit the repository.
   - List constraints: QGIS 3.28–4.x, Qt5/Qt6, Core/GUI boundary, no runtime
     dependencies, i18n, packaging, backward compatibility.

3. **Write the plan**
   Create `docs/maintainer/PLAN_<TOPIC>.md` from the template in the procedure:
   status, goal, scope/non-goals, current state, API evidence, UX, design,
   tests, i18n, versioning, risks, acceptance criteria, implementation procedure,
   verification commands and rollback.

4. **Ask for approval**
   Present the plan path, the 3–5 open decisions and the risks. Ask explicitly:
   “Do you approve this plan?” Wait. Do not write code.

5. **Implement the approved scope**
   Follow the planned order, add tests with the code, and update the plan as
   steps complete. If scope or design changes, stop and re-approve.

6. **Verify**
   Run the gates from the plan, at minimum:

   ```bash
   make pre-release
   make zip
   make security-scan
   make qt6-check
   ```

7. **Close**
   Update changelog, README/user guide/architecture, metadata if needed,
   `.agent-state/task.md`, `next_steps.md`, `docs/maintenance/DEVELOPMENT_LOG.md`
   and mark the plan `IMPLEMENTED` with the commit hash and results.

## Stop conditions

- Missing API, file or tool referenced by the plan.
- Scope change beyond the approved plan.
- The same test failure survives three fix attempts.
- Core/GUI or Qt5/Qt6 compatibility would be violated.
- A new runtime dependency is required.
- Packaging or metadata validation cannot pass.

## Example

[PLAN_RESHAPE.md](../../docs/maintainer/PLAN_RESHAPE.md) — proposed freehand
reshape feature; not approved for code yet.

---
name: plan-first
description: Mandatory plan-before-code procedure. Use before changing Python code, UI behaviour, tests, metadata, CI, packaging or translation catalogs; analyze, write an implementation plan with procedures, wait for explicit approval, then implement.
---

# Plan First

## When to use this skill

Use it **before any code change** under `core/`, `gui/`, `freehand_plugin.py`,
`tests/`, `metadata.txt`, CI/build/packaging or translation catalogs. Use it also
when a request is ambiguous about scope.

Documentation-only changes may skip the plan, but still run `make docs-check`
and update the project state.

## Non-negotiable rule

> Analyze → write `docs/maintainer/PLAN_<TOPIC>.md` with the procedures → get
> explicit user approval → only then edit code.

A chat description is not a plan. The plan must be a file in the repository so
it can be reviewed, diffed and linked from the commit. Do not edit code while
waiting for approval; do not infer approval from silence or a new question.

The full procedure is in
[CHANGE_PROCEDURE.md](../../../docs/maintainer/CHANGE_PROCEDURE.md).

## Workflow

1. **Triage** — say whether the request is code or docs. If code, announce that
   no code will be touched until approval.
2. **Analyze** — read the real modules/tests, verify QGIS/PyQt APIs, prototype
   only in ephemeral files (e.g. `/tmp`), and record the evidence.
3. **Plan** — write the plan using the template in the procedure. Include goal,
   scope/non-goals, current state, API evidence, UX, files/data flow, tests,
   i18n, versioning, risks, acceptance criteria, step-by-step procedure,
   verification and rollback.
4. **Ask** — present the plan path and the 3–5 open decisions; ask explicitly
   “Do you approve this plan?”.
5. **Implement** — only the approved scope, in small steps, tests alongside code.
6. **Verify** — `make pre-release`, plus the gates named in the plan.
7. **Close** — mark the plan `IMPLEMENTED`, update changelog/docs/state and
   commit.

## Checklist

- [ ] Is the request a code/behaviour change?
- [ ] Does `docs/maintainer/PLAN_<TOPIC>.md` exist and contain all required
      sections?
- [ ] Were API claims verified against the target QGIS/PyQt version?
- [ ] Did the user explicitly approve the plan?
- [ ] Are tests, i18n, versioning and rollback covered?
- [ ] Did the implementation stay within the approved scope?
- [ ] Was the plan updated with results and the commit hash?

## Stop conditions

Stop and ask the user when an API/path is missing, the scope changes, tests fail
three times on the same cause, the Core/GUI boundary or Qt5/Qt6 compatibility is
at risk, a runtime dependency is needed, or packaging validation cannot pass.

## Example

[PLAN_RESHAPE.md](../../../docs/maintainer/PLAN_RESHAPE.md) is the proposed plan
for the freehand reshape feature. It must remain unapproved code-wise until the
user confirms its open decisions.

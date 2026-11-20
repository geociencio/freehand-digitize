# Change Procedure — Plan First

> Version 2.0.0 | Last Updated: 2026-11-19
>
> **Mandatory from 2026-11-19.** No code change may start before an
> implementation plan and its procedures are written and approved by the user.

This procedure applies to every change under `core/`, `gui/`,
`freehand_plugin.py`, `tests/`, and to behaviour/configuration changes
(`metadata.txt`, CI, build, packaging, translations). Documentation-only changes
may skip the plan, but still follow the verification and state-update steps.

The agent-facing counterparts are:

- skill: `.agent-state/skills/plan-first/SKILL.md`
- workflow: `/plan-change` (`.agent-state/workflows/plan-change.md`)

---

## 1. Non-negotiable rule

> **Analyze → write the plan and procedures → get explicit approval → only then
> edit code.**

A verbal description in the chat is **not** a plan. The plan must be a file in
the repository so it can be reviewed, diffed and referenced by the commit.

The agent must stop after presenting the plan and wait for an explicit approval
(“approved”, “go ahead”, “adelante”) or requested changes. Silence, a new
question, or a partial answer is not approval.

---

## 2. Which changes need a plan

| Change | Plan required |
| :--- | :---: |
| Python code (`core/`, `gui/`, `freehand_plugin.py`, `__init__.py`) | **Yes** |
| Tests and test doubles | **Yes** |
| UI behaviour, actions, tools, shortcuts, messages | **Yes** |
| `metadata.txt`, version, packaging, CI, build | **Yes** |
| Translation catalogs / master data that change UI text | **Yes** |
| Documentation, README, CHANGELOG, skills, workflows | No (but verify links) |
| Typo in a comment/docstring with no behaviour change | No (state it explicitly) |

If in doubt, write the plan. A short plan is cheaper than an unwanted change.

---

## 3. Plan file location and name

```
docs/maintainer/PLAN_<TOPIC>.md
```

Examples: `PLAN_RESHAPE.md`, `PLAN_OFFLINE_HELP.md`. The approved plan is a
project record; keep it after implementation and update its **Status** and
**Results** sections instead of deleting it.

---

## 4. Procedure

### Step 0 — Triage

State whether the request is code or documentation. If it is code, continue.
Announce explicitly: “I will not modify code until the plan is approved.”

### Step 1 — Analysis (read-only)

- Read the affected modules and tests; quote real paths and line ranges.
- Verify API claims in the target QGIS/PyQt version; record the version and the
  exact command or snippet used.
- Prototype only in an ephemeral location (for example a heredoc in `/tmp`);
  do **not** edit repository code.
- List constraints: QGIS 3.28–4.x, Qt5/Qt6, no runtime dependencies, Core/GUI
  boundary, i18n, packaging, backward compatibility.
- Identify risks and unknowns. If an API is missing, say so instead of assuming.

### Step 2 — Write the plan

Create `docs/maintainer/PLAN_<TOPIC>.md` with at least:

1. **Status** — `PROPOSED` until approved.
2. **Goal** — one paragraph.
3. **Scope / non-goals** — what will and will not be done.
4. **Current state** — code paths and behaviour today.
5. **API evidence** — verified signatures, versions and prototype results.
6. **UX / behaviour** — actions, selection, shortcuts, messages, failure modes.
7. **Design** — files to add/modify and the data flow.
8. **Tests** — unit/integration cases and the commands to run.
9. **i18n** — new strings, context `FreehandDigitize`, catalog updates.
10. **Versioning** — patch/minor/major decision and files to bump.
11. **Risks and mitigations**.
12. **Acceptance criteria** — observable and testable.
13. **Step-by-step implementation procedure** — ordered, small steps.
14. **Verification commands** — `make pre-release`, `make zip`, etc.
15. **Rollback** — how to revert safely.

### Step 3 — Review gate

Present the plan to the user with:

- the plan path;
- the 3–5 key decisions that need confirmation;
- the risks;
- an explicit question: “Do you approve this plan?”

Do not write code while waiting. If the user requests changes, update the plan
and ask again.

### Step 4 — Implementation

- Implement only the approved scope, in the planned order.
- Keep the plan open and mark steps as done; record deviations and why.
- Add/update tests in the same change as the code.
- If the scope or design changes materially, **stop**, update the plan and ask
  for approval again.

### Step 5 — Verification

Run the gates declared in the plan, at minimum:

```bash
make pre-release
make zip
make security-scan
make qt6-check      # when code or enums changed
```

`make pre-release` covers formatting, lint, docs links, i18n catalogs, flake8,
mypy, analyzer, agent validation, unit/integration tests and metadata.

### Step 6 — Close

- Update `CHANGELOG.md`, `README.md`/user guide and `docs/ARCHITECTURE_EN.md`
  when behaviour changes.
- Update `metadata.txt` version/changelog if the plan requires a release.
- Update `.agent-state/task.md`, `next_steps.md` and
  `docs/maintenance/DEVELOPMENT_LOG.md`.
- Mark the plan `IMPLEMENTED` with the commit hash and verification results.
- Commit with a Conventional Commit (`feat:`, `fix:`, `docs:`, `chore:`…).

---

## 5. Stop conditions

Stop and escalate to the user when:

- an API or file path in the plan does not exist;
- the implementation needs a scope change beyond the approved plan;
- tests fail after three attempts on the same root cause;
- the Core/GUI boundary or Qt5/Qt6 compatibility would be violated;
- the change requires a new runtime dependency;
- packaging or metadata validation cannot pass.

---

## 6. Plan template

```markdown
# Implementation Plan — <Topic>

> Status: PROPOSED | IMPLEMENTED | REJECTED
> Version: X.Y.Z | Date: YYYY-MM-DD

## 1. Goal
## 2. Scope and non-goals
## 3. Current state
## 4. API evidence
## 5. UX and behaviour
## 6. Design (files and data flow)
## 7. Tests
## 8. i18n
## 9. Versioning
## 10. Risks and mitigations
## 11. Acceptance criteria
## 12. Implementation procedure
## 13. Verification commands
## 14. Rollback
## 15. Approval
```

---

## 7. Example

The reshape feature plan is
[`PLAN_RESHAPE.md`](PLAN_RESHAPE.md). Revision 2 was approved for **v2.0.0** on
2026-11-19 and implemented.

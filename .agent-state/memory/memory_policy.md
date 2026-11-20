# Agent Memory Policy (Freehand Digitize)

> Defines what the agent remembers, when it forgets, and how conflicts are
> resolved. This is the authoritative document for the `.agent-state/` memory
> lifecycle.

## 1. Memory tiers

| Tier | File | Purpose | Retention |
| :--- | :--- | :--- | :--- |
| Working | `AI_CONTEXT.md` | Current session state and decisions | Reset each session |
| Episodic | `.agent-state/history/{tasks,next_steps,memory}/` | Session snapshots | `next_steps` 90 days; tasks/memory permanent |
| Semantic | `.agent-state/memory/AGENT_LESSONS.md`, `SKILL.md` files | Reusable patterns and preferences | Permanent, pruned |

## 2. What is worth remembering

Add a lesson when at least one is true:

- the agent made the same mistake more than once;
- the lesson prevents a class of errors not obvious from the code;
- it captures a user preference that affects future work;
- it documents a non-obvious QGIS API behavior or gotcha;
- it resolves a debated architectural decision.

Do **not** add a lesson that is already in the code, duplicates a `SKILL.md`,
or is specific to a one-off task.

## 3. When lessons are pruned

- Older than 90 days **and** already reflected in a `SKILL.md`: mark
  `[PRUNED]` in the index and remove the full entry.
- Contradicted by a newer lesson: keep the newer one, mark the older
  `[SUPERSEDED]`.
- No longer relevant: mark `[OBSOLETE]` and remove within 30 days.

Run `uv run python .agent/tools/forge.py memory prune` (dry run) and
`... memory prune --apply` when the active log approaches 350 lines.

## 4. Conflict resolution

1. Date wins: the newer lesson prevails.
2. Specificity wins: a lesson about a module overrides a general guideline.
3. Explicit user preference wins over agent-generated guidance.
4. Record the resolution with a `supersedes:` field.

## 5. Escalation path

```
Session observation → AGENT_LESSONS.md (raw lesson)
        ↓ (pattern repeats)
   Relevant SKILL.md (procedural knowledge)
        ↓ (applies globally)
   AGENTS.md constraint
```

## 6. Budget and compaction

- `AGENT_LESSONS.md` must stay **under 350 lines** of active content.
- When it exceeds the budget, run `forge.py memory prune`; if still over,
  consolidate the oldest lessons into the relevant `SKILL.md` and archive the
  full text under `.agent-state/history/memory/AGENT_LESSONS_YYYY-MM-DD_full.md`.
- `AI_CONTEXT.md` is reset at the start of every session and is never long-term
  storage.
- Keep the active lessons as one YAML block (`lessons:`) so the pruner can parse
  them.

## 7. Prohibited content

Never store secrets, credentials, tokens, PII, raw stack traces, more than five
lines of code, or content in a language other than English (the agentic system
is English-only; user-facing plugin strings stay Spanish).

## 8. Archive conventions

- Task boards: `.agent-state/history/tasks/tasks_vX.Y.Z.md` or
  `tasks_YYYY-MM-DD_topic.md`.
- `next_steps` snapshots: `.agent-state/history/next_steps/next_steps_YYYY-MM-DD_topic.md`;
  delete after 90 days (recoverable from git).
- Full lesson archives: `.agent-state/history/memory/AGENT_LESSONS_YYYY-MM-DD_full.md`
  (permanent).
- When archiving, fix relative links: a snapshot moved one level deeper needs an
  extra `../`.

## 9. Review schedule

| Review | Cadence | Owner | Trigger |
| :--- | :--- | :--- | :--- |
| Memory pruning | Monthly / at session close | Agent | `/close-session` |
| Skill promotion | On demand | Agent | Pattern repeats |
| Policy review | Biannually | Human | Framework upgrade |

---

*Created: 2026-11-19 — adapted from the SecInterp Gen 5 policy for Freehand
Digitize 2.0.0.*

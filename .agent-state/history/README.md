# Agent State History

Archives of closed sessions and previous working states. The active state lives
one level up (`task.md`, `next_steps.md`, `memory/`).

## Conventions

- `tasks/tasks_vX.Y.Z.md` — task board for a release.
- `tasks/tasks_YYYY-MM-DD_topic.md` — task board for a session without a
  release.
- `next_steps/next_steps_YYYY-MM-DD_topic.md` — handoff snapshots; prune after
  90 days (git keeps the history).
- `memory/AGENT_LESSONS_YYYY-MM-DD_full.md` — full lesson log before compaction;
  permanent.

When archiving, rewrite relative links for the new depth (one extra `../` per
level) so `forge validate` keeps passing.

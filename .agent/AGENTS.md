# Agentic Forge — Agent Configuration

Default agent configuration for the **Agentic Forge** framework: roles, skills
matrix, and workflows. A consuming project may use this as-is or provide its own
`AGENTS.md` at its repository root (opencode loads the project root file).

Paths below are relative to the framework root.

---

## 🧑‍💻 Agent Roles

- **@architect** — Senior Software Architect: protects clean architecture and
  designs solid features. Skills: [coding-standards](skills/coding-standards/SKILL.md),
  [documentation-standards](skills/documentation-standards/SKILL.md).
- **@qa_engineer** — QA & Automation: testing, CI, stability, zero-bug release.
  Skills: [commit-standards](skills/commit-standards/SKILL.md),
  [testing-standards](skills/testing-standards/SKILL.md).
- **@auditor** — Independent auditor: validates plans and standards compliance,
  hunts hallucinations. Skills: [agentic-memory](skills/agentic-memory/SKILL.md),
  [coding-standards](skills/coding-standards/SKILL.md).

---

## 🛠️ Skills

| Skill | Description |
| :--- | :--- |
| [agentic-memory](skills/agentic-memory/SKILL.md) | Lessons, patterns and preferences management |
| [changelog-generator](skills/changelog-generator/SKILL.md) | User-facing changelogs from git commits |
| [coding-standards](skills/coding-standards/SKILL.md) | pathlib, Google docstrings, strict typing |
| [commit-standards](skills/commit-standards/SKILL.md) | Conventional commits with quality validation |
| [documentation-standards](skills/documentation-standards/SKILL.md) | Technical logs and project history |
| [i18n-standards](skills/i18n-standards/SKILL.md) | Internationalization standards |
| [release-management](skills/release-management/SKILL.md) | Python package release process |
| [testing-standards](skills/testing-standards/SKILL.md) | Automated testing, CI/CD, and mocks |
| [qa-docker](skills/qa-docker/SKILL.md) | **Deprecated alias** for `testing-standards`; removed in the next major release |

> A project can add its own skills as an overlay under `.agent-state/skills/`.
> Domain-specific packs (e.g. QGIS) live under `scaffold/<domain>/` and are not
> part of the core skill set.

---

## 🔄 Workflows

| Command | Workflow | Purpose |
| :--- | :--- | :--- |
| `/start-session` | [start-session](workflows/start-session.md) | Start a session with context + skills |
| `/close-session` | [close-session](workflows/close-session.md) | Close a session, sync metrics, prune memory |
| `/start-phase` | [start-phase](workflows/start-phase.md) | Start a major development phase |
| `/close-phase` | [close-phase](workflows/close-phase.md) | Close a phase with metrics and retro |
| `/build-feature` | [build-feature](workflows/build-feature.md) | Autonomous feature pipeline |
| `/refactor-code` | [refactor-code](workflows/refactor-code.md) | Refactor with complexity validation |
| `/create-commit` | [create-commit](workflows/create-commit.md) | Commit with quality validation |
| `/run-tests` | [run-tests](workflows/run-tests.md) | Run unit tests reliably |
| `/fix-linting` | [fix-linting](workflows/fix-linting.md) | Auto-correct lint/format issues |
| `/i18n-maintenance` | [i18n-maintenance](workflows/i18n-maintenance.md) | Translation maintenance |
| `/ia-critic` | [ia-critic](workflows/ia-critic.md) | Critical review of implementation plans |
| `/verify-standards` | [verify-standards](workflows/verify-standards.md) | Audit agent-system consistency |
| `/release-package` | [release-package](workflows/release-package.md) | Python package release process |
| `/audit-package` | [audit-package](workflows/audit-package.md) | Self-audit of the project's code |

Full index: [workflows/index.md](workflows/index.md).

> QGIS-specific workflows (`/release-plugin`, `/audit-plugin`, `/run-tests-in-qgis`)
> live in `scaffold/qgis/workflows/`.

---

## 🧩 Paths & Configuration

- `forge.toml` (project root) declares `[forge].framework` and `[forge].state`.
- Framework content (this repo) mounts at the framework directory (e.g. `.agent/`).
- Project-owned state and overlay skills live under the state directory (e.g.
  `.agent-state/`), never in this repository.
- Tooling: `python tools/forge.py <validate|metrics|memory|lesson|project>`
  (`memory prune` is a dry-run; add `--apply` to mutate files; `project` runs the
  commands declared in `forge.toml`).

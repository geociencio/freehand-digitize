# Commit Guidelines

> Version 2.0.0 | Last Updated: 2026-11-19

This project follows the **Conventional Commits** specification for every commit.
The history must stay readable, reviewable and machine-parsable.

## Language rule

> [!IMPORTANT]
> All commit messages MUST be written in **English**.

## Format

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Use for |
| :--- | :--- |
| `feat` | A new user-visible capability (e.g. CTRL snapping). |
| `fix` | A user-visible bug fix (e.g. wrong CRS). |
| `refactor` | Code change that neither fixes a bug nor adds a feature. |
| `docs` | Documentation only. |
| `style` | Formatting/whitespace with no behaviour change. |
| `test` | Adding or correcting tests. |
| `perf` | Performance improvement. |
| `chore` | Build, tooling, state or auxiliary files. |
| `build` | Build system or dependencies (`pyproject.toml`, `uv.lock`). |
| `ci` | CI configuration and scripts. |

### Scopes

Use the module or area that changed:

`core`, `gui`, `plugin`, `tests`, `docs`, `agent`, `qa`, `release`, `ci`,
`deps`.

## Examples

```text
feat(gui): snap the first and last vertex with Ctrl
fix(core): clamp NaN tolerance to zero
refactor(gui): split feature creation into prepare/insert steps
test(integration): cover the cancelled attribute form
docs(maintainer): adapt the uv modernization guide
chore(agent): adapt the Agentic Forge state and workflows
ci: add the docs link check
```

## Rules

1. **Lowercase summary**: start the description with a lowercase letter.
2. **Imperative mood**: "add", not "added" or "adds".
3. **No trailing period** in the summary.
4. **Length**: keep the first line under ~50 characters when possible.
5. **Body**: explain *what* and *why* for non-trivial changes; wrap at ~72
   characters.
6. **One concern per commit**: code, docs and agentic state belong in separate
   commits when they can be reviewed independently.
7. **No secrets**: never commit credentials, tokens or local QGIS profiles.

## Integration with the toolchain

- The `conventional-pre-commit` hook enforces the message format on
  `commit-msg`.
- Run `make pre-release` before committing a feature or release.
- Ruff/format-only changes use `style`; behaviour-preserving QA changes use
  `refactor`; analyzer-driven cleanups also use `refactor`.
- Reference the affected docs when the change alters behaviour, e.g.:

  ```text
  feat(gui): restore Ctrl snapping for the last vertex

  The upstream plugin only snapped the first point. The tool now also snaps the
  release point when Ctrl is held, falling back to the free point when the QGIS
  snapping engine finds no match.
  ```

See [DOCS_STYLE_GUIDE.md](DOCS_STYLE_GUIDE.md) for documentation conventions and
[LOGGING_GUIDELINES.md](LOGGING_GUIDELINES.md) for the development log.

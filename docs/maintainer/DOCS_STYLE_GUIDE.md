# Documentation Style Guide

> Version 2.0.0 | Last Updated: 2026-11-19
>
> Adapted from the SecInterp documentation guide to the real Freehand Digitize
> structure (no Sphinx, no mirrors and no translation catalogs).

## Language

| Artifact | Language |
| :--- | :--- |
| Code, commits, `README.md`, `CHANGELOG.md`, user guide | **English** |
| API/architecture docs and maintainer guides | **English** |
| Internal plans, parity reports, session logs and the logging guidelines | **Spanish** |
| Plugin UI strings | **Spanish** source; English catalog shipped; more catalogs allowed |

User-facing documentation (README, CHANGELOG and the feature/user guide) is
English. Internal project records may stay in Spanish, but everything that is
shipped or published as documentation is English. Do not add `_EN` variants
unless a genuine bilingual pair is required; 2.0.0 has none.

## File naming and locations

- `lowercase_with_underscores.md`; one topic per file.
- Keep the tree shallow and canonical: no mirrors, no generated copies.

| Content | Location |
| :--- | :--- |
| User guide | `docs/user/USER_GUIDE.md` |
| Quick start | [`README.md`](../../README.md) |
| Architecture | `docs/ARCHITECTURE_EN.md` |
| Maintainer guides | `docs/maintainer/` |
| Session log (internal, Spanish) | `docs/maintenance/DEVELOPMENT_LOG.md` |

## Links

- Use relative Markdown links: `[text](relative/path.md)`.
- External links use the full URL.
- No wikilinks, no Sphinx/MyST-specific roles, no `help/html/` targets.
- Do not link to files that do not exist yet; mention future paths in backticks.
- `make docs-check` validates every relative link in `README.md`, `CHANGELOG.md`,
  `AGENTS.md`, `AI_CONTEXT.md` and `docs/**/*.md`.
- The agentic system has its own validator: `make agent-validate`.

## Headers and metadata

- Standalone docs start with:

  ```markdown
  > Version X.Y.Z | Last Updated: YYYY-MM-DD
  ```

- The version must match `metadata.txt`. Update both in the same change.
- Use a single `#` H1 per file and do not skip heading levels.

## Diagrams

- Mermaid is allowed in fenced ` ```mermaid ` blocks; keep diagrams small.
- ASCII diagrams are acceptable in code fences for data flow.

## Duplicates and generated files

- There is no `docs/source/` mirror and no Sphinx build in this repository.
- Never commit generated HTML or `help/html/`; the QGIS ZIP only ships the
  plugin runtime.
- `README.md` is a quick start; the long-form content belongs to
  `docs/user/USER_GUIDE.md`. Do not duplicate sections between them.

## Internationalization (docs)

- The 2.0.0 UI and docs catalogs do not exist; the analyzer `MISSING_I18N` rule
  is disabled by project decision.
- If i18n is reintroduced, translate only the user-facing pages and require
  **≥ 80 %** coverage before publishing a language. Code/API docs stay in
  English.

## Quality gates

```bash
make docs-check      # relative links in the Markdown tree
make agent-validate  # AGENTS.md + .agent/ + .agent-state/ links and metadata
make lint            # ruff on Python
```

`make docs-check` is part of `make pre-release` and CI. Fix broken links instead
of adding exclusions; only truly historical documents may be excluded in
`scripts/check_docs.py` with a comment explaining why.

## Commit style

Use Conventional Commits, e.g. `docs(maintainer): adapt the uv modernization
guide`. See [COMMIT_GUIDELINES.md](COMMIT_GUIDELINES.md).

## Checklist

- [ ] File name and location follow the table above.
- [ ] Version/date header present and matching `metadata.txt`.
- [ ] Relative links resolve (`make docs-check`).
- [ ] README, CHANGELOG and the user guide are in English.
- [ ] Internal plans/logs are the only Spanish documents.
- [ ] No generated files, no duplicated content, no future-file links.

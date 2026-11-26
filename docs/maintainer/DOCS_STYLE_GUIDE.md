# Documentation Style Guide

> Version 2.0.2 | Last Updated: 2026-11-25
>
> Adapted from the SecInterp guide to the Freehand Digitize structure. Keep the
> principles; do not copy SecInterp's Sphinx, mirrors or documentation catalogs.

## Language

| Artifact | Language |
| :--- | :--- |
| Code, commits, `README.md`, `CHANGELOG.md`, user guide | **English** |
| API/architecture docs and maintainer guides | **English** |
| Internal plans, parity reports, session logs and logging guidelines | **Spanish** |
| Plugin UI strings | **English** source; `es`, `pt_BR`, `fr`, `de`, `it`, `id` catalogs shipped |

User-facing documentation is English. Internal project records may stay in
Spanish. There are no `_EN.md` pairs; the canonical English file is the only
file.

## File naming and locations

- `lowercase_with_underscores.md`; one topic per file.
- Keep the tree shallow and canonical: no mirrors, no generated copies.

| Content | Location |
| :--- | :--- |
| Documentation index | `docs/README.md` |
| User guide | `docs/user/USER_GUIDE.md` |
| Quick start | [`README.md`](../../README.md) |
| Architecture | `docs/ARCHITECTURE_EN.md` |
| Maintainer guides and plans | `docs/maintainer/` |
| Release notes | `docs/releases/notes/vX.Y.Z.md` |
| Session log (internal, Spanish) | `docs/maintenance/DEVELOPMENT_LOG.md` |

## Links

- Use relative Markdown links: `[text](relative/path.md)`.
- External links use the full URL.
- No wikilinks, no Sphinx/MyST roles, no `help/html/` targets.
- Do not link to files that do not exist yet; mention future paths in backticks.
- `make docs-check` validates every relative link in `README.md`, `CHANGELOG.md`,
  `AGENTS.md`, `AI_CONTEXT.md` and `docs/**/*.md`.
- `make agent-validate` validates the agentic system separately.

## Headers and metadata

- Active standalone docs start with:

  ```markdown
  > Version X.Y.Z | Last Updated: YYYY-MM-DD
  ```

- The version must match `metadata.txt`; update both in the same change.
- Historical plans and session logs keep their original version/date.
- Use a single `#` H1 per file and do not skip heading levels.

## Diagrams and content

- Mermaid is allowed in fenced ` ```mermaid ` blocks; keep diagrams small.
- ASCII diagrams are acceptable in code fences for data flow.
- The README is a quick start; long-form content belongs in the user guide.
- Do not duplicate sections between README, user guide and architecture.

## Duplicates and generated files

- There is no `docs/source/` mirror and no Sphinx build in this repository.
- Never commit generated HTML or `help/html/`; the QGIS ZIP only ships plugin
  runtime files.
- `tests/`, `docs/`, `.agent/` and `.agent-state/` stay out of the ZIP.

## Internationalization

- The plugin UI source language is **English**.
- The six catalogs are `es`, `pt_BR`, `fr`, `de`, `it`, `id`; edit the JSON
  master data, not the `.ts`/`.qm` files.
- There are no documentation catalogs. Do not add doc `.po` files or
  SecInterp-style `docs-i18n` unless the project explicitly adopts them.
- Use the [`i18n guide`](../../scripts/i18n/README.md) for the UI workflow.

## Release notes

- Every release has `docs/releases/notes/vX.Y.Z.md`.
- Use `make release-notes-check`; do not publish a release with placeholders.
- GitHub Releases use `--notes-file`; do not pass inline `--notes`.

## Quality gates

```bash
make docs-check           # relative links in the Markdown tree
make release-notes-check  # versioned release note
make agent-validate       # AGENTS.md + .agent/ + .agent-state/ links
make lint                 # ruff on Python
```

`make docs-check` and `make release-notes-check` are part of `make pre-release`.
Fix broken links instead of adding exclusions; only truly historical documents
may be excluded in `scripts/check_docs.py` with a comment.

## Commit style

Use Conventional Commits, e.g. `docs(maintainer): adapt the uv modernization
guide`. See [COMMIT_GUIDELINES.md](COMMIT_GUIDELINES.md).

## Checklist

- [ ] File name and location follow the table above.
- [ ] Version/date header present and matching `metadata.txt` (active docs only).
- [ ] Relative links resolve (`make docs-check`).
- [ ] README, CHANGELOG and the user guide are in English.
- [ ] Internal plans/logs are the only Spanish documents.
- [ ] Release note exists and passes `make release-notes-check`.
- [ ] No generated files, no duplicated content, no future-file links.

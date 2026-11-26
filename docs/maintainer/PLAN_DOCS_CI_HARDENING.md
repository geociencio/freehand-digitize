# Implementation Plan — Documentation, CI and QGIS Packaging Hardening

> **Status: IMPLEMENTED (2026-11-25)** — docs, CI and packaging updated;
> plugin version unchanged (**2.0.2**).
>
> Type: docs/CI/packaging | Plugin version: unchanged (**2.0.2**)
> Date: 2026-11-22 | Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Context

The attached `DOCS_STYLE_GUIDE.md` is the **SecInterp** guide (Sphinx, MyST,
`docs/source/`, vault mirrors, 13 doc languages, `docs-i18n`). Freehand has a
smaller, already-adapted guide, but it is stale:

- header says Version 2.0.0 and 2026-11-19;
- says “no translation catalogs” and “2.0.0 has none”, but six UI catalogs exist;
- does not mention `docs/releases/notes/`, `release-notes-check` or the stable
  QGIS runner;
- some active docs still say Version 2.0.0 while the plugin is 2.0.2.

The repository also lacks a docs index, contribution/security/support files,
issue/PR templates, pinned GitHub Actions and a few QGIS packaging practices.

Relevant external guidance:

- QGIS plugin publish requirements: <https://plugins.qgis.org/docs/publish>
- QGIS Cookbook, plugin structure/translation: <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html>
- QGIS Cookbook, releasing: <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/releasing.html>
- GitHub Actions secure use: <https://docs.github.com/en/actions/reference/security/secure-use>
- Keep a Changelog 1.1.0: <https://keepachangelog.com/en/1.1.0/>
- Diátaxis: <https://diataxis.fr/>
- OpenSSF Scorecard: <https://github.com/ossf/scorecard>

---

## 2. Scope

### A. Adapt the docs style guide (do not copy SecInterp)

Keep from SecInterp:

- one canonical source, no mirrors;
- one topic per file;
- relative Markdown links;
- version/date headers on active docs;
- historical documents are not rewritten;
- `docs-check` as a blocking gate;
- Conventional Commits.

Do **not** add:

- Sphinx/MyST, `docs/source/`, `docs-version`;
- vault mirrors or `sync_*_mirrors` scripts;
- `_EN.md` pairs;
- doc `.po` catalogs, `docs-i18n` or 13-language coverage.

Update [DOCS_STYLE_GUIDE.md](DOCS_STYLE_GUIDE.md):

- Version 2.0.2 / 2026-11-22.
- English UI source + six catalogs.
- `docs/releases/notes/vX.Y.Z.md` and `make release-notes-check`.
- `tests/run_integration.py` and `make test-qgis`.
- `docs/README.md` as the index.
- Active vs historical docs and version-header policy.

### B. Docs index and repository files

Add:

```text
docs/README.md
CONTRIBUTING.md
SECURITY.md
SUPPORT.md
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/feature_request.yml
.github/PULL_REQUEST_TEMPLATE.md
```

`docs/README.md` uses Diátaxis categories:

- **Tutorial/quick start**: README.
- **How-to**: user guide, sampling, difference, reshape.
- **Reference**: metadata, architecture, i18n, release notes.
- **Explanation**: architecture decisions, parity, plans/history.

`CONTRIBUTING.md` links to `AGENTS.md`, `CHANGE_PROCEDURE.md`, test commands,
commit rules and release notes.

`SECURITY.md` gives a private reporting path and scope (no secrets in issues).
`SUPPORT.md` lists QGIS version, OS, plugin version and log location.

### C. CI hardening

Update `.github/workflows/test.yml`:

1. Top-level `permissions: contents: read`.
2. Per-job least privilege (no write scopes).
3. Pin actions to full commit SHA (`actions/checkout`,
   `astral-sh/setup-uv`, `actions/upload-artifact`), with Dependabot updates.
4. `persist-credentials: false` on checkout (no push in CI).
5. `concurrency` with `cancel-in-progress: true`.
6. `timeout-minutes` per job.
7. Add `make release-notes-check` to the quality job.
8. Add `workflow_dispatch`.
9. Optional: `dependency-review-action` on PRs (no runtime deps, but dev stack).
10. Optional: OpenSSF Scorecard workflow.

No test-runner change: `tests/run_integration.py` is already stable.

### D. QGIS packaging and metadata

- **Distribute `.ts` catalogs** alongside `.qm`. QGIS Cookbook says the `.ts`
  files should be distributed; the current ZIP ships only `.qm`. Adjust
  `.qgisignore`/packaging and validate the ZIP size.
- Add `category=Vector` to `metadata.txt` if the plugin is presented in the
  Vector menu; keep the current toolbar/Plugins menu behavior otherwise.
- Add a minimal sample dataset under `examples/` (GeoJSON line/polygon and a
  short README), excluded from the ZIP.
- Verify the plugin on **QGIS 3.28** (oldest declared) via a container/tag spike;
  if no reliable 3.28 image exists, raise `qgisMinimumVersion` to the oldest
  tested version instead of claiming untested support.
- Keep `qgisMaximumVersion=4.99`, no `supportsQt6`.

### E. Changelog and release notes

Align `CHANGELOG.md` with Keep a Changelog:

```markdown
## [Unreleased]
## [2.0.2] - 2026-11-21
```

- ISO dates.
- Link versions to tags/compare URLs.
- Keep `Unreleased` only for genuinely unreleased changes.
- Keep `docs/releases/notes/vX.Y.Z.md` as the GitHub body; do not duplicate the
  full text in `CHANGELOG.md`.

`v2.1.0.md` is not created until the 2.1.0 release gate opens.

---

## 3. Tests and validation

- No new plugin runtime tests required in this plan.
- `make docs-check`, `make release-notes-check`, `make agent-validate` pass.
- Add a small unit test for the docs index/link set only if a new script is
  introduced; otherwise rely on `docs-check`.
- CI YAML lint (actionlint) if available.
- `make pre-release`, `make zip`, `make portal-check`, `make security-scan`,
  `make qt6-check`.
- Verify the ZIP includes the six `.ts` + `.qm` catalogs and excludes `docs/`,
  tests, agent state and sample data.

Expected plugin test count stays **150**; docs/tooling changes do not alter the
runtime suite.

---

## 4. Versioning and release

- No plugin version bump for docs/CI alone.
- `category`/`.ts`/sample changes are included in the next release (2.1.0).
- Release remains gated: 2.0.1 approval → 2.0.2 portal upload/approval → 2.1.0.
- No tag, ZIP or portal upload during this plan.

---

## 5. Risks

| Risk | Mitigation |
| :--- | :--- |
| Copying SecInterp’s Sphinx/mirror/doc-i18n complexity | Explicit “do not add” list; Freehand has no Sphinx. |
| CI breaks after pinning actions | Pin exact SHAs and test a PR run before merging. |
| `.ts` in ZIP increases size or portal rejection | Validate `qgis-manage` ZIP; 25 MB limit; `.ts` are small text files. |
| QGIS 3.28 image unavailable | Spike first; otherwise raise minimum to the tested version. |
| Docs index duplicates content | Index links only; canonical content stays in existing pages. |
| Security/Contribution files become stale | Link to `AGENTS.md`/`CHANGE_PROCEDURE.md`; review at release. |
| Version headers drift again | Update style guide and active docs; keep historical plans untouched. |

---

## 6. Acceptance criteria

- [ ] `DOCS_STYLE_GUIDE.md` matches 2.0.2, six catalogs and release notes.
- [ ] `docs/README.md` indexes user, maintainer, release and history docs.
- [ ] `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, issue/PR templates exist.
- [ ] CI has `permissions`, pinned actions, concurrency/timeouts and
      `release-notes-check`.
- [ ] `.ts` catalogs are in the ZIP; sample data is not.
- [ ] QGIS 3.28 is tested or `qgisMinimumVersion` is corrected.
- [ ] `CHANGELOG.md` follows Keep a Changelog and links versions.
- [ ] All gates pass; no runtime version bump.
- [ ] No tag/release/portal upload in this plan.

---

## 7. Procedure

1. Update the style guide and active doc headers.
2. Add the docs index and repository files/templates.
3. Harden CI and add `release-notes-check`.
4. Update `.qgisignore`/packaging for `.ts`; add sample data.
5. Run the QGIS 3.28 spike and decide min version.
6. Normalize `CHANGELOG.md`.
7. Run gates and `make zip`/`portal-check`; inspect the ZIP.
8. Update the plan with results and commit.

---

## 8. Results

- `DOCS_STYLE_GUIDE.md` updated to 2.0.2, six catalogs and release notes.
- Added `docs/README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`,
  issue templates and a PR template.
- CI: `permissions: contents: read`, pinned actions, `concurrency`,
  timeouts, `persist-credentials: false`, `release-notes-check` and a real
  **QGIS 3.28** integration job.
- QGIS 3.28: **93/93 integration tests pass** in `qgis/qgis:release-3_28`;
  `qgisMinimumVersion=3.28` is now verified.
- Packaging: `.ts` catalogs are included, `examples/` is excluded; a temporary
  `qgis-manage package --repo-check` passed.
- Added `examples/sample_freehand.geojson` and README.
- `CHANGELOG.md` uses Keep a Changelog headings and compare links.
- Tests remain **157** (64 unit + 93 integration); no runtime version bump.
- **Commit:** `2f6d7b9 fix: keep QGIS 4 enum compatibility in the 3.28 fallback`
  (on top of `5f6044d chore: harden docs, CI and packaging`).

---

## 9. Approval

The plan is **PROPOSED**. Implementation starts only after approval.

1. Adapt the guide’s principles only; no Sphinx/mirrors/doc-i18n.
2. Add docs index, contribution/security/support files and templates.
3. Harden CI with least privilege, pinned actions and the release-note gate.
4. Ship `.ts` catalogs, sample data, `category=Vector`; verify QGIS 3.28.
5. Align the changelog; keep the 2.1.0 release gate.

Do you approve this plan?

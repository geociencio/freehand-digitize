# Implementation Plan — English as the i18n Base

> **Status: IMPLEMENTED (2026-11-22), UNRELEASED** — English source and six
> catalogs are in the working tree. Version stays **2.0.2**; no tag or portal
> upload until 2.0.2 is public in the portal.
>
> Type: i18n refactor | Target version: **2.1.0 (release gated)** | Date: 2026-11-22
> Revision 2: includes the `pt_BR`, `fr`, `de`, `it` and `id` catalogs in the
> same change. Revision 3 corrects the portal sequence: 2.0.1 is pending in the
> portal and 2.0.2 is GitHub-only, so 2.1.0 is **not tagged or published** until
> 2.0.x is resolved in the portal.
> Procedure: [CHANGE_PROCEDURE.md](CHANGE_PROCEDURE.md)

---

## 1. Current state

- Source strings are **Spanish** in `gui/texts.py`, `gui/feature_creator.py`,
  `gui/freehand_tool.py` and `freehand_plugin.py`.
- The English catalog (`i18n/freehand_digitize_en.ts/.qm`) is a full translation
  of the Spanish source.
- `scripts/i18n/master_data/en.json` maps every Spanish source to English.
- `gui/i18n.py` loads the catalog matching the QGIS locale; Spanish users see the
  source strings without a catalog.
- `tests/test_i18n_catalogs.py` and `tests/integration/test_i18n.py` assert the
  English catalog and Spanish source fallback.
- Counts: **113** `QCoreApplication.translate` calls, **49** catalog messages,
  **43** text helper functions.

This is inverted from the usual QGIS convention (English source + translated
catalogs) and makes every new language depend on Spanish.

---

## 2. Goal

Make **English the source language** and ship **six catalogs** without changing
the visible Spanish wording or plugin behaviour:

| Locale | Catalog | Status |
| :--- | :--- | :--- |
| English | source | fallback; no catalog |
| Spanish | `es` | exact current Spanish wording |
| Portuguese (Brazil) | `pt_BR` | new |
| French | `fr` | new |
| German | `de` | new |
| Italian | `it` | new |
| Indonesian | `id` | new |

After the change:

- English source strings are the code literals.
- `i18n/freehand_digitize_es.ts/.qm` translates English to Spanish.
- The five new catalogs translate English to `pt_BR`, `fr`, `de`, `it` and `id`.
- No English catalog is needed; English is the fallback.
- The existing English translations become the new source, reviewed once.
- The existing Spanish literals become the Spanish translations, preserving the
  current wording exactly.
- The new catalogs are drafted with a shared glossary and reviewed before
  release; no half-translated catalog is shipped.

---

## 3. Design

### Source strings

Replace every Spanish literal inside `QCoreApplication.translate` with its
English equivalent. The mapping comes from the current
`i18n/freehand_digitize_en.ts`:

```text
"Dibujo a mano alzada"        -> "Freehand digitize"
"Reformar geometría"          -> "Reshape feature"
"El trazo no cruza ninguna entidad." -> "The stroke does not cross any feature."
```

All call sites keep the literal context `"FreehandDigitize"` so `pylupdate6`
still extracts them.

### Catalogs

- Remove `i18n/freehand_digitize_en.ts/.qm` (English is now source).
- Generate one `.ts` per locale from the English source:
  `es`, `pt_BR`, `fr`, `de`, `it`, `id`.
- Create `master_data/<locale>.json` mapping **English source -> translation**:
  - `es.json`: the exact current Spanish literals (lossless);
  - `pt_BR/fr/de/it/id.json`: reviewed translations.
- Compile one `.qm` per locale.

The English catalog messages are the translation source; no Spanish source text
remains in code.

### Loader

`gui/i18n.py` logic stays the same: read `locale/userLocale`, try full locale then
two-letter code, load the first `.qm`, install it. Only behaviour changes:

- `es_ES` / `es` loads the Spanish catalog.
- `en_US` / `en` gets the English source (no catalog).
- Any unknown locale falls back to English.

Update the module docstring.

### Tooling

- `Makefile`: `LOCALES = es pt_BR fr de it id`.
- `scripts/i18n/README.md`: source language English; six catalogs; master data
  layout; glossary; update the language-priority table.
- `scripts/i18n/update_metadata_languages.py`: `BASE_LANGUAGE = "English"` and a
  deterministic locale order (`es`, `pt_BR`, `fr`, `de`, `it`, `id`), then extras.
- `metadata.txt`:
  - `general_description=Supported languages: English, Spanish, Portuguese
    (Brazil), French, German, Italian, Indonesian`.
  - `about`: “UI available in English (source language), Spanish, Portuguese
    (Brazil), French, German, Italian and Indonesian”.
- `CHANGELOG.md`: 2.1.0 entry with the six catalogs.

### Tests

- `tests/test_i18n_catalogs.py`:
  - `LOCALES = ["es", "pt_BR", "fr", "de", "it", "id"]`.
  - All catalogs complete, no empty/unfinished entries, placeholders preserved.
  - Required key strings checked per locale (English source -> translated).
  - Compiled `.qm` non-empty per locale.
- `tests/integration/test_i18n.py`:
  - Load each catalog and translate a key string.
  - `es_ES` loads `es.qm` and preserves the current Spanish wording.
  - `pt_BR` loads `pt_BR.qm`; `pt` fallback still works.
  - `en_US` installs nothing and returns the English source.
  - Unknown locale falls back to English.
- Audit all integration assertions that compare user-facing messages; most only
  check that a warning was emitted, but any exact Spanish assertion must switch
  to English.
- `tests/test_metadata.py`: version 2.1.0; language description lists all six.

Expected suite: **~146 tests** (57 unit + 89 integration); the i18n tests are
parameterized and the exact count is recorded after implementation.

---

## 4. Migration procedure

1. Freeze a mapping `Spanish source -> English source` from `en.ts`.
2. Review the English text once for consistency (capitalisation, quotes,
   placeholders) and build a small glossary (layer, feature, edit session,
   tolerance, reshape, difference, sampling, undo).
3. Replace the Spanish literals in the four source modules with English.
4. Generate the six `.ts` files with `pylupdate6`.
5. Build `master_data/es.json` as `English source -> old Spanish literal`.
6. Draft `pt_BR/fr/de/it/id.json` from the English source using the glossary;
   review all 245 strings, especially action names, warnings and placeholders.
7. Run `make transup` (applies every master file), `make transcompile`,
   `make i18n-check`.
8. Rewrite/verify the i18n tests and audit exact message assertions.
9. Update metadata, CHANGELOG, README/AGENTS and i18n docs.
10. Run `make pre-release`, `make docker-test`, `make zip`, `make security-scan`,
    `make qt6-check`.
11. Deploy to QGIS 4 and smoke-test English, Spanish and one new locale.

The old `en.ts` and `en.json` are removed; Git history preserves them.

### Translation quality

- No machine-only catalog is shipped silently.
- The Spanish catalog is exact; the other five are drafted and reviewed.
- `make i18n-check` rejects empty, unfinished or placeholder-broken strings.
- If a locale cannot be completed, it is dropped from the release rather than
  shipped half-translated.

---

## 5. Versioning and release gate

**2.1.0** (minor, release blocked):

- No plugin API or behaviour change; the visible strings are the same.
- It is a structural i18n change and the base for adding more languages.

### Current portal reality

| Version | GitHub | Portal |
| :--- | :--- | :--- |
| 2.0.1 | published | **uploaded; approval pending** |
| 2.0.2 | published | **not uploaded** |
| 2.1.0 | not created | not uploaded |

### Release gate

1. Wait for **2.0.1 portal approval**.
2. Upload **2.0.2** to the portal (or handle a 2.0.1 block first).
3. Wait for **2.0.2 portal approval**.
4. Only then tag and upload **2.1.0**.

While the portal is unresolved:

- do not create the `v2.1.0` tag;
- do not upload 2.1.0;
- implementation may proceed on the working tree, but the version bump and
  release metadata stay at 2.0.2 until the gate opens.

If the user prefers not to develop ahead of the portal, implementation waits
until 2.0.2 is public.

---

## 6. Risks and mitigations

| Risk | Mitigation |
| :--- | :--- |
| Losing natural Spanish | Spanish catalog values are the exact current literals, not retranslations. |
| Missing/incorrect English | Review the existing `en.ts` translations before promoting them; compare every source. |
| Placeholder/format errors | `make i18n-check` enforces `{name}`, `{error}`, `{count}` parity. |
| Multiline strings | Replace literals with AST/manual review; `pylupdate6` extraction confirms coverage. |
| Tests coupled to Spanish | Audit exact assertions; switch to English source. |
| Catalog fallback regression | Test `es_ES`, `es`, `en_US`, `en` and an unknown locale. |
| Portal version pile-up | Keep 2.1.0 on GitHub until 2.0.x portal is resolved. |
| Five new translations increase review load | Shared glossary; review all 245 strings; drop any incomplete locale instead of shipping it. |
| Locale codes differ (`pt_BR` vs `pt`) | Test full-locale and two-letter fallback; use Qt codes. |
| Metadata source language stale | `update_metadata_languages.py` base becomes English; test asserts the line. |

---

## 7. Acceptance criteria

- [ ] All source literals are English; no Spanish source remains in code.
- [ ] `es.qm` reproduces the current Spanish UI exactly (spot-check all key
      strings and warnings).
- [ ] `en_US` uses source English; `es_ES` uses Spanish; `pt_BR`, `fr`, `de`,
      `it` and `id` load their catalogs; unknown locales fall back to English.
- [ ] `make i18n-check` passes with six catalogs.
- [ ] ~146 tests pass in QGIS 4.2.2 and the Qt5 container.
- [ ] `make pre-release`, `make zip`, security and Qt6 checks pass.
- [ ] Metadata advertises English (source) and the six catalogs.
- [ ] CI green with the gate active.
- [ ] 2.1.0 is not tagged or uploaded before 2.0.2 is public in the portal.

---

## 8. Out of scope

- Additional languages beyond `pt_BR`, `fr`, `de`, `it`, `id` (separate
  follow-up after this batch).
- Changing user-facing wording or adding features.
- Portal upload of 2.1.0 before the 2.0.x status is known.

---

## 9. Results

- English is the source language; all 49 messages are English literals.
- Catalogs generated and compiled: `es`, `pt_BR`, `fr`, `de`, `it`, `id`.
- Spanish catalog preserves the previous wording exactly from the old `en.ts`
  translations.
- 245 new translations reviewed for placeholders and terminology.
- Tests: **146** (57 unit + 89 integration incl. gate); `make test-qgis` 89 OK;
  `make docker-test` 89 OK; `make pre-release` OK.
- Version stays **2.0.2**; no tag, release or portal upload.
- **Commit:** `1cf3165 feat(i18n): make English the source language`.

---

## 10. Approval

The plan is **PROPOSED**. Implementation starts only after the user approves:

1. English as source + `es`, `pt_BR`, `fr`, `de`, `it` and `id` catalogs.
2. Reuse the current English catalog as the new source.
3. Keep the Spanish wording identical to the current UI.
4. Ship the five new catalogs in the same change, with reviewed translations.
5. **Do not tag or publish 2.1.0 until 2.0.2 is public in the portal.**

Do you approve this revision 3, and should implementation start now or wait until
2.0.2 is public in the portal?

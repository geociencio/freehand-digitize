# Implementation Plan — English as the i18n Base

> **Status: PROPOSED** — no code changes until the user approves this plan.
>
> Type: i18n refactor | Target version: **2.1.0** | Date: 2026-11-22
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

Make **English the source language** and treat **Spanish as a shipped catalog**,
without changing the visible Spanish wording or plugin behaviour.

After the change:

- English source strings are the code literals.
- `i18n/freehand_digitize_es.ts/.qm` translates English to Spanish.
- No English catalog is needed; English is the fallback.
- The existing English translations become the new source, reviewed once.
- The existing Spanish literals become the Spanish translations, preserving the
  current wording exactly.

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
- Generate `i18n/freehand_digitize_es.ts` from the English source.
- Create `scripts/i18n/master_data/es.json` mapping **English source -> current
  Spanish text**.
- Compile `i18n/freehand_digitize_es.qm`.

This is a lossless inversion: the Spanish catalog values are the exact strings
currently used in production, not machine translations.

### Loader

`gui/i18n.py` logic stays the same: read `locale/userLocale`, try full locale then
two-letter code, load the first `.qm`, install it. Only behaviour changes:

- `es_ES` / `es` loads the Spanish catalog.
- `en_US` / `en` gets the English source (no catalog).
- Any unknown locale falls back to English.

Update the module docstring.

### Tooling

- `Makefile`: `LOCALES = es`.
- `scripts/i18n/README.md`: source language English; Spanish catalog; master data
  `es.json`; update the language-priority table (English base).
- `scripts/i18n/update_metadata_languages.py`: `BASE_LANGUAGE = "English"`.
- `metadata.txt`:
  - `general_description=Supported languages: English, Spanish`.
  - `about`: “UI available in English (source language) and Spanish”.
- `CHANGELOG.md`: 2.1.0 entry.

### Tests

- `tests/test_i18n_catalogs.py`:
  - `LOCALES = ["es"]`.
  - Required key strings use English sources and Spanish translations.
  - Placeholder and completeness checks unchanged.
- `tests/integration/test_i18n.py`:
  - `test_catalog_translates_ui_string`: load `es.qm`, translate the English
    source `"Freehand digitize"` to `"Dibujo a mano alzada"`.
  - `test_install_translations_for_spanish_locale`: `es_ES` loads the catalog and
    translates `"Freehand Digitize: add feature"` to the Spanish text.
  - `test_english_locale_uses_source_strings`: `en_US` installs nothing and
    returns the English source.
- Audit all integration assertions that compare user-facing messages; most only
  check that a warning was emitted, but any exact Spanish assertion must switch
  to English.
- `tests/test_metadata.py`: version 2.1.0; language description.

Expected suite: **145 tests** (57 unit + 88 integration), same count; i18n tests
are rewritten, not added.

---

## 4. Migration procedure

1. Freeze a mapping `Spanish source -> English source` from `en.ts`.
2. Review the English text once for consistency (capitalisation, quotes,
   placeholders).
3. Replace the Spanish literals in the four source modules with English.
4. Generate `freehand_digitize_es.ts` with `pylupdate6`.
5. Build `master_data/es.json` as `English source -> old Spanish literal`.
6. Run `make transup` (applies `es.json`), `make transcompile`,
   `make i18n-check`.
7. Rewrite/verify the i18n tests.
8. Update metadata, CHANGELOG, README/AGENTS and i18n docs.
9. Run `make pre-release`, `make docker-test`, `make zip`, `make security-scan`,
   `make qt6-check`.
10. Deploy to QGIS 4 and smoke-test English and Spanish UI.

The old `en.ts` and `en.json` are removed; Git history preserves them.

---

## 5. Versioning and release

**2.1.0** (minor):

- No plugin API or behaviour change; the visible strings are the same.
- It is a structural i18n change and the base for adding `pt_BR`, `fr`, `de`, etc.
- Tag/GitHub Release `v2.1.0`; deploy locally.
- **Portal sequencing:** 2.0.1 is pending and 2.0.2 is already on GitHub. Do not
  upload 2.1.0 until the 2.0.x portal status is known; if the portal accepts one
  current upload, prefer the newest stable after 2.0.1 is resolved.

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
| Metadata source language stale | `update_metadata_languages.py` base becomes English; test asserts the line. |

---

## 7. Acceptance criteria

- [ ] All source literals are English; no Spanish source remains in code.
- [ ] `es.qm` reproduces the current Spanish UI exactly (spot-check all key
      strings and warnings).
- [ ] `en_US` uses source English; `es_ES` uses the Spanish catalog; unknown
      locales fall back to English.
- [ ] `make i18n-check` passes with `LOCALES=["es"]`.
- [ ] 145 tests pass in QGIS 4.2.2 and the Qt5 container.
- [ ] `make pre-release`, `make zip`, security and Qt6 checks pass.
- [ ] Metadata advertises English (source) and Spanish.
- [ ] CI green with the gate active.

---

## 8. Out of scope

- Adding `pt_BR`, `fr`, `de`, `it`, `id` catalogs (separate follow-up, after the
  base is stable).
- Changing user-facing wording or adding features.
- Portal upload of 2.1.0 before the 2.0.x status is known.

---

## 9. Approval

The plan is **PROPOSED**. Implementation starts only after the user approves:

1. English as source + Spanish as the only catalog, version **2.1.0**.
2. Reuse the current English catalog as the new source (recommended) rather than
   rewriting the English from scratch.
3. Keep the Spanish wording identical to the current UI.

Do you approve this plan?

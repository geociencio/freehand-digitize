# Freehand Digitize i18n

Adapted from the SecInterp translation system to a much smaller catalog. The
same principles apply: Qt `.ts` catalogs generated from source, translations
kept in JSON master data, compiled `.qm` files shipped with the plugin, and a
quality gate that rejects unfinished or broken entries.

## Architecture

- **Source language: Spanish.** The plugin UI strings are Spanish literals.
- **English catalog:** `i18n/freehand_digitize_en.ts` / `.qm`.
- **Master data:** `scripts/i18n/master_data/en.json` maps every Spanish source
  string to its English translation. It is the single source of truth for
  translations; do not edit `.ts` by hand.
- **Loader:** `gui/i18n.py` reads `locale/userLocale` from QGIS settings, tries
  the full locale (`en_US`, `pt_BR`) and then the language (`en`, `pt`), loads
  the first `.qm` found and installs it.
- **Fallback:** if no catalog matches (for example `es_ES`), the Spanish source
  strings are shown unchanged.

The SecInterp system also injects a translator into core classes and auto-
translates missing strings through an external API. Neither part is needed
here: `core/` has no user-facing strings and the English catalog is maintained
by hand.

## Workflow

```bash
# 1. Extract new strings and apply the English master data
make transup

# 2. Compile the .ts catalogs into .qm
make transcompile

# 3. Quality gate
make i18n-check

# Clean compiled catalogs (regenerate with transcompile)
make transclean
```

`make transup` runs `pylupdate6` over the plugin sources, applies
`scripts/i18n/apply_full.py`, and refreshes the `general_description` line in
`metadata.txt` with `scripts/i18n/update_metadata_languages.py`.

## Golden rules

- A user-facing literal must be inside
  `QCoreApplication.translate("FreehandDigitize", "...")` with a **literal**
  context; `pylupdate6` does not extract a variable context.
- Keep `{placeholders}` identical in source and translation.
- Never edit `.qm` files; they are compiled binaries.
- Never edit `.ts` directly: `make transup` regenerates it and injects the JSON.
- JSON keys are the exact source strings (including `\n`); values are the
  English translations.
- Add a new language by creating `i18n/freehand_digitize_<code>.ts` with
  `pylupdate6`, `master_data/<code>.json`, then run `make transup`,
  `make transcompile` and `make i18n-check`.

## Language priority

Based on the QGIS 3.40 translation statistics (last update 2026-03-12,
<https://docs.qgis.org/3.40/en/docs/about/translation_stats.html>) and the
languages already supported by SecInterp, the recommended order after English is:

| Priority | Locale | QGIS translation ratio | Notes |
| :---: | :--- | :---: | :--- |
| 1 | `en` | source | Universal; required for the portal. |
| 2 | `fr` | 83.48 % | Large QGIS community. |
| 3 | `de` | 60.22 % | Large QGIS community. |
| 4 | `it` | 99.96 % | Very complete QGIS translation. |
| 5 | `pt_BR` | 62.02 % | Large QGIS community. |
| 6 | `nl` | 100.00 % | Complete QGIS translation. |
| 7 | `ja` | 97.68 % | Complete QGIS translation. |
| 8 | `ko` | 94.62 % | Complete QGIS translation. |
| 9 | `sv` | 99.99 % | Complete, smaller user base. |
| 10 | `zh_CN` | 28.68 % | Large user base despite lower coverage. |
| 11 | `ru` | 27.51 % | Large user base despite lower coverage. |
| 12 | `pl` | 13.14 % | Lower QGIS coverage. |

Spanish is the source language, so it does not need a catalog. Avoid adding
many catalogs at once: every new locale must pass `make i18n-check` and stay
complete.

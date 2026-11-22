# Freehand Digitize i18n

Qt `.ts` catalogs generated from the English source, translations kept in JSON
master data, compiled `.qm` files shipped with the plugin, and a quality gate
that rejects unfinished or broken entries.

## Architecture

- **Source language: English.** The plugin UI strings are English literals.
- **Catalogs:** `i18n/freehand_digitize_<locale>.ts` / `.qm` for `es`, `pt_BR`,
  `fr`, `de`, `it` and `id`.
- **Master data:** `scripts/i18n/master_data/<locale>.json` maps every English
  source string to its translation. It is the single source of truth; do not
  edit `.ts` by hand.
- **Loader:** `gui/i18n.py` reads `locale/userLocale` from QGIS settings, tries
  the full locale (`pt_BR`) and then the language (`pt`), loads the first `.qm`
  found and installs it.
- **Fallback:** if no catalog matches (for example `en_US`), the English source
  strings are shown unchanged.

`core/` has no user-facing strings and no translation injection is needed.

## Workflow

```bash
# 1. Extract new strings and apply the master data for every locale
make transup

# 2. Compile the .ts catalogs into .qm
make transcompile

# 3. Quality gate
make i18n-check

# Clean compiled catalogs (regenerate with transcompile)
make transclean
```

`make transup` runs `pylupdate6` over the plugin sources, applies
`scripts/i18n/apply_full.py` for each locale in `LOCALES`, and refreshes the
`general_description` line in `metadata.txt` with
`scripts/i18n/update_metadata_languages.py`.

## Golden rules

- A user-facing literal must be inside
  `QCoreApplication.translate("FreehandDigitize", "...")` with a **literal**
  context; `pylupdate6` does not extract a variable context.
- Keep `{placeholders}` identical in source and translation.
- Never edit `.qm` files; they are compiled binaries.
- Never edit `.ts` directly: `make transup` regenerates it and injects the JSON.
- JSON keys are the exact English source strings (including `\n`); values are the
  translations.
- Add a new language by creating `i18n/freehand_digitize_<code>.ts` with
  `pylupdate6`, `master_data/<code>.json`, then run `make transup`,
  `make transcompile` and `make i18n-check`.

## Language priority

The current catalogs are `es`, `pt_BR`, `fr`, `de`, `it` and `id`. The order is
based on QGIS country opens (last-30-day public analytics), QGIS documentation
translation coverage and the size of the local community:

| Priority | Locale | Notes |
| :---: | :--- | :--- |
| 1 | `es` | Large QGIS community; exact prior wording preserved. |
| 2 | `pt_BR` | Strong QGIS use and community. |
| 3 | `fr` | Large historical QGIS community. |
| 4 | `de` | Large QGIS community. |
| 5 | `it` | High documentation coverage. |
| 6 | `id` | High QGIS use despite lower documentation coverage. |
| 7 | `zh_CN` | Large user base; future catalog. |
| 8 | `ja` | High documentation coverage; future catalog. |
| 9 | `pl` | Notable QGIS use; future catalog. |
| 10 | `ko` | High documentation coverage; future catalog. |

Do not ship a half-translated catalog: `make i18n-check` must pass for every
locale included in `LOCALES`.

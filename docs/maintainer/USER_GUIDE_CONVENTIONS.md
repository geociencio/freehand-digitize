# User Guide Conventions

> Version 2.0.0 | Last Updated: 2026-11-19
>
> Adapted from the SecInterp user-guide conventions to the current Freehand
> Digitize documentation (no Sphinx, no generated help, no translations).

## 1. Where things live

| Item | Location |
| :--- | :--- |
| Current user-facing guide | [`README.md`](../../README.md) (Spanish) |
| Future long-form guide | `docs/user/USER_GUIDE.md` (Spanish) |
| Images | `docs/images/` |
| Reference from `README.md` | `docs/images/<file>.png` |
| Reference from `docs/user/USER_GUIDE.md` | `../images/<file>.png` |
| Translations | none in 2.0.0 |

Do **not** add generated `help/html/` or duplicate the README. If a long-form
guide is created, the README links to it and keeps only a short quick start.

## 2. Image naming

Use a `prefix_` + descriptive, lowercase, underscore-separated name:

| Prefix | Use for | Example |
| :--- | :--- | :--- |
| `workflow_NN_` | Sequential tutorial steps (zero-padded) | `workflow_03_draw_polygon.png` |
| `ui_` | General interface screenshots | `ui_digitize_toolbar.png` |
| `guide_` | Feature/setup screenshots | `guide_tolerance_spinbox.png` |
| `guide_<tool>_N` | Sequential steps of one tool | `guide_snapping_1.png` |
| `feature_` | Highlighted single feature | `feature_attribute_form.png` |

- Sequential images **must** be zero-padded and consecutive (`_01`, `_02`, …).
- Use `.png`; aim for ~1200–1600 px width and < ~500 KB.
- Reuse existing screenshots; delete superseded files with `git rm`.

## 3. Markdown insertion pattern

```markdown
![Short alt text](docs/images/guide_tolerance_spinbox.png)
*Figura 1. Tolerancia de simplificación en la barra de digitalización.*
```

- Alt text and caption are user-facing: write them in **Spanish**.
- Put the image on its own line and the caption on the next line in italics.
- Keep captions short and numbered when they are part of a sequence.
- The alt text must describe the action, not the filename.

### Placement by section

| `README.md` section | Typical images |
| :--- | :--- |
| Uso | `workflow_01_select_layer.png`, `workflow_02_draw.png` |
| Atajos y botones | `guide_snapping_1.png` |
| Funciones / tolerancia | `guide_tolerance_spinbox.png` |
| Formulario de atributos | `feature_attribute_form.png` |
| Instalación | `ui_plugin_manager.png` |

## 4. After adding or updating images

```bash
make docs-check   # relative links in README/docs
make lint         # Python gates are unaffected, kept as a sanity check
```

There is no docs i18n pipeline in 2.0.0 and no Sphinx build. Images live outside
the plugin ZIP (`docs/` is excluded by `.qgisignore`), so they do not affect
`make zip`.

## 5. Checklist

- [ ] Image saved in `docs/images/` with a convention-compliant name.
- [ ] Referenced from `README.md` as `docs/images/<file>.png`.
- [ ] Alt text and Spanish caption present.
- [ ] Sequential images zero-padded and consecutive.
- [ ] Superseded images removed.
- [ ] `make docs-check` passes.

See also [DOCS_STYLE_GUIDE.md](DOCS_STYLE_GUIDE.md) and
[ARCHITECTURE_EN.md](../ARCHITECTURE_EN.md).

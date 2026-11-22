# Release Notes

Versioned, user-facing notes for every Freehand Digitize release.

## Convention

```text
docs/releases/notes/vX.Y.Z.md
```

- `X.Y.Z` is the exact numeric version in `metadata.txt` and the Git tag.
- Use the current `vX.Y.Z.md` naming only; do **not** add the legacy
  `RELEASE_NOTES_vX.Y.Z.md` files.
- Notes are written in English and are the body of the GitHub Release.
- `CHANGELOG.md` stays as the compact changelog; `metadata.txt` → `changelog=`
  stays as the short portal summary.

## Release flow

1. Create `docs/releases/notes/vX.Y.Z.md` from
   [`RELEASE_NOTES_TEMPLATE.md`](RELEASE_NOTES_TEMPLATE.md).
2. Draft it from `git log`, `CHANGELOG.md` and the relevant issues/PRs using the
   `changelog-generator` skill. Do not invent metrics.
3. Validate it:

   ```bash
   make release-notes-check
   # or: python scripts/check_release_notes.py --version X.Y.Z
   ```

4. Commit the note before creating the tag.
5. Publish with the note file:

   ```bash
   gh release create vX.Y.Z \
     --title "Freehand Digitize X.Y.Z" \
     --notes-file docs/releases/notes/vX.Y.Z.md \
     dist/freehand_digitize.X.Y.Z.zip \
     dist/freehand_digitize.X.Y.Z.zip.sha256
   ```

6. Upload the same ZIP to <https://plugins.qgis.org/plugins/freehand_digitize/>.

## Current notes

- [`notes/v2.0.0.md`](notes/v2.0.0.md)
- [`notes/v2.0.1.md`](notes/v2.0.1.md)
- [`notes/v2.0.2.md`](notes/v2.0.2.md)

`v2.1.0.md` is created only when the 2.1.0 release gate opens (2.0.2 public in
the QGIS portal).

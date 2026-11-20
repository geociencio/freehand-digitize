---
description: Procedure for i18n maintenance and expansion (Translations)
agent: qa_engineer
skills: [i18n-standards]
---

# Workflow: i18n Maintenance

This workflow ensures that translations are synchronized with the code and expanded following the project's translation standard.

## Steps

1. **Synchronize Strings**:
   // turbo
   Extract the latest strings from the source code using the project's translation tooling
   (e.g. `lupdate`/`gettext` extraction, or a project script).

2. **Validate Untranslated Strings**:
   Run the project's analyzer/i18n check to see which files have the most pending strings.

3. **Update Master Data**:
   - New language: create the per-language translation map (JSON/YAML/PO).
   - Existing language: update the map with newly detected keys.

4. **Apply Translations**:
   // turbo
   Inject the translation map back into the catalog (`.ts`/`.po`).

5. **Compile and Publish**:
   // turbo
   Compile the catalog to the runtime binary format (`.qm`/`.mo`).

6. **Update Metadata**:
   Ensure the release/version metadata reflects the translation changes and language count.

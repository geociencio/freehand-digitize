---
name: i18n-standards
description: Standards and best practices for internationalization (i18n). Use when adding or modifying user-facing strings, running translation tooling, triaging untranslated-string flags, or using the /i18n-maintenance workflow.
---

# Skill: i18n Standards

This skill defines the standard workflow for maintaining, updating, and validating
translations in a project.

## 1. Fundamental Principles

1. **Source Code (English)**: all source code, logs, and comments must be in English.
2. **Explicit Marking**: every user-visible string must be wrapped in the project's
   translation helper (e.g. `self.tr("...")` in Qt/QGIS, `gettext("...")`, or a
   framework-specific `t("...")`).
3. **No Concatenation**: use string formatting (`%s`, `.format()`, f-strings) instead
   of concatenation so word order can follow the target language's grammar.
   - ✅ `self.tr("File %s not found") % filename`
   - ❌ `self.tr("File ") + filename + self.tr(" not found")`

## 2. Workflow

### 2.1. Master Data Engine (Recommended for Scaling)
To add multiple languages or perform bulk updates:
1. **Translation map**: keep a `Source: Translation` map per language in a machine-
   readable file (JSON/YAML/PO).
2. **Extraction**: regenerate the translation catalog (`.ts`/`.po`) from source.
3. **Injection**: apply the translation map back into the catalog.
4. **Compilation**: compile the catalog to the binary runtime format (`.qm`/`.mo`).

### 2.2. Manual Review
For minor fixes or context review, edit the catalog files in a translation editor
(Qt Linguist for `.ts`, Poedit for `.po`):
- **Context**: ensure you understand where the string appears.
- **Variables**: keep `%1`, `%s`, etc. intact.

### 2.3. Compilation
Compile the catalog to the binary format consumed by the runtime and ship the binary
artifacts (not the source catalogs).

## 3. Critical Configuration (Gotchas)

### 3.1. Scan Scope
The extraction config must:
- **Exclude**: tests, dev scripts, and virtual environments.
- **Include**: application source (not generated/template files).

### 3.2. Release & Packaging
- **INCLUDE**: compiled binaries (`.qm`/`.mo`).
- **EXCLUDE**: source catalogs (`.ts`/`.po`) to reduce package size.

### 3.3. Untranslated-string detection
A static-analysis rule flags hardcoded user-facing strings not wrapped in the
translation helper. Inline opt-out tags (e.g. `# no-i18n`, `# noqa`) mark
developer-facing strings. The target is zero untranslated user-facing strings.

## 4. Common Snippets

### Loading a translator (Qt example)
```python
translator = QTranslator()
if translator.load(locale_path):
    QCoreApplication.installTranslator(translator)
```

### Gettext example
```python
import gettext
_ = gettext.gettext
print(_("Hello, world"))
```

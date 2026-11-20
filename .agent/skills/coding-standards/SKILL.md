---
name: coding-standards
description: Project coding standards, focused on the use of pathlib, Google docstrings, and strict typing. Use when writing Python code, performing refactors, or defining file paths.
---

# Coding Standards

Defines the technical rules to ensure modern, maintainable, and consistent Python code throughout the project.

## When to use this skill
- When creating new Python modules or functions.
- When refactoring existing code.
- When defining file paths or manipulating the file system.

## Degree of Freedom
- **Strict**: The use of `pathlib`, Google Docstrings, and Type Hints is mandatory.

## Workflow
1. **Typing**: Add type annotations (Type Hints) to all arguments and return values.
2. **Documentation**: Write docstrings following the Google format.
3. **Paths**: Replace string manipulations or `os.path` with `pathlib.Path` objects.
4. **Modeling**: Mandatory use of Dataclasses (DTOs) for all service returns. Avoid using index-based tuples for complex data transfer.
5. **Validation**: Run `ruff format .` and `ruff check .` to confirm compliance.
6. **Audit**: Run the project's analyzer for new user-facing strings and its security scan for sensitive code.

## Instructions and Rules

### Modern Python (Pathlib)
- NEVER use string concatenation for paths.
- Use `/` to join paths with `Path`.
- Example: `base_dir / "data" / "file.txt"`.

### Data Transfer Objects (DTOs)
- **Mandatory** use of Dataclasses (DTOs) for all service returns.
- Avoid index-based tuples for complex data transfer.

### Documentation (Google Style)
```python
"""Module-level docstring (MANDATORY per PEP 257)."""

def function(arg1: int) -> str:
    """Short summary.

    Args:
        arg1: Argument description.

    Returns:
        Return value description.
    """
```

### Code Quality
- Follow SOLID principles.
- Keep cyclomatic complexity within the project's `max_cc` threshold from `forge.toml`.

## Quality Checklist
- [ ] Is `pathlib` used for all paths?
- [ ] Do all functions have Type Hints?
- [ ] Do docstrings follow the Google format?
- [ ] Does the code pass `ruff check` and `ruff format`?

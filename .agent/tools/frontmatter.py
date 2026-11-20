#!/usr/bin/env python3
"""Frontmatter parsing shared by the Agentic Forge validators."""

from __future__ import annotations

from typing import Any

import yaml

_FENCE = "---"


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse the YAML frontmatter block of a Markdown document.

    Args:
        content: Full Markdown content.

    Returns:
        The parsed mapping, or an empty dict when the block is missing or
        malformed.
    """
    if not content.startswith(_FENCE):
        return {}

    parts = content.split(_FENCE, 2)
    if len(parts) < 3:
        return {}

    try:
        parsed = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def as_list(value: Any) -> list[str]:
    """Normalize an inline or block YAML list to a list of strings."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []

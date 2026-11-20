#!/usr/bin/env python3
"""Metric consistency validation and scanning for Agentic Forge."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import forge_paths

PROJECT_ROOT = forge_paths.PROJECT_ROOT
FRAMEWORK_DIR = forge_paths.FRAMEWORK_DIR
METRICS_FILE = forge_paths.METRICS_FILE
CC_THRESHOLD = forge_paths.MAX_CC


# =====================================================================
# Metric consistency validator
# =====================================================================
TEST_PATTERNS = [
    (
        re.compile(r"\b(\d+)\s*tests?\s*(?:OK|pass|passing|ok)", re.IGNORECASE),
        "test_count",
    ),
    (re.compile(r"tests?:\s*(\d+)"), "test_count"),
    (re.compile(r"total_?tests?:\s*(\d+)", re.IGNORECASE), "test_count"),
    (re.compile(r"(\d+)/\d+\s*\(100%\)", re.IGNORECASE), "test_count"),
    (re.compile(r"Achieve\s+(\d+)\+?\s*passing\s+tests?", re.IGNORECASE), "test_min"),
]

QUALITY_PATTERNS = [
    (re.compile(r"[Qq]uality\s*[Ss]core:?\s*(\d+\.?\d*)/?\d*"), "quality_score"),
    (
        re.compile(r"[Mm]odule\s*[Ss]tability:?\s*\*?\*?(\d+\.?\d*)/?\d*"),
        "quality_score",
    ),
    (re.compile(r"[Ss]tability\s*[Ss]core:?\s*(\d+\.?\d*)/?\d*"), "quality_score"),
]

CC_PATTERNS = [
    (re.compile(r"CC\s*[><=]+\s*(\d+)"), "cc_threshold"),
    (
        re.compile(r"cyclomatic\s+complexity\s+(?:below|under)\s+(\d+)", re.IGNORECASE),
        "cc_threshold",
    ),
    (re.compile(r"complexity\s*(?:>\s*(\d+)|<=?\s*(\d+))"), "cc_threshold"),
]

# Common stale→correct mappings for --fix mode (project-tunable).
# Project-specific stale-value mappings can be injected by an adapter.
# The framework intentionally ships no hardcoded project values.
STALE_MAPPINGS: dict[str, dict] = {}

# Phrases that mark a line as documenting a past/archaic state (project-tunable).
ARCHAIC_MARKERS = [
    "v3.6.0 Baseline",
    "v3.5.0",
    "v3.4.0",
    "v3.3.0",
    "v3.2.0",
    "v3.0.0",
    "v2.",
    "previously",
    "before phase",
    "was stale",
]


@dataclass
class MetricViolation:
    file: str
    line: int
    metric_type: str
    found_value: str
    expected_value: str
    context: str

    def __str__(self):
        return (
            f"  {self.file}:{self.line}  [{self.metric_type}] "
            f"found={self.found_value}  expected={self.expected_value}"
            f"\n    → {self.context.strip()}"
        )


@dataclass
class ValidationReport:
    violations: list[MetricViolation] = field(default_factory=list)
    files_scanned: int = 0

    @property
    def clean(self) -> bool:
        return len(self.violations) == 0


def load_ground_truth() -> dict:
    """Extract canonical metric values from agent_metrics.json."""
    if not METRICS_FILE.exists():
        return {}

    try:
        data = json.loads(METRICS_FILE.read_text())
    except json.JSONDecodeError:
        return {}

    truth = {}
    summary = data.get("summary", {})
    if "test_count" in summary:
        truth["test_count"] = summary["test_count"]
    elif "tests_ok" in summary:
        truth["test_count"] = summary["tests_ok"]

    truth["quality_score"] = summary.get("quality_score_latest")
    truth["maintainability_score"] = summary.get("maintainability_score")
    truth["security_score"] = summary.get("security_score")

    # CC gate threshold: single source of truth in forge.toml (max_cc).
    truth["cc_threshold"] = CC_THRESHOLD

    return truth


_SUMMARY_SCORE_KEYS = {
    "module_stability": "quality_score_latest",
    "quality_score": "quality_score_latest",
    "maintainability": "maintainability_score",
    "security": "security_score",
}


def _check_issue_total(summary: dict, issues: list[str]) -> None:
    """Validate that total_issues equals the sum of the issue breakdown."""
    breakdown = summary.get("issue_breakdown", {})
    total_issues = summary.get("total_issues")
    if total_issues is None or not breakdown:
        return
    breakdown_sum = sum(v for v in breakdown.values() if isinstance(v, int))
    if total_issues != breakdown_sum:
        issues.append(
            f"summary.total_issues ({total_issues}) != sum(issue_breakdown) ({breakdown_sum})"
        )


def _check_test_count(summary: dict, issues: list[str]) -> None:
    """Validate that test_count and tests_ok agree."""
    test_count = summary.get("test_count")
    tests_ok = summary.get("tests_ok")
    if test_count is not None and tests_ok is not None and test_count != tests_ok:
        issues.append(f"summary.test_count ({test_count}) != summary.tests_ok ({tests_ok})")


def _check_ground_truth_scores(summary: dict, data: dict, issues: list[str]) -> None:
    """Compare summary scores with any declared ground-truth source scores."""
    sources = data.get("ground_truth_sources", {})
    if not isinstance(sources, dict):
        return
    for source_name, source in sources.items():
        scores = source.get("scores", {}) if isinstance(source, dict) else {}
        if not isinstance(scores, dict):
            continue
        for gt_key, value in scores.items():
            summary_key = _SUMMARY_SCORE_KEYS.get(gt_key)
            if summary_key is None:
                continue
            summary_val = summary.get(summary_key)
            if summary_val is not None and summary_val != value:
                issues.append(
                    f"summary.{summary_key} ({summary_val}) != "
                    f"ground_truth_sources.{source_name}.scores.{gt_key} ({value})"
                )


def _check_session_date(data: dict, issues: list[str]) -> None:
    """Validate that last_session.date is not older than the newest history entry."""
    last_date = data.get("last_session", {}).get("date")
    history = data.get("history", [])
    dates = [h.get("date") for h in history if h.get("date")]
    if last_date and dates and max(dates) > last_date:
        issues.append(
            f"last_session.date ({last_date}) is older than newest history entry ({max(dates)})"
        )


def check_internal_consistency(metrics_file: Path = METRICS_FILE) -> list[str]:
    """Validate that agent_metrics.json is internally coherent."""
    if not metrics_file.exists():
        return ["agent_metrics.json not found"]

    try:
        data = json.loads(metrics_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"agent_metrics.json is not valid JSON: {exc}"]

    issues: list[str] = []
    summary = data.get("summary", {})
    _check_issue_total(summary, issues)
    _check_test_count(summary, issues)
    _check_ground_truth_scores(summary, data, issues)
    _check_session_date(data, issues)
    return issues


def _relative_to_agent_roots(filepath: Path) -> str:
    """Return ``filepath`` relative to the framework or state root."""
    for root in (FRAMEWORK_DIR, forge_paths.STATE_DIR):
        try:
            return str(filepath.relative_to(root))
        except ValueError:
            continue
    return str(filepath)


def should_skip_file(filepath: Path) -> bool:
    """Skip history archives and non-markdown/json files."""
    if filepath.suffix not in (".md", ".json"):
        return True

    rel_path = _relative_to_agent_roots(filepath)
    cache_parts = {".mypy_cache", ".ruff_cache", ".pytest_cache", "__pycache__", ".git"}
    if cache_parts.intersection(filepath.parts):
        return True
    if rel_path.startswith("history/"):
        return True
    if rel_path.startswith("architecture/"):
        return True
    # Domain packs are templates for other projects: their sample metrics
    # must not be validated against this project's ground truth.
    if rel_path.startswith("scaffold/"):
        return True

    # Never validate the ground-truth file against itself.
    is_metrics_file = filepath.resolve() == METRICS_FILE.resolve()
    return is_metrics_file


def extract_metrics_from_line(line: str) -> list[tuple[str, str, str]]:
    """Extract metric references from a single line."""
    results = []

    for pattern, metric_type in TEST_PATTERNS:
        for m in pattern.finditer(line):
            results.append((metric_type, m.group(0), m.group(1)))

    for pattern, metric_type in QUALITY_PATTERNS:
        for m in pattern.finditer(line):
            results.append((metric_type, m.group(0), m.group(1)))

    for pattern, metric_type in CC_PATTERNS:
        for m in pattern.finditer(line):
            val = m.group(1) or m.group(2)
            if val:
                results.append((metric_type, m.group(0), val))

    return results


def normalize_value(val_str: str) -> float | None:
    """Normalize a found metric value to float for comparison."""
    try:
        return float(val_str)
    except ValueError:
        return None


def detect_documented_triage(context: str, found_val: float, expected_val: float) -> bool:
    """Skip lines that explicitly document a discrepancy being triaged/resolved."""
    triage_markers = [
        "vs",
        "→",
        "conflicting",
        "verified",
        "RESOLVED",
        "resolved",
        "discrepancy",
        "confirmed",
    ]
    if not any(marker.lower() in context.lower() for marker in triage_markers):
        return False
    return str(int(found_val)) in context and str(int(expected_val)) in context


def is_archaic_reference(context: str, found_val: float, expected_val: float) -> bool:
    """Check if the line is describing a past state (e.g., a baseline version)."""
    return any(marker.lower() in context.lower() for marker in ARCHAIC_MARKERS)


def validate_file(filepath: Path, ground_truth: dict) -> list[MetricViolation]:
    """Scan a single file for metric inconsistencies."""
    violations: list[MetricViolation] = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return violations

    lines = content.splitlines()
    for lineno, line in enumerate(lines, start=1):
        metrics = extract_metrics_from_line(line)
        for metric_type, _raw_match, clean_val in metrics:
            found = normalize_value(clean_val)
            if found is None:
                continue

            expected = ground_truth.get(metric_type)
            if expected is None:
                continue

            if found == expected:
                continue

            if detect_documented_triage(line, found, expected):
                continue
            if is_archaic_reference(line, found, expected):
                continue

            violations.append(
                MetricViolation(
                    file=str(filepath.relative_to(PROJECT_ROOT)),
                    line=lineno,
                    metric_type=metric_type,
                    found_value=str(int(found) if found == int(found) else found),
                    expected_value=str(int(expected) if expected == int(expected) else expected),
                    context=line.strip(),
                )
            )

    return violations


def scan_agent_files(ground_truth: dict) -> ValidationReport:
    """Scan all relevant agentic files (framework + project state)."""
    report = ValidationReport()

    for root in forge_paths.state_and_framework_dirs():
        for filepath in sorted(root.rglob("*")):
            if not filepath.is_file():
                continue
            if should_skip_file(filepath):
                continue

            report.files_scanned += 1
            report.violations.extend(validate_file(filepath, ground_truth))

    return report


def auto_fix(filepath: Path, violations: list[MetricViolation]) -> bool:
    """Attempt to auto-fix known stale values inline."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return False

    modified = False
    for v in violations:
        mapping = STALE_MAPPINGS.get(v.metric_type, {})
        try:
            found_num = float(v.found_value)
        except ValueError:
            continue
        found_int = int(found_num) if found_num == int(found_num) else found_num

        new_val = mapping.get(found_int)
        if new_val is None:
            continue

        old_str = str(v.found_value)
        if old_str in content:
            content = content.replace(old_str, str(new_val), 1)
            modified = True

    if modified:
        filepath.write_text(content, encoding="utf-8")

    return modified

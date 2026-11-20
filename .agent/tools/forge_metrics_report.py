#!/usr/bin/env python3
"""Metrics trend report generation for Agentic Forge."""

from __future__ import annotations

import json
import sys
from datetime import datetime

import forge_paths

METRICS_FILE = forge_paths.METRICS_FILE
PROJECT_NAME = forge_paths.PROJECT_NAME


# =====================================================================
# Metrics trend report
# =====================================================================
CHART_WIDTH = 30
BLOCKS = "▁▂▃▄▅▆▇█"


def trend_direction(values: list[float]) -> str:
    if len(values) < 2:
        return "⏸️  Stable (insufficient data)"
    first, last = values[0], values[-1]
    if last > first:
        return "📈 Improving"
    elif last < first:
        return "📉 Declining"
    return "⏸️  Stable"


def sparkline(values: list[float], width: int = CHART_WIDTH) -> str:
    """Generate an ASCII sparkline from a series of values."""
    if not values:
        return "(no data)"
    cleaned = [v for v in values if v is not None]
    if not cleaned:
        return "(no data)"
    vmin, vmax = min(cleaned), max(cleaned)
    if vmin == vmax:
        return "─" * min(len(cleaned), width)
    step = len(cleaned) / width if len(cleaned) > width else 1
    result = []
    for i in range(width):
        idx = min(int(i * step), len(cleaned) - 1)
        norm = (cleaned[idx] - vmin) / (vmax - vmin)
        block_idx = min(int(norm * (len(BLOCKS) - 1)), len(BLOCKS) - 1)
        result.append(BLOCKS[block_idx])
    return "".join(result)


def bar_chart(label: str, value: float, max_val: float = 100.0, width: int = 20) -> str:
    """Generate a single labeled ASCII bar."""
    bar_len = max(1, int((value / max_val) * width))
    bar = "█" * bar_len + "░" * (width - bar_len)
    return f"`{label:>16s}` {bar} {value:.1f}"


def extract_score_history(history: list[dict]) -> list[tuple[str, float]]:
    """Extract quality score timeline from session history."""
    entries = []
    for entry in history:
        qs = _find_score(entry)
        if qs is not None:
            entries.append((entry.get("date", "?"), qs))
    return entries


def _find_score(entry: dict) -> float | None:
    """Try multiple keys for quality score."""
    for key in ("quality_score", "quality_score_latest", "score"):
        if key in entry and entry[key] is not None:
            try:
                return float(entry[key])
            except (ValueError, TypeError):
                pass
    return None


def _display(value: object) -> object:
    """Return a printable KPI value, falling back to ``?`` for nulls."""
    return "?" if value is None else value


def _numeric(value: object) -> float:
    """Convert a KPI value to float, returning 0 for unknown values."""
    return float(value) if isinstance(value, (int, float)) else 0.0


def _load_report_data() -> dict:
    """Load the metrics document or exit with a clear error."""
    if not METRICS_FILE.exists():
        print(f"Error: {METRICS_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error parsing JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def _print_kpis(summary: dict) -> None:
    """Print the KPI dashboard table."""
    print("\n## KPI Dashboard\n")
    values = {
        "Module Stability": _display(summary.get("quality_score_latest")),
        "Maintainability": _display(summary.get("maintainability_score")),
        "CC Gate": _display(summary.get("cyclomatic_complexity_gate")),
        "Total Issues": _display(summary.get("total_issues")),
        "Task Completion": _display(summary.get("task_completion_rate")),
        "Sessions Tracked": _display(summary.get("total_sessions")),
    }
    if summary.get("security_score") is not None:
        values["Security"] = _display(summary.get("security_score"))
    if summary.get("i18n_hygiene_gate") is not None:
        values["i18n Gate"] = _display(summary.get("i18n_hygiene_gate"))
    print("| KPI | Value |")
    print("| :--- | :--- |")
    for label, value in values.items():
        suffix = "/100" if label in ("Module Stability", "Maintainability", "Security") else ""
        print(f"| {label} | **{value}{suffix}** |")


def _print_quality_trend(history: list[dict], compact: bool) -> None:
    """Print the quality-score sparkline and optional per-session table."""
    qs_history = extract_score_history(history)
    if not qs_history:
        return
    scores = [score for _, score in qs_history]
    print("\n## Quality Score Trend\n")
    print(f"```\n{sparkline(scores, 40)}\n```")
    print(
        f"**Range**: {min(scores):.1f} → {max(scores):.1f}  |  "
        f"**Direction**: {trend_direction(scores)}"
    )
    print(f"**Sessions tracked**: {len(qs_history)}")
    if compact:
        return
    print("\n| Session | Score | Bar |")
    print("| :--- | :--- | :--- |")
    for date, score in qs_history[-8:]:
        print(f"| {date} | {score:.1f} | {'█' * max(1, int(score / 5))} |")


def _print_bars(summary: dict, compact: bool) -> None:
    """Print the multi-metric bar chart when not in compact mode."""
    if compact:
        return
    print("\n## Multi-Metric Comparison\n")
    print("```")
    print(bar_chart("Stability", _numeric(summary.get("quality_score_latest"))))
    print(bar_chart("Maintainability", _numeric(summary.get("maintainability_score"))))
    if summary.get("security_score") is not None:
        print(bar_chart("Security", _numeric(summary.get("security_score"))))
    print("```")


def _print_i18n_and_issues(summary: dict, compact: bool) -> None:
    """Print optional i18n status and the active-issue breakdown."""
    i18n_issues = summary.get("i18n_issues")
    if i18n_issues is not None:
        print("\n## i18n Status\n")
        print("| Metric | Value |")
        print("| :--- | :--- |")
        print(f"| analyzer MISSING_I18N | {i18n_issues} |")

    breakdown = summary.get("issue_breakdown", {})
    if not breakdown or compact:
        return
    print("\n## Active Issues\n")
    print("| Category | Count |")
    print("| :--- | :--- |")
    for category, count in sorted(breakdown.items(), key=lambda item: -item[1]):
        emoji = "🔴" if count > 50 else "🟡" if count > 10 else "🟢"
        print(f"| {category} | {emoji} {count} |")


def _print_history(history: list[dict]) -> None:
    """Print the most recent sessions."""
    if not history:
        return
    print(f"\n## Session History (last {min(10, len(history))})\n")
    print("| Date | Session | TCR | Retries | Status |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    for entry in history[-10:][::-1]:
        status = entry.get("status", "SUCCESS")
        emoji = "✅" if status == "SUCCESS" else "🚀" if status == "release" else "⚠️"
        print(
            f"| {entry.get('date', '?')} | {entry.get('session', '?')} | "
            f"{entry.get('task_completion_rate', 1.0):.2f} | "
            f"{entry.get('retries', 0)} | {emoji} {status} |"
        )


def _print_delta(history: list[dict]) -> None:
    """Print the delta between the last two sessions when available."""
    if len(history) < 2:
        return
    previous, current = history[-2], history[-1]
    previous_score, current_score = _find_score(previous), _find_score(current)
    print("\n## Last Session Delta\n")
    print(f"**{previous.get('date', '?')} → {current.get('date', '?')}**\n")
    if previous_score is None or current_score is None:
        return
    delta = current_score - previous_score
    arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
    print(
        f"- Quality Score: {previous_score:.1f} {arrow} {current_score:.1f} "
        f"({'+' if delta > 0 else ''}{delta:.1f})"
    )


def _print_freshness(ground_truth: dict) -> None:
    """Print the data-freshness table."""
    print("\n## Data Freshness\n")
    print("| Source | Last Run |")
    print("| :--- | :--- |")
    for source_name, source_data in ground_truth.items():
        if isinstance(source_data, dict):
            print(f"| {source_name} | {source_data.get('date', '?')} |")


def generate_report(compact: bool = False) -> None:
    """Print the metrics trend report."""
    data = _load_report_data()
    summary = data.get("summary", {})
    history = data.get("history", [])
    ground_truth = data.get("ground_truth_sources", {})

    print(f"# {PROJECT_NAME} Metrics Trend Report\n")
    print(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("**Data source**: `agent_metrics.json`")
    _print_kpis(summary)
    _print_quality_trend(history, compact)
    _print_bars(summary, compact)
    _print_i18n_and_issues(summary, compact)
    _print_history(history)
    _print_delta(history)
    _print_freshness(ground_truth)
    print(
        f"\n\n*Generated by Agentic Forge Metrics Engine — "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    )


def report_main() -> None:
    generate_report(compact="--compact" in sys.argv)

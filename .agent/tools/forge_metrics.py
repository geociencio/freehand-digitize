#!/usr/bin/env python3
"""Generic agentic metrics core for Agentic Forge.

Subcommands (also reachable as ``forge metrics <cmd>``):
    validate [--quiet] [--fix]
    report [--compact]
    close-session [--topic NAME]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import forge_paths
from forge_metrics_checks import (
    auto_fix,
    check_internal_consistency,
    load_ground_truth,
    scan_agent_files,
)
from forge_metrics_report import report_main

METRICS_FILE = forge_paths.METRICS_FILE
PROJECT_ROOT = forge_paths.PROJECT_ROOT


# =====================================================================
# Session rotation
# =====================================================================
def rotate_session_history(topic: str | None = None, metrics_file: Path = METRICS_FILE) -> bool:
    """Rotate the current last_session into history and start a fresh one.

    Prevents ``last_session`` from going stale across sessions by always
    advancing its date to today. The previous session is preserved in the
    ``history`` array (deduplicated by date+topic).
    """
    if not metrics_file.exists():
        print(f"❌ {metrics_file} not found", file=sys.stderr)
        return False

    try:
        data = json.loads(metrics_file.read_text())
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {metrics_file}: {e}", file=sys.stderr)
        return False

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = data.get("summary", {})

    previous = data.get("last_session") or {}
    history = data.get("history", []) or []

    # Preserve the previous session in history (dedup by date+topic)
    if previous.get("date"):
        prev_topic = previous.get("topic") or previous.get("session") or ""
        prev_key = (previous["date"], prev_topic)
        existing_keys = {
            (h.get("date"), h.get("session") or h.get("topic") or "")
            for h in history
            if isinstance(h, dict)
        }
        if prev_key not in existing_keys:
            archived = dict(previous)
            if "topic" in archived and "session" not in archived:
                archived["session"] = archived.pop("topic")
            history.insert(0, archived)

    data["last_session"] = {
        "date": today,
        "topic": topic or "session",
        "tests_ok": summary.get("tests_ok", summary.get("test_count")),
        "quality_score": summary.get("quality_score_latest"),
        "task_completion_rate": None,
        "retries": 0,
        "stop_conditions_triggered": 0,
        "tasks": [],
        "status": "SUCCESS",
    }
    data["history"] = history

    metrics_file.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n")
    return True


# =====================================================================
# CLI entry points
# =====================================================================
def _print_internal_issues(issues: list[str], quiet: bool) -> None:
    """Print internal-consistency issues when not quiet."""
    if issues and not quiet:
        print("❌ agent_metrics.json internal inconsistencies:")
        for issue in issues:
            print(f"  - {issue}")
        print()


def _print_scan(report, ground_truth: dict, quiet: bool) -> None:
    """Print the scan summary when not quiet."""
    if quiet:
        return
    print(f"🔍 Scanned {report.files_scanned} agentic files (framework + state)")
    print(
        f"   Ground truth: tests={ground_truth.get('test_count', '?')}, "
        f"quality={ground_truth.get('quality_score', '?')}, "
        f"CC≤{ground_truth.get('cc_threshold', '?')}"
    )


def _apply_fixes(report, quiet: bool) -> int:
    """Apply auto-fixes for the reported violations and return the count."""
    fixes_applied = 0
    for violation in report.violations:
        if not quiet:
            print(str(violation))
        filepath = PROJECT_ROOT / violation.file
        if auto_fix(filepath, [violation]):
            fixes_applied += 1
    return fixes_applied


def _ground_truth_or_exit() -> dict:
    """Load ground truth or exit with guidance."""
    ground_truth = load_ground_truth()
    if not ground_truth:
        print("❌ Cannot load ground truth from agent_metrics.json", file=sys.stderr)
        print("   Run `uv run python scripts/sync_metrics.py` first.", file=sys.stderr)
        sys.exit(1)
    return ground_truth


def _report_violations(report, quiet: bool, fix_mode: bool) -> None:
    """Print violations and apply fixes when requested."""
    if not report.violations:
        return
    if not quiet:
        print(f"❌ Found {len(report.violations)} metric inconsistencies:\n")
    if not fix_mode:
        if not quiet:
            for violation in report.violations:
                print(str(violation))
        return
    fixes_applied = _apply_fixes(report, quiet)
    if fixes_applied > 0:
        if not quiet:
            print(f"\n🔧 Auto-fixed {fixes_applied} stale values. Run again to verify.")
        sys.exit(0)


def validate_main() -> None:
    """Validate metric consistency and optionally auto-fix stale values."""
    quiet = "--quiet" in sys.argv
    fix_mode = "--fix" in sys.argv

    internal_issues = check_internal_consistency()
    _print_internal_issues(internal_issues, quiet)
    ground_truth = _ground_truth_or_exit()
    report = scan_agent_files(ground_truth)
    _print_scan(report, ground_truth, quiet)

    if report.clean and not internal_issues:
        if not quiet:
            print("✅ All agentic files are metric-consistent with agent_metrics.json")
        sys.exit(0)

    _report_violations(report, quiet, fix_mode)
    sys.exit(1)


def close_session_main() -> None:
    topic = None
    if "--topic" in sys.argv:
        try:
            topic = sys.argv[sys.argv.index("--topic") + 1]
        except IndexError:
            topic = None
    if not rotate_session_history(topic):
        sys.exit(1)


def main() -> None:
    argv = sys.argv[1:]
    if "report" in argv or "--report" in argv:
        report_main()
    elif "validate" in argv or "--validate" in argv:
        validate_main()
    elif "close-session" in argv or "--close-session" in argv:
        close_session_main()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()

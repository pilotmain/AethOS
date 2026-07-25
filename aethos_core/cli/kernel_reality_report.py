# SPDX-License-Identifier: Apache-2.0
"""KERNEL_REALITY_PROOF_001 — daily operational evidence report."""

from __future__ import annotations

import argparse
import json
import sys


def format_reality_report(summary: dict) -> str:
    sr = summary.get("success_report") or {}
    lines = [
        "# Kernel Reality Report",
        "",
        f"Generated: {summary.get('generated_at', '—')}",
        f"Period: last {summary.get('period_days', 7)} day(s)",
        f"Evidence store: `{summary.get('evidence_store', '—')}`",
        "",
    ]
    if summary.get("message"):
        lines.extend([f"> {summary['message']}", ""])
    lines.extend(
        [
        "## Success report",
        "",
        f"- Kernel turns: **{sr.get('kernel_turns', summary.get('total_turns', 0))}**",
        f"- Railway accuracy: **{sr.get('railway_accuracy_pct', '—')}%**",
        f"- Vercel accuracy: **{sr.get('vercel_accuracy_pct', '—')}%**",
        f"- Conversation continuity: **{sr.get('conversation_continuity_pct', '—')}%**",
        f"- Recovery success rate: **{sr.get('recovery_success_rate_pct', '—')}%**",
        f"- Provider misroutes: **{sr.get('provider_misroutes', 0)}**",
        f"- Fallback rate: **{sr.get('fallback_rate_pct', '—')}%**",
        f"- Operational goals started: **{sr.get('operational_goals_started', 0)}**",
        f"- Operational goals completed: **{sr.get('operational_goals_completed', 0)}**",
        f"- Goal completion rate: **{sr.get('goal_completion_rate_pct', '—')}%**",
        f"- User retry count: **{sr.get('user_retry_count', 0)}**",
        f"- User clarifications: **{sr.get('user_clarifications', 0)}**",
        f"- 7-day soak: **{sr.get('seven_day_soak', 'PENDING')}**",
        "",
        "## Daily summary",
        "",
        f"- Total turns: **{summary.get('total_turns', 0)}**",
        f"- Successful: **{summary.get('successful_turns', 0)}**",
        f"- Failed: **{summary.get('failed_turns', 0)}**",
        f"- Recovered: **{summary.get('recovered_turns', 0)}**",
        f"- Fallback: **{summary.get('fallback_turns', 0)}**",
        f"- Success rate: **{_pct(summary.get('success_rate'))}**",
        f"- Recovery rate: **{_pct(summary.get('recovery_success_rate'))}**",
        f"- Continuity accuracy: **{_pct(summary.get('continuity_accuracy'))}**",
        "",
        "## Provider accuracy summary",
        "",
        ]
    )
    routing = summary.get("provider_routing") or {}
    lines.extend(
        [
            f"- Provider accuracy rate: **{_pct(routing.get('provider_accuracy_rate'))}**",
            f"- Provider misroutes: **{routing.get('provider_misroute_count', 0)}**",
            f"- Railway routing accuracy: **{_pct(routing.get('railway_accuracy'))}**",
            f"- Vercel routing accuracy: **{_pct(routing.get('vercel_accuracy'))}**",
            "",
            "## Provider summary (turn volume)",
            "",
        ]
    )
    for provider, stats in (summary.get("provider_proof") or {}).items():
        lines.append(f"### {provider.title()}")
        lines.append(f"- Successful turns: **{stats.get('successful_turns', 0)}** / 100 required")
        lines.append(f"- Meets 100 target: **{'yes' if stats.get('meets_100_successful') else 'no'}**")
        cats = stats.get("by_category") or {}
        if cats:
            lines.append("- Categories: " + ", ".join(f"{k}={v}" for k, v in sorted(cats.items())))
        lines.append("")

    goals = summary.get("goal_completion") or {}
    lines.extend(
        [
            "## Goal completion summary",
            "",
            f"- Goals started: **{goals.get('goals_started', 0)}**",
            f"- Goals completed: **{goals.get('goals_completed', 0)}**",
            f"- Goals blocked: **{goals.get('goals_blocked', 0)}**",
            f"- Completion rate: **{_pct(goals.get('goal_completion_rate'))}**",
            f"- Meets 20 completed: **{'yes' if goals.get('meets_20_completed') else 'no'}**",
            "",
            "## User friction summary",
            "",
        ]
    )
    friction = summary.get("user_friction") or {}
    lines.extend(
        [
            f"- Repeated questions: **{friction.get('repeated_question_count', 0)}**",
            f"- Retries: **{friction.get('retry_count', 0)}**",
            f"- Clarifications: **{friction.get('clarification_count', 0)}**",
            f"- Fallbacks: **{friction.get('fallback_count', 0)}**",
            f"- Corrections: **{friction.get('correction_count', 0)}**",
            f"- Friction trend: **{friction.get('friction_trend', 'unknown')}**",
            "",
            "## Failure summary",
            "",
        ]
    )
    fails = summary.get("top_failures") or []
    if not fails:
        lines.append("- No recorded failures in window.")
    else:
        for row in fails:
            lines.append(f"- `{row.get('intent')}` — {row.get('count')} occurrence(s)")
    lines.extend(["", "## Recovery summary", ""])
    lines.append(f"- Recovery success rate: **{_pct(summary.get('recovery_success_rate'))}** (target 90%+)")
    lines.append(f"- Recovered turns: **{summary.get('recovered_turns', 0)}**")
    lines.extend(["", "## Top regressions", ""])
    regs = summary.get("top_regressions") or []
    if not regs:
        lines.append("- No provider misroutes or continuity failures recorded.")
    else:
        for row in regs:
            lines.append(f"- `{row.get('request')}` — {row.get('count')} occurrence(s)")

    acc = summary.get("acceptance") or {}
    soak = summary.get("soak_progress") or {}
    lines.extend(
        [
            "",
            "## Acceptance gates",
            "",
            f"- Railway 100+ successful: **{'PASS' if acc.get('railway_100_successful_turns') else 'PENDING'}**",
            f"- Vercel 100+ successful: **{'PASS' if acc.get('vercel_100_successful_turns') else 'PENDING'}**",
            f"- Continuity 95%+: **{'PASS' if acc.get('continuity_95_percent') else 'PENDING'}**",
            f"- Recovery 90%+: **{'PASS' if acc.get('recovery_90_percent') else 'PENDING'}**",
            f"- Provider accuracy 95%+: **{'PASS' if acc.get('provider_accuracy_95_percent') else 'PENDING'}**",
            f"- 20+ goals completed: **{'PASS' if acc.get('twenty_goals_completed') else 'PENDING'}**",
            f"- Fallback <5%: **{'PASS' if acc.get('fallback_under_5_percent') else 'PENDING'}**",
            f"- 7-day soak: **{'PASS' if soak.get('complete') else 'PENDING'}** ({soak.get('days_recorded', 0)}/{soak.get('required_days', 7)} days)",
            "",
            "## Ready for manual test (kernel reality gate)",
            "",
            f"**{'YES — schedule manual test session' if acc.get('ready_for_manual_test') else 'NO — continue soak and live usage'}**",
            "",
            "## Ready for APPROVAL_PRIVACY_REHARDENING_001",
            "",
            f"**{'YES' if acc.get('ready_for_approval_privacy_rehardening') else 'NO — accumulate live evidence first'}**",
        ]
    )
    return "\n".join(lines)


def _pct(value) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.1f}"


def _archive_evidence_backup(summary: dict) -> None:
    """Archive live store + soak summary under repo-root evidence/ (not in git)."""
    from datetime import UTC, datetime

    from aethos_core.operational_session.kernel_reality_registry import (
        _evidence_root,
        archive_evidence_store,
    )

    archive_evidence_store()
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    evidence_root = _evidence_root()
    evidence_root.mkdir(parents=True, exist_ok=True)
    soak_dir = evidence_root / "soak"
    soak_dir.mkdir(parents=True, exist_ok=True)
    soak_dir.joinpath(f"{day}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def cmd_kernel_reality_report(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aethos kernel-reality-report")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--save-daily", action="store_true", help="Persist today's snapshot for soak tracking")
    parser.add_argument(
        "--as-date",
        default=None,
        metavar="YYYY-MM-DD",
        help="Synthetic soak day (requires KERNEL_SOAK_DEV_ACCELERATE=true)",
    )
    parser.add_argument(
        "--restore-evidence",
        nargs="?",
        const="latest",
        default=None,
        metavar="YYYY-MM-DD",
        help="Restore data/operational_kernel_reality from evidence/backup (latest or given day)",
    )
    args = parser.parse_args(argv)

    from aethos_core.operational_session.kernel_reality_registry import (
        archive_evidence_store,
        compute_reality_summary,
        restore_evidence_backup,
        save_daily_snapshot,
        soak_progress,
    )

    if args.restore_evidence:
        day = None if args.restore_evidence == "latest" else args.restore_evidence
        result = restore_evidence_backup(day=day)
        if args.json:
            print(json.dumps(result, indent=2))
        elif result.get("ok"):
            print(f"Restored {result.get('record_count', 0)} record(s) from {result.get('restored_from')}")
        else:
            print(result.get("error") or "Restore failed.")
        return 0 if result.get("ok") else 1

    summary = compute_reality_summary(days=args.days)
    if args.save_daily:
        archive_evidence_store()
        save_daily_snapshot(summary, as_date=args.as_date)
        _archive_evidence_backup(summary)
    summary["soak_progress"] = soak_progress(required_days=7)
    acc = dict(summary.get("acceptance") or {})
    soak_complete = bool(summary["soak_progress"].get("complete", False))
    acc["seven_day_soak_complete"] = soak_complete
    proven_keys = (
        "railway_100_successful_turns",
        "vercel_100_successful_turns",
        "continuity_95_percent",
        "recovery_90_percent",
        "provider_accuracy_95_percent",
        "fallback_under_5_percent",
        "twenty_goals_completed",
        "seven_day_soak_complete",
    )
    acc["operationally_proven"] = all(acc.get(k) for k in proven_keys)
    acc["ready_for_approval_privacy_rehardening"] = acc["operationally_proven"]
    acc["ready_for_manual_test"] = acc["operationally_proven"]
    if summary.get("success_report") is not None:
        summary["success_report"]["seven_day_soak"] = "PASS" if soak_complete else "PENDING"
    summary["acceptance"] = acc

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(format_reality_report(summary))
    return 0


def main(argv: list[str] | None = None) -> int:
    return cmd_kernel_reality_report(argv)


if __name__ == "__main__":
    sys.exit(main())

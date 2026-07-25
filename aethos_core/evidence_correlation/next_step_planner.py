# SPDX-License-Identifier: Apache-2.0
"""Single best next action from correlated evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.evidence_correlation.evidence_conflict_detector import ConflictReport
from aethos_core.evidence_correlation.evidence_freshness import SourceFreshness


@dataclass
class NextStepPlan:
    action: str
    reason: str
    category: str = "investigate"


def plan_best_next_step(
    *,
    service_name: str,
    root_category: str,
    logs_freshness: SourceFreshness,
    events_freshness: SourceFreshness,
    inventory_freshness: SourceFreshness,
    low_signal_logs: bool,
    conflicts: ConflictReport,
    events_available: bool,
) -> NextStepPlan:
    name = service_name or "service"

    if inventory_freshness.freshness == "stale":
        return NextStepPlan(
            action="Refresh provider-wide Railway inventory and re-check current service status.",
            reason="Cached provider inventory is stale.",
            category="refresh_inventory",
        )

    if conflicts.has_conflicts and any(c.kind == "success_event_vs_failed_status" for c in conflicts.conflicts):
        return NextStepPlan(
            action=f"Refresh Railway service events and fetch logs around the latest failed deployment window for {name}.",
            reason="Current status contradicts the latest success event.",
            category="refresh_truth",
        )

    if root_category == "missing_env_variable":
        return NextStepPlan(
            action=f"Prepare a governed env-variable fix plan for {name} after confirming the missing variable in Railway settings.",
            reason="Logs indicate missing required configuration.",
            category="env_fix_plan",
        )

    if root_category == "resource_pressure":
        return NextStepPlan(
            action=f"Check memory/resource metrics for {name} before recommending restart or redeploy.",
            reason="Evidence suggests resource pressure.",
            category="resource_metrics",
        )

    if root_category == "crash_loop":
        return NextStepPlan(
            action=f"Fetch runtime logs immediately before process exit for {name} and inspect Railway service events.",
            reason="Crash-loop pattern detected.",
            category="pre_exit_logs",
        )

    if low_signal_logs and events_freshness.freshness in {"stale", "unknown"}:
        return NextStepPlan(
            action=f"Refresh Railway service events and fetch logs around the latest failed deployment window for {name}.",
            reason="Logs are fresh but low-signal and service events are stale or missing.",
            category="refresh_events_log_window",
        )

    if root_category == "database_startup_or_storage_activity":
        return NextStepPlan(
            action=f"Refresh Railway service events and fetch logs around the latest failed deployment window for {name}.",
            reason="Database logs only show storage-engine activity without a definitive fatal error.",
            category="refresh_events_log_window",
        )

    if not events_available or events_freshness.freshness in {"stale", "unknown"}:
        return NextStepPlan(
            action=(
                "Investigate by refreshing Railway service events and fetching deployment/runtime logs "
                f"near the failure timestamp for {name}."
            ),
            reason="Event evidence is missing or stale for the current failure.",
            category="refresh_events",
        )

    if logs_freshness.freshness in {"stale", "unknown"}:
        return NextStepPlan(
            action=f"Fetch fresh runtime logs for {name} around the current failure window.",
            reason="Available logs are not recent enough to explain the current state.",
            category="refresh_logs",
        )

    return NextStepPlan(
        action=f"Inspect surrounding logs and Railway service events for {name} before proposing mutation.",
        reason="Evidence is present but not yet strong enough for a fix action.",
        category="investigate",
    )

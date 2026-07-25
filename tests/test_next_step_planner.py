# SPDX-License-Identifier: Apache-2.0
"""Next-step action planner tests."""

from __future__ import annotations

from aethos_core.evidence_correlation.evidence_conflict_detector import ConflictReport, EvidenceConflict
from aethos_core.evidence_correlation.evidence_freshness import SourceFreshness
from aethos_core.evidence_correlation.next_step_planner import plan_best_next_step


def _fresh(source: str) -> SourceFreshness:
    return SourceFreshness(source=source, freshness="fresh")


def _stale(source: str) -> SourceFreshness:
    return SourceFreshness(source=source, freshness="stale")


def test_wiredtiger_only_stale_events_refresh_events_and_log_window():
    step = plan_best_next_step(
        service_name="MongoDB",
        root_category="database_startup_or_storage_activity",
        logs_freshness=_fresh("runtime_logs"),
        events_freshness=_stale("service_events"),
        inventory_freshness=_fresh("provider_inventory"),
        low_signal_logs=True,
        conflicts=ConflictReport(),
        events_available=True,
    )
    assert step.category == "refresh_events_log_window"
    assert "Refresh Railway service events" in step.action


def test_crash_loop_fetch_pre_exit_logs():
    step = plan_best_next_step(
        service_name="worker",
        root_category="crash_loop",
        logs_freshness=_fresh("runtime_logs"),
        events_freshness=_fresh("service_events"),
        inventory_freshness=_fresh("provider_inventory"),
        low_signal_logs=False,
        conflicts=ConflictReport(),
        events_available=True,
    )
    assert step.category == "pre_exit_logs"
    assert "before process exit" in step.action


def test_missing_env_suggests_env_fix_plan():
    step = plan_best_next_step(
        service_name="api",
        root_category="missing_env_variable",
        logs_freshness=_fresh("runtime_logs"),
        events_freshness=_fresh("service_events"),
        inventory_freshness=_fresh("provider_inventory"),
        low_signal_logs=False,
        conflicts=ConflictReport(),
        events_available=True,
    )
    assert step.category == "env_fix_plan"
    assert "env-variable fix plan" in step.action


def test_oom_suggests_resource_metrics():
    step = plan_best_next_step(
        service_name="worker",
        root_category="resource_pressure",
        logs_freshness=_fresh("runtime_logs"),
        events_freshness=_fresh("service_events"),
        inventory_freshness=_fresh("provider_inventory"),
        low_signal_logs=False,
        conflicts=ConflictReport(),
        events_available=True,
    )
    assert step.category == "resource_metrics"
    assert "memory/resource metrics" in step.action


def test_conflicting_evidence_refresh_truth():
    conflicts = ConflictReport(
        conflicts=[
            EvidenceConflict(
                kind="success_event_vs_failed_status",
                summary="Latest service event shows success while current status remains failed.",
            )
        ]
    )
    step = plan_best_next_step(
        service_name="MongoDB",
        root_category="database_startup_or_storage_activity",
        logs_freshness=_fresh("runtime_logs"),
        events_freshness=_stale("service_events"),
        inventory_freshness=_fresh("provider_inventory"),
        low_signal_logs=True,
        conflicts=conflicts,
        events_available=True,
    )
    assert step.category == "refresh_truth"
    assert "Refresh Railway service events" in step.action

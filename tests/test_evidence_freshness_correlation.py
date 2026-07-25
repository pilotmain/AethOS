# SPDX-License-Identifier: Apache-2.0
"""Evidence freshness correlation tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from aethos_core.evidence_correlation.correlated_diagnosis import correlate_evidence
from aethos_core.evidence_correlation.evidence_freshness import (
    assess_event_freshness,
    assess_log_freshness,
)
from aethos_core.failed_service_investigation.failed_service_diagnosis import compose_diagnosis_reply
from aethos_core.failed_service_investigation.failed_service_resolver import ResolvedFailedService


NOW = datetime(2026, 5, 25, 12, 0, 0, tzinfo=UTC)


def _mongo_evidence(*, logs: list[dict], events: list[dict]) -> dict:
    return {
        "target": {
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "deployment_state": "failed",
        },
        "target_label": "pilotcore-sales-engine / production / MongoDB",
        "status": "failed",
        "deployment_state": "failed",
        "health": "failed",
        "logs": logs,
        "logs_available": bool(logs),
        "events": events,
        "events_available": bool(events),
        "root_cause": {
            "category": "database_startup_or_storage_activity",
            "label": "Database startup or storage activity",
            "confidence": "medium",
            "summary": "Database startup/storage activity without a clear fatal error",
            "bounded_diagnosis": True,
            "suggests_mutation": False,
            "evidence_gaps": ["Available logs only show startup/storage activity, not a definitive fatal error line"],
        },
    }


def test_fresh_logs_and_stale_events_produce_bounded_diagnosis():
    evidence = _mongo_evidence(
        logs=[{"timestamp": (NOW - timedelta(minutes=5)).isoformat(), "message": "WiredTiger recovery checkpoint"}],
        events=[{"created_at": "2026-04-01T10:00:00+00:00", "state": "FAILED", "message": "Deployment dep-old state=FAILED"}],
    )
    correlated = correlate_evidence(evidence, reference_time=NOW)
    assert correlated.freshness["runtime_logs"] == "fresh"
    assert correlated.freshness["service_events"] == "stale"
    assert "unconfirmed" in correlated.conclusion.lower() or "still unconfirmed" in correlated.conclusion.lower()
    assert "Refresh Railway service events" in correlated.best_next_step


def test_fresh_logs_and_fresh_failed_event_increase_confidence_note():
    evidence = _mongo_evidence(
        logs=[{"timestamp": (NOW - timedelta(minutes=3)).isoformat(), "message": "process exited with code 1"}],
        events=[{"created_at": (NOW - timedelta(hours=2)).isoformat(), "state": "FAILED", "message": "Deployment dep-new state=FAILED"}],
    )
    evidence["root_cause"] = {
        "category": "crash_loop",
        "label": "Crash loop",
        "confidence": "medium",
        "summary": "Crash loop",
        "bounded_diagnosis": False,
        "suggests_mutation": False,
    }
    correlated = correlate_evidence(evidence, reference_time=NOW)
    assert correlated.freshness["runtime_logs"] == "fresh"
    assert correlated.freshness["service_events"] == "fresh"
    assert "align" in correlated.confidence_note.lower() or "stronger" in correlated.confidence_note.lower()


def test_success_event_with_failed_status_flags_conflict():
    evidence = _mongo_evidence(
        logs=[{"timestamp": (NOW - timedelta(minutes=4)).isoformat(), "message": "WiredTiger message"}],
        events=[
            {"created_at": "2026-04-01T09:00:00+00:00", "state": "FAILED", "message": "Deployment dep-fail state=FAILED"},
            {"created_at": "2026-04-01T10:00:00+00:00", "state": "SUCCESS", "message": "Deployment dep-ok state=SUCCESS"},
        ],
    )
    correlated = correlate_evidence(evidence, reference_time=NOW)
    assert any("success" in conflict.lower() for conflict in correlated.conflicts)
    assert "Refresh Railway service events" in correlated.best_next_step


def test_stale_inventory_recommends_refresh():
    from aethos_core.evidence_correlation.next_step_planner import plan_best_next_step
    from aethos_core.evidence_correlation.evidence_conflict_detector import ConflictReport
    from aethos_core.evidence_correlation.evidence_freshness import SourceFreshness

    step = plan_best_next_step(
        service_name="MongoDB",
        root_category="database_startup_or_storage_activity",
        logs_freshness=SourceFreshness(source="runtime_logs", freshness="fresh"),
        events_freshness=SourceFreshness(source="service_events", freshness="stale"),
        inventory_freshness=SourceFreshness(source="provider_inventory", freshness="stale"),
        low_signal_logs=True,
        conflicts=ConflictReport(),
        events_available=True,
    )
    assert "Refresh provider-wide Railway inventory" in step.action


def test_diagnosis_reply_includes_evidence_correlation_section():
    evidence = _mongo_evidence(
        logs=[{"timestamp": (NOW - timedelta(minutes=5)).isoformat(), "message": "WiredTiger message"}],
        events=[{"created_at": "2026-04-01T10:00:00+00:00", "state": "FAILED", "message": "Deployment dep-old state=FAILED"}],
    )
    evidence["evidence_correlation"] = correlate_evidence(evidence, reference_time=NOW).to_dict()
    body = compose_diagnosis_reply(evidence)
    assert "Evidence correlation:" in body
    assert "Best next step:" in body
    assert "No mutation recommended yet." in body


def test_assess_log_and_event_freshness_helpers():
    logs = [{"timestamp": (NOW - timedelta(minutes=10)).isoformat(), "message": "line"}]
    events = [{"created_at": (NOW - timedelta(days=2)).isoformat(), "state": "FAILED"}]
    assert assess_log_freshness(logs, reference_time=NOW).freshness == "fresh"
    assert assess_event_freshness(events, reference_time=NOW).freshness == "stale"

# SPDX-License-Identifier: Apache-2.0
"""Hypothesis and confidence evolution tests."""

from __future__ import annotations

import pytest

from aethos_core.world_model.confidence_tracker import confidence_label, score_from_evidence
from aethos_core.world_model.hypothesis_graph import evolve_hypotheses, leading_hypothesis
from aethos_core.world_model.investigation_engine import update_investigation_from_evidence
from aethos_core.world_model.investigation_state import Hypothesis, InvestigationState
from aethos_core.world_model.world_state_store import clear_world_model_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_world_model_for_tests()
    yield
    clear_world_model_for_tests()


def _row() -> dict:
    return {
        "service": "MongoDB",
        "project": "pilotcore-sales-engine",
        "environment": "production",
        "status": "failed",
    }


def _evidence(*, category: str, confidence: str, logs: list[dict], events_freshness: str) -> dict:
    return {
        "target": _row(),
        "provider": "railway",
        "status": "failed",
        "deployment_state": "failed",
        "logs_available": True,
        "events_available": True,
        "logs": logs,
        "root_cause": {"category": category, "confidence": confidence, "bounded_diagnosis": category.endswith("storage_activity")},
        "evidence_correlation": {"freshness": {"runtime_logs": "fresh", "service_events": events_freshness}},
    }


def test_wiredtiger_only_starts_bounded_confidence():
    evidence = _evidence(
        category="database_startup_or_storage_activity",
        confidence="low",
        logs=[{"message": "WiredTiger recovery checkpoint"}],
        events_freshness="stale",
    )
    state = update_investigation_from_evidence(
        session_id="hc-bounded",
        evidence=evidence,
        investigation_kind="why_failed",
    )
    assert state.confidence_label in {"weak", "bounded"}
    leading = leading_hypothesis(state)
    assert leading is not None
    assert leading.type == "storage_startup_issue"
    assert leading.confidence <= 0.62


def test_exit_code_and_disk_issue_increases_confidence():
    initial = _evidence(
        category="database_startup_or_storage_activity",
        confidence="low",
        logs=[{"message": "WiredTiger recovery checkpoint"}],
        events_freshness="stale",
    )
    update_investigation_from_evidence(session_id="hc-grow", evidence=initial, investigation_kind="why_failed")

    stronger = _evidence(
        category="database_storage_issue",
        confidence="high",
        logs=[{"message": "fatal disk corrupt exit code 137"}],
        events_freshness="fresh",
    )
    stronger["evidence_correlation"]["root_cause_confirmed"] = True
    state = update_investigation_from_evidence(
        session_id="hc-grow",
        evidence=stronger,
        investigation_kind="check_logs",
    )
    leading = leading_hypothesis(state)
    assert leading is not None
    assert leading.type == "storage_corruption_issue"
    assert state.confidence_score >= 0.7
    assert confidence_label(state.confidence_score) in {"likely", "strong"}


def test_stale_hypothesis_decays_when_new_hypothesis_leads():
    state = InvestigationState(
        target="pilotcore-sales-engine / production / MongoDB",
        session_id="hc-decay",
        service="MongoDB",
        hypotheses=[Hypothesis(type="storage_startup_issue", confidence=0.45, status="active", label="storage/startup issue")],
    )
    evolve_hypotheses(
        state,
        root_category="database_storage_issue",
        confidence_score=0.83,
        new_evidence=["high_signal_logs", "fresh_service_events"],
    )
    startup = next(item for item in state.hypotheses if item.type == "storage_startup_issue")
    storage = next(item for item in state.hypotheses if item.type == "storage_corruption_issue")
    assert storage.status == "active"
    assert storage.confidence >= 0.8
    assert startup.status == "decayed"


def test_stale_events_reduce_confidence_score():
    score = score_from_evidence(
        root={"confidence": "medium", "category": "database_startup_or_storage_activity"},
        correlation={"freshness": {"service_events": "stale"}},
        evidence_tags=["stale_service_events", "fresh_runtime_logs"],
    )
    assert score < 0.55
    assert confidence_label(score) == "bounded"

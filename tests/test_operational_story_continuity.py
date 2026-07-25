# SPDX-License-Identifier: Apache-2.0
"""Operational story continuity tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.failed_service_investigation.global_preemption import route_failed_service_intent
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.investigation_engine import update_investigation_from_evidence
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.operational_story import compose_continuation_intro, compose_investigation_recap
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()


def _rows() -> list[dict]:
    return [
        {
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
            "service_id": "svc-mongo",
        }
    ]


def _seed(session_id: str) -> None:
    rows = _rows()
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": rows, "counts": {"total": 1, "failed": 1}, "failures": rows, "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def _mock_logs():
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-25T11:55:00+00:00", "message": "WiredTiger message"}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    )


def _mock_events():
    return patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={
            "ok": True,
            "events": [{"created_at": "2026-04-01T10:00:00+00:00", "state": "FAILED"}],
        },
    )


def test_first_turn_does_not_prepend_continuation_story():
    _seed("story-first")
    with _mock_logs(), _mock_events():
        reply, intent, _meta = route_failed_service_intent("why is MongoDB failed?", session_id="story-first")
    assert intent == "failed_service_diagnosis"
    assert "Continuing the **MongoDB** investigation" not in reply


def test_second_turn_logs_use_continuation_intro():
    _seed("story-second")
    with _mock_logs(), _mock_events():
        route_failed_service_intent("why is MongoDB failed?", session_id="story-second")
    with _mock_logs(), _mock_events():
        reply, intent, _meta = route_failed_service_intent("show MongoDB logs", session_id="story-second")
    assert intent == "failed_service_logs"
    assert "Continuing the **MongoDB** investigation" in reply


def test_recap_narrates_operational_understanding():
    state = InvestigationState(
        target="pilotcore-sales-engine / production / MongoDB",
        session_id="story-recap",
        service="MongoDB",
        confidence_score=0.55,
        confidence_label="bounded",
        evidence=["failed_runtime_status", "fresh_wiredtiger_logs", "stale_service_events"],
        missing_evidence=["recent_failure_events", "exit_code", "storage-volume health"],
        next_best_action="Refresh Railway service events and inspect logs around the latest failure window.",
    )
    from aethos_core.world_model.hypothesis_graph import evolve_hypotheses

    evolve_hypotheses(
        state,
        root_category="database_startup_or_storage_activity",
        confidence_score=0.55,
        new_evidence=["fresh_wiredtiger_logs"],
    )
    recap = compose_investigation_recap(state)
    assert "We're still investigating the **MongoDB** failure." in recap
    assert "Runtime logs are fresh" in recap
    assert "Service events are stale" in recap
    assert "No fatal database/runtime error has been observed yet." in recap
    assert "storage/startup issue" in recap
    assert "recent_failure_events" in recap or "exit_code" in recap


def test_continuation_intro_varies_by_action():
    state = InvestigationState(target="pilotcore-sales-engine / production / MongoDB", service="MongoDB")
    assert "latest logs" in compose_continuation_intro(state, action="logs")
    assert "service events" in compose_continuation_intro(state, action="events")
    assert "still investigating" in compose_continuation_intro(state, action="diagnosis")


def test_what_changed_uses_world_model_followup():
    row = _rows()[0]
    target = target_label_from_row(row)
    state = InvestigationState(
        target=target,
        session_id="story-changed",
        service="MongoDB",
        evidence=["failed_runtime_status"],
        meta={"previous_evidence": ["failed_runtime_status"]},
    )
    save_investigation_state(state)
    evidence = {
        "target": row,
        "provider": "railway",
        "status": "failed",
        "logs_available": True,
        "events_available": True,
        "logs": [{"message": "WiredTiger message"}],
        "root_cause": {"category": "database_startup_or_storage_activity", "confidence": "low"},
        "evidence_correlation": {"freshness": {"runtime_logs": "fresh", "service_events": "stale"}},
    }
    update_investigation_from_evidence(
        session_id="story-changed",
        evidence=evidence,
        investigation_kind="check_logs",
    )
    reply, intent, _meta = route_failed_service_intent("what changed?", session_id="story-changed")
    assert intent == "world_model_what_changed"
    assert "New evidence since the last turn:" in reply

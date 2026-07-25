# SPDX-License-Identifier: Apache-2.0
"""World-model investigation state tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.failed_service_investigation.global_preemption import route_failed_service_intent
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.investigation_engine import update_investigation_from_evidence
from aethos_core.world_model.investigation_state import target_label_from_row
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, load_investigation_state


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


def _mock_logs(*, message: str = "WiredTiger message"):
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-25T11:55:00+00:00", "message": message}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    )


def _mock_events(*, created_at: str = "2026-04-01T10:00:00+00:00"):
    return patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={
            "ok": True,
            "events": [{"created_at": created_at, "state": "FAILED", "message": "Deployment dep-old state=FAILED"}],
        },
    )


def test_initial_investigation_creates_persistent_state():
    _seed("wm-init")
    with _mock_logs(), _mock_events():
        reply, intent, meta = route_failed_service_intent("why is MongoDB failed?", session_id="wm-init")

    assert intent == "failed_service_diagnosis"
    assert meta.get("world_model_active") == "true"
    target = target_label_from_row(_rows()[0])
    state = load_investigation_state(session_id="wm-init", target=target)
    assert state is not None
    assert state.active_investigation is True
    assert "failed_runtime_status" in state.evidence
    assert state.completed_checks == ["why_failed"]
    assert len(state.timeline) == 1


def test_followup_show_logs_extends_same_investigation():
    _seed("wm-logs")
    with _mock_logs(), _mock_events():
        route_failed_service_intent("why is MongoDB failed?", session_id="wm-logs")
    with _mock_logs(message="WiredTiger recovery checkpoint"), _mock_events():
        reply, intent, meta = route_failed_service_intent("show MongoDB logs", session_id="wm-logs")

    assert intent == "failed_service_logs"
    assert meta.get("world_model_active") == "true"
    target = target_label_from_row(_rows()[0])
    state = load_investigation_state(session_id="wm-logs", target=target)
    assert state is not None
    assert "check_logs" in state.completed_checks
    assert len(state.timeline) >= 2
    assert "Continuing the **MongoDB** investigation" in reply


def test_what_do_we_know_returns_world_model_recap():
    _seed("wm-recap")
    with _mock_logs(), _mock_events():
        route_failed_service_intent("why is MongoDB failed?", session_id="wm-recap")

    reply, intent, meta = route_failed_service_intent(
        "what do we know so far about MongoDB?", session_id="wm-recap"
    )
    assert intent == "world_model_investigation_recap"
    assert meta.get("active_investigation") == "true"
    assert "We're investigating the failed **MongoDB** service" in reply
    assert "Current hypothesis:" in reply
    assert "Best next step:" in reply


def test_evidence_accumulation_merges_tags():
    row = _rows()[0]
    target = target_label_from_row(row)
    base = {
        "target": row,
        "provider": "railway",
        "status": "failed",
        "deployment_state": "failed",
        "logs_available": True,
        "events_available": True,
        "logs": [{"message": "WiredTiger message"}],
        "root_cause": {"category": "database_startup_or_storage_activity", "confidence": "low"},
        "evidence_correlation": {"freshness": {"runtime_logs": "fresh", "service_events": "stale"}},
    }
    update_investigation_from_evidence(
        session_id="wm-merge",
        evidence=base,
        investigation_kind="why_failed",
        operator_intent="why_failed",
    )
    enriched = dict(base)
    enriched["logs"] = [{"message": "process exited with code 137 disk corrupt fatal"}]
    enriched["root_cause"] = {"category": "database_storage_issue", "confidence": "high"}
    enriched["evidence_correlation"] = {
        "freshness": {"runtime_logs": "fresh", "service_events": "fresh"},
        "root_cause_confirmed": True,
    }
    state = update_investigation_from_evidence(
        session_id="wm-merge",
        evidence=enriched,
        investigation_kind="check_logs",
        operator_intent="show_logs",
    )
    assert "fresh_wiredtiger_logs" in state.evidence
    assert "high_signal_logs" in state.evidence
    assert state.confidence_score > 0.5

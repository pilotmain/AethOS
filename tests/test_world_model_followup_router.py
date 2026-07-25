# SPDX-License-Identifier: Apache-2.0
"""World-model follow-up router tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.post_mutation_verification.verification_intent_router import reset_pending_verification_for_tests
from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.repair_memory.repair_attempt_memory import reset_repair_memory_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.runtime.jobs import job_store
from aethos_core.world_model.investigation_engine import update_investigation_from_evidence
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.world_model_followup_router import (
    classify_world_model_followup,
    route_world_model_followup,
)
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    reset_repair_memory_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_operation_state_store_for_tests()
    reset_pending_verification_for_tests()
    job_store.clear_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    reset_repair_memory_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_operation_state_store_for_tests()
    reset_pending_verification_for_tests()
    job_store.clear_for_tests()


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


def _seed_state(session_id: str) -> InvestigationState:
    row = _rows()[0]
    state = InvestigationState(
        target=target_label_from_row(row),
        session_id=session_id,
        service="MongoDB",
        project="pilotcore-sales-engine",
        environment="production",
        confidence_score=0.55,
        confidence_label="bounded",
        active_investigation=True,
        evidence=["failed_runtime_status", "fresh_wiredtiger_logs", "stale_service_events"],
        missing_evidence=["recent_failure_events", "exit_code", "storage-volume health"],
        next_best_action="Refresh Railway service events and fetch logs around the latest failed deployment window.",
    )
    from aethos_core.world_model.hypothesis_graph import evolve_hypotheses

    evolve_hypotheses(
        state,
        root_category="database_startup_or_storage_activity",
        confidence_score=0.55,
        new_evidence=["fresh_wiredtiger_logs"],
    )
    save_investigation_state(state)
    return state


def test_classify_world_model_followup_intents():
    assert classify_world_model_followup("what do we know so far about MongoDB?") == "recap"
    assert classify_world_model_followup("what should we do next?") == "next_step"
    assert classify_world_model_followup("is restart safe?") == "safety_check"
    assert classify_world_model_followup("should we redeploy MongoDB?") == "safety_check"
    assert classify_world_model_followup("what changed?") == "evidence_delta"
    assert classify_world_model_followup("what evidence are we missing?") == "missing_evidence"


def test_what_do_we_know_returns_recap():
    _seed("wm-router-recap")
    _seed_state("wm-router-recap")
    reply, intent, meta = route_world_model_followup(
        "what do we know so far about MongoDB?", session_id="wm-router-recap"
    )
    assert intent == "world_model_investigation_recap"
    assert "MongoDB" in reply
    assert "Current understanding:" in reply
    assert "No mutation is recommended yet." in reply
    assert meta.get("route_id") == "world_model_investigation"


def test_what_should_we_do_next_returns_next_step():
    _seed("wm-router-next")
    _seed_state("wm-router-next")
    reply, intent, _meta = route_world_model_followup("what should we do next?", session_id="wm-router-next")
    assert intent == "world_model_next_action"
    assert reply.startswith("Best next step:")
    assert "Reason:" in reply


def test_is_restart_safe_returns_safety_check():
    _seed("wm-router-safe")
    _seed_state("wm-router-safe")
    reply, intent, meta = route_world_model_followup("is restart safe for MongoDB?", session_id="wm-router-safe")
    assert intent == "world_model_restart_safety"
    assert "Not yet." in reply
    assert "not recommended" in reply.lower()
    assert meta.get("blocked_routes")


def test_missing_evidence_followup():
    _seed("wm-router-missing")
    _seed_state("wm-router-missing")
    reply, intent, _meta = route_world_model_followup("what evidence are we missing?", session_id="wm-router-missing")
    assert intent == "world_model_missing_evidence"
    assert "exit_code" in reply or "recent_failure_events" in reply


def test_missing_state_bootstraps_from_known_service():
    _seed("wm-router-bootstrap")
    evidence = {
        "target": _rows()[0],
        "provider": "railway",
        "status": "failed",
        "deployment_state": "failed",
        "logs_available": True,
        "events_available": True,
        "logs": [{"message": "WiredTiger message"}],
        "root_cause": {"category": "database_startup_or_storage_activity", "confidence": "low"},
        "evidence_correlation": {"freshness": {"runtime_logs": "fresh", "service_events": "stale"}},
    }
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.collect_failed_service_evidence",
        return_value=evidence,
    ):
        reply, intent, _meta = route_world_model_followup(
            "what do we know so far about MongoDB?", session_id="wm-router-bootstrap"
        )
    assert intent == "world_model_investigation_recap"
    assert "MongoDB" in reply

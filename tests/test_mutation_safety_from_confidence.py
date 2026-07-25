# SPDX-License-Identifier: Apache-2.0
"""Mutation safety from world-model confidence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.failed_service_investigation.failed_service_fix_plan import compose_fix_plan_reply
from aethos_core.failed_service_investigation.failed_service_resolver import ResolvedFailedService
from aethos_core.failed_service_investigation.global_preemption import route_failed_service_intent
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.confidence_tracker import mutation_allowed
from aethos_core.world_model.investigation_engine import try_world_model_followup, update_investigation_from_evidence
from aethos_core.world_model.investigation_state import InvestigationState
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()


def _mongo_target() -> ResolvedFailedService:
    return ResolvedFailedService(
        row={
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
            "service_id": "svc-mongo",
        }
    )


def _seed(session_id: str) -> None:
    row = _mongo_target().row
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": [row], "counts": {"total": 1, "failed": 1}, "failures": [row], "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def _weak_state() -> InvestigationState:
    state = InvestigationState(
        target="pilotcore-sales-engine / production / MongoDB",
        session_id="mut-weak",
        service="MongoDB",
        confidence_score=0.42,
        confidence_label="bounded",
        next_best_action="Refresh Railway service events and inspect logs around the latest failure window.",
    )
    save_investigation_state(state)
    return state


def test_mutation_allowed_blocks_weak_confidence():
    assert mutation_allowed(0.42, root={"suggests_mutation": True}) is False
    assert mutation_allowed(0.75, root={"suggests_mutation": True, "bounded_diagnosis": True}) is False
    assert mutation_allowed(0.85, root={"suggests_mutation": True}) is True


def test_restart_blocked_under_weak_confidence():
    _weak_state()
    result = try_world_model_followup("is restart safe for MongoDB?", session_id="mut-weak")
    assert result is not None
    body, intent, meta = result
    assert intent == "world_model_restart_safety"
    assert "not recommended" in body.lower()
    assert meta["confidence_score"] == "0.42"


def test_fix_plan_blocks_restart_when_confidence_low():
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-25T11:55:00+00:00", "message": "WiredTiger message"}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": True, "events": [{"created_at": "2026-04-01T10:00:00+00:00", "state": "FAILED"}]},
    ):
        body, plan = compose_fix_plan_reply(_mongo_target(), session_id="mut-fix")

    assert "Do **not** restart/redeploy yet" in body
    assert plan.get("proposed_operation") is None
    assert plan.get("ok") is False
    assert plan.get("confidence_score", 1.0) < 0.6


def test_high_confidence_missing_env_allows_governed_fix_plan():
    row = _mongo_target().row
    evidence = {
        "target": row,
        "provider": "railway",
        "status": "failed",
        "deployment_state": "crashed",
        "logs_available": True,
        "events_available": True,
        "logs": [{"message": "Missing required env DATABASE_URL exit code 1"}],
        "root_cause": {
            "category": "missing_env_variable",
            "confidence": "high",
            "suggests_mutation": True,
            "suggested_operation": "redeploy",
            "next_checks": ["Verify env vars in Railway dashboard"],
        },
        "evidence_correlation": {
            "freshness": {"runtime_logs": "fresh", "service_events": "fresh"},
            "root_cause_confirmed": True,
        },
    }
    state = update_investigation_from_evidence(
        session_id="mut-strong",
        evidence=evidence,
        investigation_kind="fix_plan",
        operator_intent="create_fix_plan",
    )
    assert state.confidence_score >= 0.6
    assert mutation_allowed(state.confidence_score, root=evidence["root_cause"]) is True


def test_what_next_routes_with_active_investigation():
    _seed("mut-next")
    _weak_state()
    reply, intent, meta = route_failed_service_intent("what should we do next for MongoDB?", session_id="mut-weak")
    assert intent == "world_model_next_action"
    assert "Best next step" in reply
    assert meta.get("active_investigation") == "true"

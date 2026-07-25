# SPDX-License-Identifier: Apache-2.0
"""Safety question route ownership tests."""

from __future__ import annotations

import pytest

from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent
from aethos_core.chat.route_trace import clear_route_traces_for_tests, get_last_route_trace
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.safety_question_classifier import is_safety_question
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    clear_route_traces_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    clear_route_traces_for_tests()


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


def _seed_state(session_id: str) -> None:
    row = _rows()[0]
    save_investigation_state(
        InvestigationState(
            target=target_label_from_row(row),
            session_id=session_id,
            service="MongoDB",
            project="pilotcore-sales-engine",
            environment="production",
            confidence_score=0.42,
            confidence_label="bounded",
            active_investigation=True,
            evidence=["failed_runtime_status", "fresh_wiredtiger_logs", "stale_service_events"],
            next_best_action="Refresh Railway service events and inspect logs around the latest failure window.",
        )
    )


def test_is_restart_safe_is_safety_question():
    assert is_safety_question("is restart safe?")
    assert is_safety_question("can we safely restart MongoDB?")


def test_is_restart_safe_routes_to_world_model_safety_check():
    _seed("wm-safety-route")
    _seed_state("wm-safety-route")
    result = resolve_chat_turn("is restart safe?", session_id="wm-safety-route", apply_relational_layer=False)
    assert result.intent == "world_model_restart_safety"
    assert detect_explicit_mutation_intent("is restart safe?", session_id="wm-safety-route") is None


def test_should_we_restart_mongodb_no_preflight():
    _seed("wm-safety-should")
    _seed_state("wm-safety-should")
    result = resolve_chat_turn("should we restart MongoDB?", session_id="wm-safety-should", apply_relational_layer=False)
    assert result.intent == "world_model_restart_safety"
    assert result.intent != "mutation_preflight_job_created"


def test_restart_mongodb_still_explicit_mutation():
    _seed("wm-safety-command")
    _seed_state("wm-safety-command")
    intent = detect_explicit_mutation_intent("restart MongoDB", session_id="wm-safety-command")
    assert intent is not None
    assert intent.operation == "restart"
    result = resolve_chat_turn("restart MongoDB", session_id="wm-safety-command", apply_relational_layer=False)
    assert result.intent == "mutation_preflight_job_created"


def test_route_trace_shows_world_model_after_safety_question():
    _seed("wm-safety-trace")
    _seed_state("wm-safety-trace")
    resolve_chat_turn("is restart safe for MongoDB?", session_id="wm-safety-trace", apply_relational_layer=False)
    trace = get_last_route_trace(session_id="wm-safety-trace")
    assert trace is not None
    assert trace.get("route_id") == "world_model_investigation"
    assert "world_model" in str(trace.get("intent") or "")

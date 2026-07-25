# SPDX-License-Identifier: Apache-2.0
"""World-model routing priority over mutation preflight."""

from __future__ import annotations

import pytest

from aethos_core.chat.explicit_mutation_intent import (
    compose_explicit_mutation_preflight_reply,
    detect_explicit_mutation_intent,
    has_explicit_mutation_verb,
)
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
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


def test_is_restart_safe_does_not_create_mutation_preflight():
    _seed("wm-priority-safe")
    _seed_state("wm-priority-safe")
    assert detect_explicit_mutation_intent("is restart safe for MongoDB?", session_id="wm-priority-safe") is None
    assert compose_explicit_mutation_preflight_reply("is restart safe for MongoDB?", session_id="wm-priority-safe") is None
    result = resolve_chat_turn("is restart safe for MongoDB?", session_id="wm-priority-safe", apply_relational_layer=False)
    assert result.intent == "world_model_restart_safety"
    assert result.intent != "mutation_preflight_job_created"


def test_should_we_restart_mongodb_does_not_create_mutation_preflight():
    _seed("wm-priority-should")
    _seed_state("wm-priority-should")
    assert has_explicit_mutation_verb("should we restart MongoDB?") is False
    result = resolve_chat_turn("should we restart MongoDB?", session_id="wm-priority-should", apply_relational_layer=False)
    assert result.intent == "world_model_restart_safety"


def test_restart_mongodb_still_creates_governed_preflight():
    _seed("wm-priority-command")
    _seed_state("wm-priority-command")
    intent = detect_explicit_mutation_intent("restart MongoDB", session_id="wm-priority-command")
    assert intent is not None
    assert intent.operation == "restart"
    assert intent.confidence >= 0.75


def test_safety_questions_route_before_mutation_verbs():
    _seed("wm-priority-order")
    _seed_state("wm-priority-order")
    result = resolve_chat_turn("what do we know so far about MongoDB?", session_id="wm-priority-order", apply_relational_layer=False)
    assert result.intent == "world_model_investigation_recap"
    assert result.meta.get("route_id") == "world_model_investigation"
    assert "connection dropped" not in result.reply.lower()

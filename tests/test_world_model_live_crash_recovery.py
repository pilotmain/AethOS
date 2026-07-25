# SPDX-License-Identifier: Apache-2.0
"""Live crash recovery tests for world-model recall transport."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.api.routes.chat import _to_out
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
            confidence_score=0.55,
            confidence_label="bounded",
            active_investigation=True,
            evidence=["failed_runtime_status", "fresh_wiredtiger_logs", "stale_service_events"],
            next_best_action="Refresh Railway service events and fetch logs around the latest failed deployment window.",
        )
    )


@pytest.mark.parametrize(
    "query",
    [
        "what do we know so far about MongoDB?",
        "what should we do next?",
        "is restart safe?",
    ],
)
def test_world_model_recall_cannot_crash_transport(query: str):
    _seed("wm-live-transport")
    _seed_state("wm-live-transport")
    result = resolve_chat_turn(query, session_id="wm-live-transport", apply_relational_layer=False)
    out = _to_out(result)
    assert out.reply
    assert out.intent.startswith("world_model_")
    assert "connection dropped" not in out.reply.lower()


@pytest.mark.parametrize(
    "query,intent",
    [
        ("what do we know so far about MongoDB?", "world_model_investigation_recap"),
        ("what should we do next?", "world_model_next_action"),
        ("is restart safe?", "world_model_restart_safety"),
    ],
)
def test_cognition_pipeline_failure_still_returns_bounded_answer(query: str, intent: str):
    _seed("wm-live-crash")
    _seed_state("wm-live-crash")
    with patch(
        "aethos_core.conversation.continuity_synthesis.naturalize_operational_reply",
        side_effect=RuntimeError("naturalization failed"),
    ), patch(
        "aethos_core.chat.service._finalize_result",
        side_effect=RuntimeError("finalization failed"),
    ):
        result = resolve_chat_turn(query, session_id="wm-live-crash", apply_relational_layer=False)
    out = _to_out(result)
    assert out.intent in {intent, "world_model_investigation_recap", "world_model_next_action", "world_model_restart_safety", "cognition_exception_fallback"}
    assert "Diagnostic ID: cogerr-" in out.reply or "MongoDB" in out.reply
    assert "connection dropped" not in out.reply.lower()


def test_show_route_trace_does_not_crash_transport():
    _seed("wm-live-trace")
    _seed_state("wm-live-trace")
    result = resolve_chat_turn("show route trace", session_id="wm-live-trace", apply_relational_layer=False)
    out = _to_out(result)
    assert out.reply
    assert "connection dropped" not in out.reply.lower()

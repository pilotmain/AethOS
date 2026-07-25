# SPDX-License-Identifier: Apache-2.0
"""World-model route exception isolation tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.safe_world_model_runtime import safe_route_world_model_followup
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


def test_route_exception_returns_safe_fallback():
    _seed("wm-iso-route")
    _seed_state("wm-iso-route")
    with patch(
        "aethos_core.world_model.safe_world_model_runtime.safe_recover_or_rebuild_investigation",
        side_effect=RuntimeError("boom"),
    ):
        reply, intent, meta = safe_route_world_model_followup(
            "what do we know so far about MongoDB?", session_id="wm-iso-route"
        )
    assert intent == "world_model_investigation_recap"
    assert meta.get("recovered") == "true"
    assert meta.get("fallback_used") == "exception_isolation"
    assert meta.get("error_type") == "RuntimeError"
    assert "connection dropped" not in reply.lower()


def test_chat_layer_never_returns_api_dropped_for_world_model_recall():
    _seed("wm-iso-chat")
    _seed_state("wm-iso-chat")
    with patch(
        "aethos_core.world_model.safe_world_model_runtime._safe_compose_followup_reply",
        side_effect=Exception("compose crash"),
    ):
        for query in (
            "what do we know so far about MongoDB?",
            "what should we do next?",
            "is restart safe?",
        ):
            result = resolve_chat_turn(query, session_id="wm-iso-chat", apply_relational_layer=False)
            assert result.intent.startswith("world_model_")
            assert result.used_llm is False
            assert "connection dropped" not in result.reply.lower()


def test_restart_mongodb_still_uses_governed_preflight():
    _seed("wm-iso-restart")
    _seed_state("wm-iso-restart")
    result = resolve_chat_turn("restart MongoDB", session_id="wm-iso-restart", apply_relational_layer=False)
    assert result.intent == "mutation_preflight_job_created"

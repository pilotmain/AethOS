# SPDX-License-Identifier: Apache-2.0
"""World-model API resilience tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.world_model_followup_router import route_world_model_followup
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
            missing_evidence=["recent_failure_events", "exit_code"],
            next_best_action="Refresh Railway service events and inspect logs around the latest failure window.",
        )
    )


def test_memory_load_failure_returns_partial_recap():
    _seed("wm-res-partial")
    with patch(
        "aethos_core.world_model.world_model_followup_router._bootstrap_investigation_from_row",
        return_value=(None, ["railway logs unavailable"]),
    ):
        reply, intent, meta = route_world_model_followup(
            "what do we know so far about MongoDB?", session_id="wm-res-partial"
        )
    assert intent == "world_model_investigation_recap"
    assert "MongoDB" in reply
    assert "one evidence source failed to load" in reply
    assert meta.get("world_model_degraded") == "true"
    assert "connection dropped" not in reply.lower()


def test_missing_state_known_service_fallback_discovery():
    _seed("wm-res-fallback")
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
        result = resolve_chat_turn(
            "what do we know so far about MongoDB?",
            session_id="wm-res-fallback",
            apply_relational_layer=False,
        )
    assert result.intent == "world_model_investigation_recap"
    assert result.used_llm is False
    assert "connection dropped" not in result.reply.lower()
    assert "MongoDB" in result.reply


def test_chat_recall_does_not_surface_api_drop_message():
    _seed("wm-res-chat")
    _seed_state("wm-res-chat")
    result = resolve_chat_turn(
        "what should we do next for MongoDB?",
        session_id="wm-res-chat",
        apply_relational_layer=False,
    )
    assert result.intent == "world_model_next_action"
    assert result.used_llm is False
    assert "connection dropped" not in result.reply.lower()

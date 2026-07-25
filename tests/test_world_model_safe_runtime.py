# SPDX-License-Identifier: Apache-2.0
"""Safe world-model runtime tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.safe_world_model_runtime import (
    compose_world_model_error_fallback,
    safe_load_investigation_state,
    safe_route_world_model_followup,
)
from aethos_core.world_model.world_state_store import (
    _session_path,
    clear_world_model_for_tests,
    save_investigation_state,
)


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
        missing_evidence=["recent service events / exit code", "storage/volume health"],
        next_best_action="Refresh Railway service events and fetch logs around the latest failed deployment window.",
    )
    save_investigation_state(state)
    return state


def test_corrupt_state_file_returns_fallback_recap():
    _seed("wm-safe-corrupt")
    path = _session_path("wm-safe-corrupt")
    path.write_text("{not valid json", encoding="utf-8")
    reply, intent, meta = safe_route_world_model_followup(
        "what do we know so far about MongoDB?", session_id="wm-safe-corrupt"
    )
    assert intent == "world_model_investigation_recap"
    assert "MongoDB" in reply
    assert meta.get("recovered") == "true"
    assert meta.get("fallback_used") == "rebuild_from_health_report"
    assert "connection dropped" not in reply.lower()


def test_missing_state_rebuilds_from_health_report():
    _seed("wm-safe-rebuild")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.collect_failed_service_evidence",
        side_effect=RuntimeError("railway unavailable"),
    ):
        reply, intent, meta = safe_route_world_model_followup(
            "what do we know so far about MongoDB?", session_id="wm-safe-rebuild"
        )
    assert intent == "world_model_investigation_recap"
    assert "MongoDB" in reply
    assert meta.get("recovered") == "true"
    assert "connection dropped" not in reply.lower()


def test_evidence_source_failure_returns_partial_recap():
    _seed("wm-safe-partial")
    _seed_state("wm-safe-partial")
    with patch(
        "aethos_core.world_model.safe_world_model_runtime._safe_compose_followup_reply",
        side_effect=RuntimeError("compose failed"),
    ):
        reply, intent, meta = safe_route_world_model_followup(
            "what do we know so far about MongoDB?", session_id="wm-safe-partial"
        )
    assert intent == "world_model_investigation_recap"
    assert "MongoDB" in reply
    assert meta.get("world_model_degraded") == "true"
    assert "connection dropped" not in reply.lower()


def test_confidence_tracker_exception_uses_safety_fallback():
    _seed("wm-safe-confidence")
    _seed_state("wm-safe-confidence")
    with patch(
        "aethos_core.world_model.world_model_followup_router._compose_followup_reply",
        side_effect=ValueError("confidence tracker failed"),
    ):
        reply, intent, _meta = safe_route_world_model_followup("is restart safe?", session_id="wm-safe-confidence")
    assert intent == "world_model_restart_safety"
    assert "Not yet." in reply or "not recommended" in reply.lower()
    assert "connection dropped" not in reply.lower()


def test_safe_load_quarantines_corrupt_row():
    _seed("wm-safe-load")
    row = _rows()[0]
    target = target_label_from_row(row)
    path = _session_path("wm-safe-load")
    path.write_text(
        json.dumps({"investigations": [{"target": target, "hypotheses": "corrupt-not-a-list"}]}),
        encoding="utf-8",
    )
    state, error, quarantined = safe_load_investigation_state(session_id="wm-safe-load", target=target)
    assert state is None
    assert quarantined is True


def test_error_fallback_never_mentions_api_drop():
    body = compose_world_model_error_fallback(
        "state unavailable",
        partial_context={"intent": "recap", "row": _rows()[0]},
    )
    assert "MongoDB" in body
    assert "connection dropped" not in body.lower()

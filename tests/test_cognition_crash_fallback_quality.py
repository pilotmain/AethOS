# SPDX-License-Identifier: Apache-2.0
"""Cognition crash fallback quality tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.cognition_exception_boundary import (
    CognitionBoundaryContext,
    compose_cognition_crash_fallback,
)
from aethos_core.chat.route_trace import clear_route_traces_for_tests, get_last_route_trace
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.world_state_store import clear_world_model_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    clear_route_traces_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    clear_route_traces_for_tests()


def _seed(session_id: str) -> None:
    rows = [
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
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": rows, "counts": {"total": 1, "failed": 1}, "failures": rows, "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def test_fallback_includes_real_target():
    _seed("wm-fallback-quality")
    result = compose_cognition_crash_fallback(
        RuntimeError("boom"),
        CognitionBoundaryContext(
            text="what do we know so far about MongoDB?",
            session_id="wm-fallback-quality",
        ),
    )
    assert "pilotcore-sales-engine / production / MongoDB" in result.reply
    assert "the active service" not in result.reply.lower()


def test_fallback_includes_evidence_summary():
    _seed("wm-fallback-evidence")
    result = compose_cognition_crash_fallback(
        RuntimeError("boom"),
        CognitionBoundaryContext(
            text="what do we know so far about MongoDB?",
            session_id="wm-fallback-evidence",
        ),
    )
    assert "Recent evidence:" in result.reply
    assert "recent operational evidence" not in result.reply.lower()


def test_safety_fallback_uses_real_service():
    _seed("wm-fallback-safety")
    result = compose_cognition_crash_fallback(
        RuntimeError("boom"),
        CognitionBoundaryContext(text="is restart safe?", session_id="wm-fallback-safety"),
    )
    assert result.intent == "world_model_restart_safety"
    assert "MongoDB" in result.reply
    assert "Not yet." in result.reply


def test_route_trace_updated_after_fallback():
    _seed("wm-fallback-trace-update")
    compose_cognition_crash_fallback(
        RuntimeError("boom"),
        CognitionBoundaryContext(
            text="what should we do next for MongoDB?",
            session_id="wm-fallback-trace-update",
        ),
    )
    trace = get_last_route_trace(session_id="wm-fallback-trace-update")
    assert trace is not None
    assert trace.get("route_id") == "world_model_investigation"
    assert trace.get("fallback_used") == "cognition_crash_fallback"
    assert trace.get("recovered") == "true"


def test_boundary_fallback_on_master_route_crash():
    _seed("wm-fallback-boundary")
    from aethos_core.chat.cognition_exception_boundary import safe_resolve_operational_turn

    with patch(
        "aethos_core.chat.operational_master_router.resolve_operational_master_route",
        side_effect=RuntimeError("master route failed"),
    ):
        result = safe_resolve_operational_turn(
            "what do we know so far about MongoDB?",
            session_id="wm-fallback-boundary",
        )
    assert result is not None
    assert "MongoDB" in result.reply
    assert result.meta.get("route_id") == "world_model_investigation"
    assert "connection dropped" not in result.reply.lower()

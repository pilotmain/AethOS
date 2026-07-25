# SPDX-License-Identifier: Apache-2.0
"""Cognition exception boundary tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from unittest.mock import patch

import pytest

from aethos_core.chat.cognition_exception_boundary import (
    CognitionBoundaryContext,
    compose_cognition_crash_fallback,
    safe_finalize_chat_result,
    safe_record_route_trace,
    safe_resolve_operational_turn,
    sanitize_chat_result_for_transport,
)
from aethos_core.chat.service import ChatTurnResult
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.world_state_store import clear_world_model_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()


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


def test_cognition_graph_raises_returns_fallback_response():
    _seed("cog-boundary-route")
    context = CognitionBoundaryContext(
        text="what do we know so far about MongoDB?",
        session_id="cog-boundary-route",
    )
    with patch(
        "aethos_core.chat.operational_master_router.resolve_operational_master_route",
        side_effect=RuntimeError("cognition graph exploded"),
    ):
        result = safe_resolve_operational_turn(
            context.text,
            session_id=context.session_id,
        )
    assert result is not None
    assert result.intent == "world_model_investigation_recap"
    assert "MongoDB" in result.reply
    assert "Diagnostic ID: cogerr-" in result.reply
    assert result.meta.get("cognition_boundary") == "true"
    assert "connection dropped" not in result.reply.lower()


def test_finalizer_raises_returns_raw_or_fallback():
    _seed("cog-boundary-finalize")
    context = CognitionBoundaryContext(text="what should we do next?", session_id="cog-boundary-finalize")
    partial = ChatTurnResult(
        reply="Best next step:\nRefresh Railway service events.",
        intent="world_model_next_action",
        meta={"service": "MongoDB"},
    )
    with patch("aethos_core.chat.service._finalize_result", side_effect=ValueError("polish failed")):
        result = safe_finalize_chat_result(partial, context)
    assert "Refresh Railway service events" in result.reply
    assert "Diagnostic ID: cogerr-" in result.reply
    assert "connection dropped" not in result.reply.lower()


def test_route_trace_save_raises_response_still_returned():
    _seed("cog-boundary-trace")
    decision = type(
        "Decision",
        (),
        {
            "reply": "We're investigating MongoDB.",
            "intent": "world_model_investigation_recap",
            "meta": {"service": "MongoDB", "route_id": "world_model_investigation"},
        },
    )()
    with patch(
        "aethos_core.chat.operational_master_router.resolve_operational_master_route",
        return_value=decision,
    ), patch(
        "aethos_core.chat.operational_master_router.record_master_route_trace",
        side_effect=RuntimeError("trace save failed"),
    ), patch(
        "aethos_core.chat.service._finalize_result",
        side_effect=lambda result, emotional_context=None: result,
    ):
        result = safe_resolve_operational_turn(
            "what do we know so far about MongoDB?",
            session_id="cog-boundary-trace",
        )
    assert result is not None
    assert "MongoDB" in result.reply
    assert "connection dropped" not in result.reply.lower()


def test_non_serializable_metadata_sanitized():
    class SampleEnum(Enum):
        ACTIVE = "active"

    @dataclass
    class SampleState:
        service: str = "MongoDB"

    raw = ChatTurnResult(
        reply="ok",
        intent="world_model_investigation_recap",
        meta={
            "when": datetime(2026, 5, 20, tzinfo=timezone.utc),
            "status": SampleEnum.ACTIVE,
            "state": SampleState(),
            "tags": {"wiredtiger"},
            "error": RuntimeError("boom"),
        },
    )
    sanitized = sanitize_chat_result_for_transport(raw)
    assert isinstance(sanitized.meta["when"], str)
    assert sanitized.meta["status"] == "active"
    assert sanitized.meta["state"]["service"] == "MongoDB"
    assert sanitized.meta["tags"] == ["wiredtiger"]
    assert str(sanitized.meta["error"]).startswith("RuntimeError:")


def test_compose_fallback_includes_partial_context():
    _seed("cog-boundary-partial")
    context = CognitionBoundaryContext(
        text="what do we know so far about MongoDB?",
        session_id="cog-boundary-partial",
    )
    result = compose_cognition_crash_fallback(RuntimeError("load failed"), context)
    assert "pilotcore-sales-engine" in result.reply
    assert "MongoDB" in result.reply
    assert "No mutation has been performed." in result.reply
    assert "connection dropped" not in result.reply.lower()


def test_safe_record_route_trace_swallows_errors():
    decision = type("Decision", (), {"meta": {}, "intent": "world_model_investigation_recap"})()
    with patch(
        "aethos_core.chat.operational_master_router.record_master_route_trace",
        side_effect=RuntimeError("trace failed"),
    ):
        safe_record_route_trace(session_id="cog-boundary-safe-trace", decision=decision)

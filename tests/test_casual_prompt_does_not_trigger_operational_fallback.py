# SPDX-License-Identifier: Apache-2.0
"""Casual prompts must not trigger operational crash fallback or world model."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.cognition_exception_boundary import (
    CognitionBoundaryContext,
    compose_cognition_crash_fallback,
    safe_resolve_operational_turn,
)
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


def _seed_mongodb(session_id: str) -> None:
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


def test_hi_does_not_call_world_model() -> None:
    _seed_mongodb("front-door-hi")
    with patch(
        "aethos_core.world_model.safe_world_model_runtime.safe_route_world_model_followup",
    ) as world_model:
        result = safe_resolve_operational_turn("Hi", session_id="front-door-hi")
    assert result is not None
    world_model.assert_not_called()
    assert result.intent == "casual_greeting"
    assert "MongoDB" not in result.reply


def test_capability_question_does_not_call_world_model() -> None:
    _seed_mongodb("front-door-capability")
    with patch(
        "aethos_core.world_model.safe_world_model_runtime.safe_route_world_model_followup",
    ) as world_model:
        result = safe_resolve_operational_turn(
            "what are you capable of?",
            session_id="front-door-capability",
        )
    assert result is not None
    world_model.assert_not_called()
    assert result.intent == "capability_intro"
    assert "MongoDB" not in result.reply


def test_casual_prompt_does_not_include_diagnostic_id_on_crash() -> None:
    _seed_mongodb("front-door-crash")
    with patch(
        "aethos_core.chat.operational_master_router.resolve_operational_master_route",
        side_effect=RuntimeError("boom"),
    ):
        result = safe_resolve_operational_turn("Hi", session_id="front-door-crash")
    assert result is not None
    assert "Diagnostic ID:" not in result.reply
    assert "MongoDB" not in result.reply
    assert result.intent == "casual_greeting"


def test_capability_crash_fallback_does_not_recover_mongodb() -> None:
    _seed_mongodb("front-door-cap-crash")
    with patch(
        "aethos_core.world_model.fallback_context_resolver.resolve_fallback_context",
    ) as resolve_fallback:
        result = compose_cognition_crash_fallback(
            RuntimeError("boom"),
            CognitionBoundaryContext(
                text="what are you capable of?",
                session_id="front-door-cap-crash",
            ),
        )
    resolve_fallback.assert_not_called()
    assert result is not None
    assert "MongoDB" not in result.reply
    assert "Diagnostic ID:" not in result.reply
    assert result.intent == "capability_intro"

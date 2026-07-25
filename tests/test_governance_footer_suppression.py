# SPDX-License-Identifier: Apache-2.0
"""Governance footer suppression for casual and capability replies."""

from __future__ import annotations

import pytest

from aethos_core.chat.cognition_exception_boundary import safe_resolve_operational_turn
from aethos_core.chat.explicit_mutation_intent import compose_explicit_mutation_preflight_reply
from aethos_core.chat.service import ChatTurnResult, _finalize_result
from aethos_core.identity.trust_language import LIGHT_TRUST_REMINDER
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.relational.relational_runtime import prepare_relational_turn
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.world_state_store import clear_world_model_for_tests

_FOOTER_FRAGMENT = "approval-gated and reviewable"


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


def _finalize_with_relational(
    *,
    user_text: str,
    reply: str,
    intent: str,
    session_id: str,
    meta: dict[str, str] | None = None,
) -> ChatTurnResult:
    emotional_context = prepare_relational_turn(user_text=user_text, session_id=session_id)
    result = ChatTurnResult(
        reply=reply,
        intent=intent,
        meta=dict(meta or {}),
    )
    return _finalize_result(result, emotional_context=emotional_context)


def test_hi_suppresses_footer() -> None:
    session_id = "gov-footer-hi"
    emotional_context = prepare_relational_turn(user_text="Hi", session_id=session_id)
    result = safe_resolve_operational_turn("Hi", session_id=session_id, emotional_context=emotional_context)
    assert result is not None
    assert result.intent == "casual_greeting"
    assert result.meta.get("suppress_governance_footer") == "true"
    assert _FOOTER_FRAGMENT not in result.reply.lower()


def test_capability_intro_suppresses_footer() -> None:
    session_id = "gov-footer-capability"
    emotional_context = prepare_relational_turn(
        user_text="what are you capable of?",
        session_id=session_id,
    )
    result = safe_resolve_operational_turn(
        "what are you capable of?",
        session_id=session_id,
        emotional_context=emotional_context,
    )
    assert result is not None
    assert result.intent in ("capability_intro", "capability_response")
    assert result.meta.get("suppress_governance_footer") == "true"
    assert _FOOTER_FRAGMENT not in result.reply.lower()


def test_general_help_suppresses_footer() -> None:
    session_id = "gov-footer-help"
    result = _finalize_with_relational(
        user_text="help",
        reply="I'm AethOS — an operational intelligence partner.",
        intent="general_help",
        session_id=session_id,
        meta={"suppress_governance_footer": "true", "route_id": "front_door"},
    )
    assert _FOOTER_FRAGMENT not in result.reply.lower()


def test_mongodb_diagnosis_keeps_footer() -> None:
    session_id = "gov-footer-mongo"
    _seed_mongodb(session_id)
    emotional_context = prepare_relational_turn(
        user_text="why is MongoDB failed",
        session_id=session_id,
    )
    result = safe_resolve_operational_turn(
        "why is MongoDB failed",
        session_id=session_id,
        emotional_context=emotional_context,
    )
    assert result is not None
    assert result.meta.get("suppress_governance_footer") != "true"
    assert _FOOTER_FRAGMENT in result.reply.lower() or LIGHT_TRUST_REMINDER.lower() in result.reply.lower()


def test_restart_preflight_keeps_footer() -> None:
    session_id = "gov-footer-restart"
    handled = compose_explicit_mutation_preflight_reply("restart MongoDB", session_id=session_id)
    assert handled is not None
    reply, intent, meta = handled
    result = _finalize_with_relational(
        user_text="restart MongoDB",
        reply=reply,
        intent=intent,
        session_id=session_id,
        meta=meta,
    )
    assert "preflight" in intent or "mutation" in intent
    assert _FOOTER_FRAGMENT in result.reply.lower() or "human-authorized" in result.reply.lower()

# SPDX-License-Identifier: Apache-2.0
"""Continuity recall API resilience tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.route_trace import clear_route_traces_for_tests, save_last_route_trace
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_state.narrative import (
    clear_operational_narrative_for_tests,
    compose_resilient_continuity_reply,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_operational_narrative_for_tests()
    clear_route_traces_for_tests()
    yield
    clear_operational_narrative_for_tests()
    clear_route_traces_for_tests()


def test_one_memory_source_fails_returns_partial_recap():
    save_last_route_trace(
        session_id="cont-partial",
        meta={
            "route_id": "failed_service_preemption",
            "matched_target": "pilotcore-sales-engine / production / MongoDB",
            "route_trace": "failed_service_preemption → failed_service_diagnosis",
        },
        intent="failed_service_diagnosis",
    )
    with patch(
        "aethos_core.operational_state.state.load_operational_state",
        side_effect=Exception("state unavailable"),
    ):
        reply, intent, meta = compose_resilient_continuity_reply("what were we doing earlier?", session_id="cont-partial")
    assert intent == "operational_narrative_continuity"
    assert "MongoDB" in reply or "failed_service_preemption" in reply
    assert meta.get("continuity_degraded") == "true"
    assert meta.get("continuity_correlation_id")
    assert "connection dropped" not in reply.lower()


def test_all_sources_empty_still_returns_bounded_recap():
    reply, intent, meta = compose_resilient_continuity_reply("what were we doing earlier?", session_id="cont-empty")
    assert intent == "operational_narrative_continuity"
    assert "don't have much stored" in reply.lower() or "operational tasks" in reply.lower()
    assert meta.get("continuity_correlation_id")
    assert "connection dropped" not in reply.lower()


def test_route_trace_history_used_in_recap():
    save_last_route_trace(
        session_id="cont-trace",
        meta={"route_id": "failed_service_preemption", "matched_target": "pilotcore-sales-engine / production / MongoDB", "route_trace": "operational_cognition → failed_service_preemption"},
        intent="failed_service_diagnosis",
    )
    reply, intent, _meta = compose_resilient_continuity_reply("what were we doing earlier?", session_id="cont-trace")
    assert "failed_service_preemption" in reply
    assert "MongoDB" in reply


def test_chat_continuity_recall_does_not_require_provider_llm():
    save_last_route_trace(
        session_id="cont-chat",
        meta={"route_id": "failed_service_preemption", "route_trace": "failed_service_preemption → failed_service_diagnosis"},
        intent="failed_service_diagnosis",
    )
    result = resolve_chat_turn("what were we doing earlier?", session_id="cont-chat", apply_relational_layer=False)
    assert result.intent == "operational_narrative_continuity"
    assert result.used_llm is False
    assert "connection dropped" not in result.reply.lower()

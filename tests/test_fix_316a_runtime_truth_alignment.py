# SPDX-License-Identifier: Apache-2.0
"""FIX 316A — runtime truth alignment tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.governance_restraint_runtime.restraint_runtime import assess_governance_restraint
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_intent import (
    parse_autonomous_capability_registry_intent,
)
from aethos_core.runtime_truth_alignment.governance_footer_policy import should_show_governance_footer
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_classifier import classify_runtime_prompt
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_composer import (
    compose_creator_attribution_response,
    compose_human_support_response,
    compose_platform_identity_response,
)
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_router import route_runtime_truth_alignment


_MOCK_EVIDENCE = {
    "summary": {"overall_maturity_tier": "OPERATIONAL"},
    "proven_items": ["Mission Control (PROVEN)"],
    "operational_items": ["Provider inspection (OPERATIONAL)"],
    "authority_note": "Observation only — humans approve execution.",
    "provider_readiness": [{"provider": "github", "readiness": "OPERATIONAL"}],
    "maturity_tier": "OPERATIONAL",
}


@pytest.fixture(autouse=True)
def _mock_capability_evidence():
    with patch(
        "aethos_core.runtime_truth_alignment.runtime_truth_alignment_composer._safe_capability_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


def test_classify_identity_and_capability():
    assert classify_runtime_prompt("Who are you?") == "platform_identity_response"
    assert classify_runtime_prompt("What is AethOS?") == "platform_identity_response"
    assert classify_runtime_prompt("Who created you?") == "creator_attribution_response"
    assert classify_runtime_prompt("What can you do?") == "capability_response"
    assert classify_runtime_prompt("What are you capable of doing?") == "capability_response"
    assert classify_runtime_prompt("I'm depressed") == "human_support_response"
    assert classify_runtime_prompt("deploy service api") == "operational_action"


def test_identity_routing_regression():
    routed = route_runtime_truth_alignment("Who are you?", session_id="rt-316a-id")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "platform_identity_response"
    assert "Platform identity" in body
    assert "governed operational intelligence" in body.lower()
    assert "Platform maturity" not in body
    assert meta["suppress_governance_footer"] == "true"


def test_creator_attribution_regression():
    body = compose_creator_attribution_response()
    assert "Raya Meresa" in body
    assert "Governance philosophy" in body
    assert "anthropic" not in body.lower()
    assert "openai" not in body.lower()

    routed = route_runtime_truth_alignment("Who created you?", session_id="rt-316a-creator")
    assert routed is not None
    assert routed[1] == "creator_attribution_response"
    assert "Raya Meresa" in routed[0]


def test_depression_routing_regression():
    routed = route_runtime_truth_alignment("I feel depressed", session_id="rt-316a-support")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "human_support_response"
    assert "wellbeing" in body.lower() or "sorry" in body.lower()
    assert "provider" not in body.lower()
    assert "Mission Control" not in body
    assert meta["suppress_governance_footer"] == "true"


def test_capability_routing_regression():
    routed = route_runtime_truth_alignment("What can you do?", session_id="rt-316a-cap")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "capability_response"
    assert "what I can help you with" in body.lower() or "operational intelligence partner" in body.lower()
    assert meta["suppress_governance_footer"] == "true"


def test_general_conversation_footer_suppression():
    restraint = assess_governance_restraint(intent="generative_answer", channel="chat")
    assert restraint["suppress_footer"] is True
    assert should_show_governance_footer(text="Tell me a joke", intent="generative_answer") is False


def test_operational_footer_preservation():
    assert should_show_governance_footer(text="Deploy service api", intent="mutation_preflight") is True
    restraint = assess_governance_restraint(intent="mutation_preflight", channel="chat")
    assert restraint["suppress_footer"] is False


def test_mission_control_routing_priority_validation():
    assert parse_autonomous_capability_registry_intent("what can you do") is not None
    preempted = route_runtime_truth_alignment("what can you do", session_id="rt-316a-priority")
    assert preempted is not None
    assert preempted[1] == "capability_response"
    assert preempted[1] != "mission_control_autonomous_capability_registry"


def test_resolve_chat_turn_identity_without_governance_footer():
    turn = resolve_chat_turn("Who are you?", session_id="rt-316a-chat-id")
    assert turn.intent == "platform_identity_response"
    assert "approval-gated" not in turn.reply.lower()
    assert "governed operational intelligence" in turn.reply.lower()


def test_platform_identity_structure():
    body = compose_platform_identity_response(session_id="rt-316a-structure")
    assert "## Platform identity" in body
    assert "## Mission" in body
    assert "## Core capabilities" in body
    assert "## Trust boundaries" in body
    assert "## Human oversight" in body
    assert "## Provider readiness (secondary)" in body


def test_human_support_copy():
    body = compose_human_support_response()
    assert "crisis" in body.lower() or "emergency" in body.lower()

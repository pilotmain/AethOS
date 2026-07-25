# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.6 — Operational entity realism & execution continuity tests."""

from __future__ import annotations

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.agents.runtime.role_inference import infer_execution_intent
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.entity_grounding.entity_disambiguation import ground_entity_query
from aethos_core.governance_restraint_runtime.restraint_runtime import assess_governance_restraint
from aethos_core.agent_progression_memory.progression_store import clear_progression_for_tests
from aethos_core.agents.runtime.subagent_session_store import clear_subagent_sessions_for_tests
from aethos_core.operational_entity_runtime.lightweight_agent_registry import clear_operational_entities_for_tests
from aethos_core.operational_entity_runtime.runtime import assess_operational_entity_runtime
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.research_entity_alignment.entity_alignment import align_research_entity


def setup_function() -> None:
    clear_operational_entities_for_tests()
    clear_progression_for_tests()
    clear_subagent_sessions_for_tests()


def test_execution_intent_agent_creation():
    intent = infer_execution_intent("create two agents, one development one qa")
    assert intent["execution_prompt"] is True
    assert intent["intent"] == "agent_creation"


def test_agent_creation_operational_reply():
    session = "test-1176-create"
    result = resolve_chat_turn(
        "create two agents, one development one qa, assign them skills",
        session_id=session,
        channel="telegram",
    )
    assert "initialized" in result.reply.lower()
    assert "development" in result.reply.lower()
    assert "qa" in result.reply.lower()
    assert "gtm" not in result.reply.lower()
    assert "I can help you design" not in result.reply
    assert result.meta.get("lane") == "operational_entity"


def test_entity_status_continuity():
    session = "test-1176-status"
    resolve_chat_turn(
        "create two agents, one development one qa",
        session_id=session,
        channel="telegram",
    )
    follow = resolve_chat_turn("Have you created them already?", session_id=session, channel="telegram")
    assert "yes" in follow.reply.lower() or "initialized" in follow.reply.lower()
    assert "haven't created" not in follow.reply.lower()


def test_workspace_results_continuity():
    session = "test-1176-results"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    follow = resolve_chat_turn(
        "Where can I see the agents work result?",
        session_id=session,
        channel="telegram",
    )
    assert "operational workspace" in follow.reply.lower()
    assert "need more context" not in follow.reply.lower()


def test_entity_grounding_disambiguates_aethos():
    grounding = ground_entity_query(query="AethOS competitor analysis for GTM strategy")
    assert grounding["grounded"] is True
    assert grounding["entity"] == "aethos_platform"
    assert "operational intelligence platform" in grounding["platform_context"]


def test_research_entity_alignment():
    aligned = align_research_entity(query="Research AethOS market competitors")
    assert aligned["grounded"] is True
    assert "operational intelligence platform" in aligned["aligned_query"]


def test_governance_suppressed_for_entity_lane():
    restraint = assess_governance_restraint(intent="agent_creation", lane="operational_entity", channel="telegram")
    assert restraint["suppress_footer"] is True


def test_operational_entity_runtime_assessment():
    session = "test-1176-assess"
    assess_operational_entity_runtime(
        session_id=session,
        channel="telegram",
        user_text="create two agents, one development one qa",
    )
    assessment = assess_operational_entity_runtime(session_id=session, channel="telegram")
    assert assessment["phase"] == "11.7.6"
    assert assessment["execution_presence"]["has_active_entities"] is True


def test_aggregate_runtime_phase():
    agg = assess_conversational_operational_grounding(session_id="test-1176-agg", channel="telegram")
    assert agg["phase"] == "11.8.2"
    assert "operational_entity_runtime" in agg


def test_capability_matrix_includes_entity_runtime():
    rows = build_capability_truth_matrix()
    assert any(r["id"] == "operational_entity_runtime" for r in rows)

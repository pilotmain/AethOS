# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.7 — Operational progression realism tests."""

from __future__ import annotations

from aethos_core.agent_progression_memory.progression_store import clear_progression_for_tests, get_progression_state
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.conversation.progression_inference import infer_progression_intent
from aethos_core.governance_restraint_runtime.restraint_runtime import assess_governance_restraint
from aethos_core.investigation_output_runtime.output_composer import compose_investigation_output
from aethos_core.operational_entity_runtime.lightweight_agent_registry import clear_operational_entities_for_tests
from aethos_core.operational_progression_runtime.runtime import assess_operational_progression_runtime
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


def setup_function() -> None:
    clear_operational_entities_for_tests()
    clear_progression_for_tests()


def test_progression_intent_agent_conclusion():
    intent = infer_progression_intent("What did the strategist conclude?")
    assert intent["progression_prompt"] is True
    assert intent["intent"] == "agent_conclusion"
    assert intent["target_agent"] == "Product Strategist"


def test_strategist_conclusion_evolving_findings():
    session = "test-1177-conclude"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    follow = resolve_chat_turn("What did the strategist conclude?", session_id=session, channel="telegram")
    assert "positioning advantages" in follow.reply.lower() or "operational partner" in follow.reply.lower()
    assert "accumulate here" not in follow.reply.lower()
    assert "need more context" not in follow.reply.lower()
    assert follow.meta.get("lane") in {"operational_progression", "operational_entity"}


def test_progression_advances_across_turns():
    session = "test-1177-advance"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    resolve_chat_turn("What did the strategist conclude?", session_id=session, channel="telegram")
    state = get_progression_state(session_id=session)
    assert int(state.get("stage") or 0) >= 2


def test_researcher_findings_included_at_stage_two():
    session = "test-1177-researcher"
    from aethos_core.agent_progression_memory.progression_store import seed_progression
    from aethos_core.operational_entity_runtime.lightweight_agent_registry import register_operational_entity

    register_operational_entity(session_id=session, name="Market Researcher", role="Market Researcher")
    register_operational_entity(session_id=session, name="Product Strategist", role="Product Strategist")
    seed_progression(session_id=session, agent_names=["Market Researcher", "Product Strategist"])
    output = compose_investigation_output(session_id=session, agent_name="Product Strategist", advance=True)
    reply = str(output.get("reply") or "").lower()
    assert output.get("available") is True
    assert "observability" in reply or "devops" in reply or "multi-agent" in reply or "positioning" in reply


def test_workspace_results_shows_progression():
    session = "test-1177-workspace"
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
    assert "operational workspace" in follow.reply.lower() or "strategist" in follow.reply.lower()
    assert "accumulate here as the agents progress" not in follow.reply.lower()


def test_governance_suppressed_for_progression_lane():
    restraint = assess_governance_restraint(intent="agent_conclusion", lane="operational_progression", channel="telegram")
    assert restraint["suppress_footer"] is True


def test_operational_progression_runtime_assessment():
    session = "test-1177-assess"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    resolve_chat_turn("What did the strategist conclude?", session_id=session, channel="telegram")
    assessment = assess_operational_progression_runtime(session_id=session, channel="telegram")
    assert assessment["phase"] == "11.7.7"
    assert assessment["execution_progress"]["progression_active"] is True


def test_aggregate_runtime_phase_1177():
    agg = assess_conversational_operational_grounding(session_id="test-1177-agg", channel="telegram")
    assert agg["phase"] == "11.8.2"
    assert "operational_progression_runtime" in agg


def test_completion_watch_no_visibility_collapse():
    session = "test-1177-watch"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    follow = resolve_chat_turn(
        "please let me know once they are done",
        session_id=session,
        channel="telegram",
    )
    assert "don't have visibility" not in follow.reply.lower()
    assert "need more context" not in follow.reply.lower()
    assert "operational" in follow.reply.lower() or "strategist" in follow.reply.lower() or "track" in follow.reply.lower()


def test_operational_continuity_guard():
    session = "test-1177-guard"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    follow = resolve_chat_turn(
        "I'm waiting for the agent analysis to finish",
        session_id=session,
        channel="telegram",
    )
    assert "don't have visibility" not in follow.reply.lower()
    assert follow.used_llm is False

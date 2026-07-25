# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.8 — Investigative continuity realism tests."""

from __future__ import annotations

from aethos_core.agent_progression_memory.progression_store import clear_progression_for_tests
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.investigative_continuity_memory.reasoning_chain import get_reasoning_chain
from aethos_core.investigative_continuity_runtime.runtime import assess_investigative_continuity_runtime
from aethos_core.operational_entity_runtime.lightweight_agent_registry import clear_operational_entities_for_tests
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


def setup_function() -> None:
    clear_operational_entities_for_tests()
    clear_progression_for_tests()


def test_investigative_continuity_chain_builds():
    session = "test-1178-chain"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    resolve_chat_turn("What did the strategist conclude?", session_id=session, channel="telegram")
    resolve_chat_turn("What did the strategist conclude?", session_id=session, channel="telegram")
    chain = get_reasoning_chain(session_id=session, agent_name="Product Strategist")
    assert len(chain) >= 2
    assert chain[0].get("hypothesis")


def test_investigative_narrative_references_prior_findings():
    session = "test-1178-narrative"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    resolve_chat_turn("What did the strategist conclude?", session_id=session, channel="telegram")
    follow = resolve_chat_turn("What did the strategist conclude?", session_id=session, channel="telegram")
    assert "investigative continuity" in follow.reply.lower() or "strategic confidence" in follow.reply.lower()
    assert "don't have visibility" not in follow.reply.lower()


def test_investigative_continuity_runtime_assessment():
    session = "test-1178-assess"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    resolve_chat_turn("What did the strategist conclude?", session_id=session, channel="telegram")
    assessment = assess_investigative_continuity_runtime(session_id=session, channel="telegram")
    assert assessment["phase"] == "11.7.8"
    assert assessment["chain_count"] >= 1


def test_aggregate_runtime_phase_1178():
    agg = assess_conversational_operational_grounding(session_id="test-1178-agg", channel="telegram")
    assert agg["phase"] == "11.8.2"
    assert "investigative_continuity_runtime" in agg


def test_capability_matrix_includes_investigative_continuity():
    rows = build_capability_truth_matrix()
    assert any(r["id"] == "investigative_continuity_runtime" for r in rows)

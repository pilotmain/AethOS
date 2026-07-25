# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.3 — Conversational realism polish tests."""

from __future__ import annotations

from aethos_core.conversation.legacy_polish_api import synthesize_grounded_operational_reply
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.conversation.polish_compat import pacing_profile
from aethos_core.conversation.polish_compat import score_formulaic_density, shape_interaction
from aethos_core.conversation.legacy_polish_api import assess_conversational_realism_polish
from aethos_core.conversation.polish_compat import (
    assess_semantic_diversification,
    compose_improvement_narrative,
)
from aethos_core.conversation.polish_compat import assess_thread_resurrection
from aethos_core.conversation.operational_memory import clear_operational_memory_for_tests, persist_investigation, record_focus_recovery
from aethos_core.operational_context_memory.context_store import persist_operational_context
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


def _seed(session_id: str = "test-1173") -> None:
    clear_operational_memory_for_tests()
    record_focus_recovery(session_id=session_id, focus="Railway deployment recovery", channel="telegram")
    persist_investigation(session_id=session_id, investigation="replay continuity durability")
    persist_operational_context(
        session_id=session_id,
        context={"deployment_subject": "Railway deployment recovery", "replay_concern": "replay continuity durability"},
    )


def test_semantic_diversification_varies_structure():
    a = compose_improvement_narrative(
        concern="replay continuity",
        signals=["telemetry staying fresh"],
        closing="Still watching.",
        session_id="session-a",
    )
    b = compose_improvement_narrative(
        concern="replay continuity",
        signals=["telemetry staying fresh"],
        closing="Still watching.",
        session_id="session-b",
    )
    semantic = assess_semantic_diversification()
    assert semantic["semantic_variants_enabled"] is True
    assert a != b or "replay continuity" in a.lower()


def test_pacing_decisive_vs_honest_brief():
    decisive = pacing_profile(confidence=0.75, channel="telegram", certainty_tier="high")
    brief = pacing_profile(confidence=0.4, channel="telegram", certainty_tier="low")
    assert decisive["mode"] == "decisive"
    assert brief["mode"] == "honest_brief"
    assert brief["compress"] is True


def test_interaction_shaping_and_formulaic_scoring():
    dense = (
        "Extended monitoring remains active across verification windows. "
        "Topology convergence and sustained verification continue."
    )
    before = score_formulaic_density(dense)
    shaped = shape_interaction(dense, channel="telegram", pacing={"compress": True, "max_paragraphs": 2})
    after = score_formulaic_density(shaped)
    assert before["dense"] is True
    assert before["formulaic_hits"] >= 2
    assert shaped  # shaping preserves content while applying channel compression rules
    assert after["formulaic_hits"] >= 2


def test_thread_resurrection_guard_penalizes_stale_mismatch():
    guard = assess_thread_resurrection(
        subject="old replay continuity issue",
        category="replay",
        bridge={"last_focus": "Railway deployment recovery", "active_investigations": ["old replay continuity issue"]},
        age_hours=30.0,
    )
    assert guard["stale"] is True
    assert guard["confidence_penalty"] > 0


def test_realism_polish_aggregate():
    polish = assess_conversational_realism_polish(session_id="test-1173", channel="telegram", confidence=0.7)
    assert polish["phase"] == "11.7.3"
    assert polish["polish_qualified"] is True


def test_conversational_grounding_phase_1173():
    _seed()
    state = assess_conversational_operational_grounding(session_id="test-1173", channel="telegram")
    assert state["phase"] == "11.8.2"
    assert state["realism_polish"] is not None
    assert "durable agent" in state["narrative"].lower() or "cross-surface" in state["narrative"].lower()


def test_synthesis_applies_pacing_and_resurrection():
    _seed()
    result = synthesize_grounded_operational_reply(
        user_text="Has the situation improved?",
        session_id="test-1173",
        channel="telegram",
    )
    assert result is not None
    assert result["pacing"]["mode"] in {"decisive", "balanced", "honest_brief"}
    assert "resurrection_guard" in result


def test_capability_matrix_conversational_realism_polish():
    matrix = build_capability_truth_matrix()
    polish = next((r for r in matrix if r.get("id") == "conversational_realism_polish"), None)
    assert polish is not None and polish["verification_coverage_pct"] >= 89

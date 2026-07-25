# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.x — Real-world conversational hardening tests."""

from __future__ import annotations

from aethos_core.continuity_reconstruction.ambiguity_scoring import score_continuity_ambiguity
from aethos_core.continuity_reconstruction.subject_affinity import rank_operational_subjects, select_primary_subject
from aethos_core.conversation.legacy_polish_api import synthesize_grounded_operational_reply
from aethos_core.conversation.polish_compat import (
    assess_narrative_entropy,
    diversify_monitoring_close,
)
from aethos_core.operational_context_memory.context_bridge import build_operational_context_bridge
from aethos_core.operational_context_memory.context_store import persist_operational_context
from aethos_core.conversation.operational_memory import clear_operational_memory_for_tests, persist_investigation, record_focus_recovery


def _seed_multi_thread(session_id: str = "test-117x") -> None:
    clear_operational_memory_for_tests()
    record_focus_recovery(session_id=session_id, focus="Railway production deployment", channel="telegram")
    persist_investigation(session_id=session_id, investigation="replay continuity durability")
    persist_investigation(session_id=session_id, investigation="topology dependency instability")
    persist_operational_context(
        session_id=session_id,
        context={
            "deployment_subject": "Railway production deployment",
            "replay_concern": "replay continuity durability",
            "topology_concern": "topology dependency instability",
        },
    )


def test_subject_affinity_prefers_deployment_prompt():
    _seed_multi_thread()
    bridge = build_operational_context_bridge(session_id="test-117x", channel="telegram")
    selection = select_primary_subject(
        user_text="Did the Railway deployment fully stabilize?",
        bridge=bridge,
    )
    assert "railway" in selection["subject"].lower() or "deployment" in selection["subject"].lower()
    assert selection["category"] in {"deployment", "provider", "recovery"}


def test_ambiguity_detects_competing_subjects():
    _seed_multi_thread()
    bridge = build_operational_context_bridge(session_id="test-117x", channel="telegram")
    ambiguity = score_continuity_ambiguity(user_text="Did it improve?", bridge=bridge, intent="implicit_followup")
    assert ambiguity["ambiguous"] is True
    assert ambiguity["ambiguity_score"] >= 0.5


def test_low_confidence_graceful_uncertainty():
    clear_operational_memory_for_tests()
    from aethos_core.human_centered.continuity_memory import clear_continuity_memory_for_tests

    clear_continuity_memory_for_tests()
    result = synthesize_grounded_operational_reply(
        user_text="Did it improve?",
        session_id="empty-session",
        channel="telegram",
    )
    assert result is not None
    reply = result["reply"].lower()
    assert (
        "strong enough thread match" in reply
        or "continuity confidence" in reply
        or "operational context confidence" in reply
        or "name the deployment" in reply
    )


def test_narrative_diversification_rotates_closings():
    a = diversify_monitoring_close(session_id="session-a")
    b = diversify_monitoring_close(session_id="session-b")
    entropy = assess_narrative_entropy()
    assert entropy["rotation_enabled"] is True
    assert "extended monitoring remains active" not in a.lower()
    assert a != b or "observation" in a.lower()


def test_rank_operational_subjects_returns_ordered_candidates():
    _seed_multi_thread()
    bridge = build_operational_context_bridge(session_id="test-117x", channel="telegram")
    ranked = rank_operational_subjects(user_text="Has replay continuity improved?", bridge=bridge)
    assert len(ranked) >= 2
    assert ranked[0]["affinity_score"] >= ranked[1]["affinity_score"]

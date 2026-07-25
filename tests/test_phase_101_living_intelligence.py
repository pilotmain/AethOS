# SPDX-License-Identifier: Apache-2.0
"""Phase 10.1 — Living intelligence, real presence, world-class agentic experience."""

from __future__ import annotations

import pytest

from aethos_core.chat.living_intelligence import execute_living_intelligence, is_living_intelligence_request
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.collaboration.teamwork_runtime import clear_teamwork_for_tests, create_collaboration_room, list_collaboration_rooms
from aethos_core.conversation.conversation_runtime import clear_conversation_for_tests, record_conversation_thread, resume_conversation
from aethos_core.copilot.copilot_runtime import generate_operational_hypotheses, get_copilot_status
from aethos_core.human_centered.living_companion_runtime import get_living_companion_overview
from aethos_core.human_centered.thinking_boundaries import assess_thinking_boundaries
from aethos_core.personal_intelligence.personal_runtime import clear_personal_intelligence_for_tests, delete_personal_intelligence, opt_in_personal_intelligence
from aethos_core.presence.live.live_presence_runtime import build_contextual_nudge, clear_live_presence_for_tests, record_focus
from aethos_core.trust.world_class_explainability import build_world_class_explanation


@pytest.fixture(autouse=True)
def _clean():
    clear_live_presence_for_tests()
    clear_conversation_for_tests()
    clear_personal_intelligence_for_tests()
    clear_teamwork_for_tests()
    yield
    clear_live_presence_for_tests()
    clear_conversation_for_tests()
    clear_personal_intelligence_for_tests()
    clear_teamwork_for_tests()


def test_living_companion_overview():
    overview = get_living_companion_overview()
    assert overview.get("phase") == "10.1.4"
    assert overview.get("autonomous_execution_blocked") is True
    assert "live_presence" in overview
    assert "copilot" in overview


def test_live_presence_nudge():
    from aethos_core.human_centered.continuity_memory import seed_default_continuity

    seed_default_continuity(session_id="live-test")
    record_focus(session_id="live-test", topic="Railway deployment debugging")
    nudge = build_contextual_nudge(session_id="live-test")
    assert nudge.get("ok") is True
    text = nudge.get("nudge", "")
    assert "Human API" in text or "404" in text or "Would you like" in text
    assert nudge.get("autonomous_execution_blocked") is True


def test_conversation_resume():
    record_conversation_thread(
        session_id="conv-test",
        topics=["Railway restart verification", "GitHub workflow discovery"],
        unresolved=["deployment evidence reliability"],
        summary="Investigating deployment failures",
    )
    resume = resume_conversation(session_id="conv-test")
    assert resume.get("ok") is True
    text = resume.get("resume_text", "")
    assert "Railway" in text or "GitHub" in text or "10.1.1" in text
    assert "deployment evidence" in text.lower() or "404" in text


def test_copilot_hypotheses_with_confidence():
    hyp = generate_operational_hypotheses(session_id="copilot-test", context="deployment failure")
    assert hyp.get("ok") is True
    assert hyp.get("hypotheses")
    assert "confidence" in hyp.get("explanation", "").lower()
    assert hyp.get("autonomous_execution_blocked") is True


def test_thinking_boundaries_blocks_silent_execution():
    result = assess_thinking_boundaries(proposed_capability="silent_execution")
    assert result.get("allowed") is False
    allowed = assess_thinking_boundaries(proposed_capability="continuous_analysis")
    assert allowed.get("allowed") is True


def test_personal_intelligence_opt_in_deletable():
    assert opt_in_personal_intelligence(session_id="pi-test").get("opted_in") is True
    deleted = delete_personal_intelligence(session_id="pi-test")
    assert deleted.get("deleted") is True


def test_world_class_explainability_narrative():
    expl = build_world_class_explanation(session_id="trust-test")
    assert expl.get("ok") is True
    assert expl.get("narrative")
    assert expl.get("autonomous_execution_blocked") is True


def test_teamwork_collaboration_room():
    room = create_collaboration_room(operator_id="op1", title="Deploy investigation")
    assert room.get("ok") is True
    rooms = list_collaboration_rooms(operator_id="op1")
    assert len(rooms.get("rooms") or []) >= 1


def test_living_intelligence_chat_lane_resume():
    record_conversation_thread(session_id="chat-resume", topics=["workflow health"], unresolved=["CI instability"])
    handled = execute_living_intelligence("continue where we left off", session_id="chat-resume")
    assert handled is not None
    body, intent, meta = handled
    assert intent == "conversation_resume"
    assert meta.get("lane") == "living_intelligence"


def test_living_intelligence_copilot_lane():
    assert is_living_intelligence_request("copilot analysis please")
    handled = execute_living_intelligence("why did this fail — root cause", session_id="copilot-chat")
    assert handled is not None
    assert handled[1] == "operational_copilot"


def test_chat_turn_living_intelligence_integrated():
    record_conversation_thread(session_id="turn-test", topics=["Railway deploy"], unresolved=["verification"])
    result = resolve_chat_turn("continue where we left off", session_id="turn-test")
    assert "Railway" in result.reply or "investigating" in result.reply.lower()
    assert result.meta.get("lane") in ("living_intelligence", "human_centered")


def test_copilot_status_features():
    status = get_copilot_status()
    assert status.get("phase") == "10.1D"
    assert status.get("features", {}).get("operational_hypothesis_engine") is True

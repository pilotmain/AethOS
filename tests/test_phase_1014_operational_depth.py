# SPDX-License-Identifier: Apache-2.0
"""Phase 10.1.4 — Operational depth, human realism, companion intelligence refinement."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.conversation_runtime import clear_conversation_for_tests, record_conversation_thread
from aethos_core.human_centered.continuity_memory import clear_continuity_memory_for_tests, seed_default_continuity
from aethos_core.human_centered.operational_partner_runtime import render_operational_partner_brief
from aethos_core.intuition.companion_quality_metrics import compute_companion_quality_metrics
from aethos_core.presence.calm.calm_presence_runtime import clear_calm_presence_for_tests
from aethos_core.reasoning.reasoning_engine import assess_deep_operational_reasoning
from aethos_core.replay.deep_replay.deep_replay_runtime import clear_deep_replay_for_tests
from aethos_core.restraint.restraint_runtime import clear_restraint_for_tests
from aethos_core.timeline.operational_timeline import clear_timeline_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_conversation_for_tests()
    clear_continuity_memory_for_tests()
    clear_calm_presence_for_tests()
    clear_restraint_for_tests()
    clear_timeline_for_tests()
    clear_deep_replay_for_tests()
    yield
    clear_conversation_for_tests()
    clear_continuity_memory_for_tests()
    clear_calm_presence_for_tests()
    clear_restraint_for_tests()
    clear_timeline_for_tests()
    clear_deep_replay_for_tests()


def test_deep_operational_reasoning_causality():
    seed_default_continuity(session_id="reasoning-test")
    result = assess_deep_operational_reasoning(session_id="reasoning-test")
    synthesis = result.get("synthesis", "")
    assert "0.84" in synthesis and "0.61" in synthesis
    assert "production instability" in synthesis.lower() or "does not currently indicate" in synthesis.lower()
    assert result.get("phase") == "10.1.4A"


def test_partner_brief_end_state():
    seed_default_continuity(session_id="partner-test")
    brief = render_operational_partner_brief(session_id="partner-test")
    text = brief.get("brief", "")
    assert "production-critical" in text.lower() or "replay" in text.lower()
    assert "scheduler" in text.lower() or "validation" in text.lower()
    assert brief.get("phase") == "10.1.4"
    assert brief.get("identity") == "operational partner"


def test_continue_where_we_left_off_operational_depth():
    seed_default_continuity(session_id="continue-depth")
    result = resolve_chat_turn("continue where we left off", session_id="continue-depth")
    assert result.meta.get("operational_depth") == "true"
    assert "Governed assistance — I recommend" not in result.reply
    assert "replay" in result.reply.lower() or "stabilized" in result.reply.lower()


def test_thread_context_in_partner_brief():
    record_conversation_thread(
        session_id="thread-partner",
        topics=["Railway restart verification"],
        unresolved=["deployment evidence reliability"],
    )
    result = resolve_chat_turn("continue where we left off", session_id="thread-partner")
    assert "Railway" in result.reply or "deployment evidence" in result.reply


def test_companion_quality_metrics_v2():
    seed_default_continuity(session_id="quality-v2")
    metrics = compute_companion_quality_metrics(session_id="quality-v2")
    assert metrics.get("phase") == "10.1.4H"
    assert "trust_retention" in (metrics.get("metrics") or {})
    assert metrics.get("overall_score", 0) > 0.7


def test_human_operational_reasoning_api():
    client = TestClient(app)
    r = client.get("/api/v1/human/operational-reasoning?session_id=default")
    assert r.status_code == 200
    assert r.json().get("phase") == "10.1.4A"


def test_human_partner_brief_api():
    client = TestClient(app)
    r = client.get("/api/v1/human/partner-brief?session_id=default")
    assert r.status_code == 200
    assert r.json().get("phase") == "10.1.4"


def test_human_companion_quality_api():
    client = TestClient(app)
    r = client.get("/api/v1/human/companion-quality?session_id=default")
    assert r.status_code == 200
    assert r.json().get("phase") == "10.1.4H"


def test_investigation_companion_honest_uncertainty():
    client = TestClient(app)
    r = client.get("/api/v1/human/investigation-companion?session_id=default")
    assert r.status_code == 200
    narrative = r.json().get("narrative", "")
    assert "enough evidence" in narrative.lower() or "validation step" in narrative.lower()

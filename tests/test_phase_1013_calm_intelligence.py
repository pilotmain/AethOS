# SPDX-License-Identifier: Apache-2.0
"""Phase 10.1.3 — Operational intuition, presence flow, calm intelligence."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.conversation_runtime import clear_conversation_for_tests
from aethos_core.human_centered.continuity_memory import clear_continuity_memory_for_tests, seed_default_continuity
from aethos_core.human_centered.operational_companion_runtime import render_operational_companion_brief
from aethos_core.intuition.intuition_engine import assess_operational_intuition
from aethos_core.intuition.presence_quality_metrics import compute_presence_quality_metrics
from aethos_core.presence.calm.calm_presence_runtime import clear_calm_presence_for_tests
from aethos_core.restraint.restraint_runtime import clear_restraint_for_tests
from aethos_core.timeline.operational_timeline import clear_timeline_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_conversation_for_tests()
    clear_continuity_memory_for_tests()
    clear_calm_presence_for_tests()
    clear_restraint_for_tests()
    clear_timeline_for_tests()
    yield
    clear_conversation_for_tests()
    clear_continuity_memory_for_tests()
    clear_calm_presence_for_tests()
    clear_restraint_for_tests()
    clear_timeline_for_tests()


def test_operational_intuition_prioritizes_impact():
    seed_default_continuity(session_id="intuition-test")
    result = assess_operational_intuition(session_id="intuition-test")
    guidance = result.get("guidance", "")
    assert "highest-impact" in guidance.lower() or "Highest-impact" in guidance
    assert "replay" in guidance.lower() or "Living Intelligence" in guidance
    assert result.get("phase") == "10.1.3"


def test_companion_brief_calm_end_state():
    seed_default_continuity(session_id="brief-test")
    brief = render_operational_companion_brief(session_id="brief-test")
    text = brief.get("brief", "")
    assert "stabilized" in text.lower() or "Human API" in text
    assert "replay" in text.lower() or "I can:" in text
    assert brief.get("phase") == "10.1.3"


def test_continue_where_we_left_off_companion_quality():
    seed_default_continuity(session_id="continue-test")
    result = resolve_chat_turn("continue where we left off", session_id="continue-test")
    assert "404" in result.reply or "mcFetch" in result.reply or "stabilized" in result.reply.lower()
    assert "Governed assistance — I recommend" not in result.reply
    assert result.meta.get("calm_intelligence") == "true"


def test_presence_quality_metrics():
    seed_default_continuity(session_id="metrics-test")
    metrics = compute_presence_quality_metrics(session_id="metrics-test")
    assert metrics.get("ok") is True
    assert "interruption_quality" in (metrics.get("metrics") or {})
    assert metrics.get("overall_score", 0) > 0.5


def test_human_intuition_api():
    client = TestClient(app)
    r = client.get("/api/v1/human/intuition?session_id=default")
    assert r.status_code == 200
    assert r.json().get("phase") == "10.1.3"
    client = TestClient(app)
    r = client.get("/api/v1/human/companion-brief?session_id=default")
    assert r.status_code == 200
    assert r.json().get("phase") == "10.1.4"


def test_human_presence_quality_api():
    client = TestClient(app)
    r = client.get("/api/v1/human/presence-quality?session_id=default")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_restraint_prevents_repetition():
    from aethos_core.restraint.restraint_runtime import apply_restraint

    first = apply_restraint(text="Same guidance text for testing restraint layer.", session_id="r-test")
    second = apply_restraint(text="Same guidance text for testing restraint layer.", session_id="r-test")
    assert "already shared" in second.get("text", "").lower()

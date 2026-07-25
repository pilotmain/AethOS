# SPDX-License-Identifier: Apache-2.0
"""Phase 10.1.2 — Living intelligence depth, memory realism, trust polish."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.continuity_renderer import render_continuity_resume
from aethos_core.conversation.conversation_runtime import clear_conversation_for_tests, record_conversation_thread, resume_conversation
from aethos_core.human_centered.continuity_memory import (
    clear_continuity_memory_for_tests,
    load_continuity_memory,
    record_resolved_issue,
    seed_default_continuity,
    set_active_phase,
)
from aethos_core.human_centered.trust_controls import delete_all_operator_memory, get_trust_controls


@pytest.fixture(autouse=True)
def _clean():
    clear_conversation_for_tests()
    clear_continuity_memory_for_tests()
    yield
    clear_conversation_for_tests()
    clear_continuity_memory_for_tests()


def test_continuity_memory_seed_grounded():
    record = seed_default_continuity(session_id="seed-test")
    assert record.get("phase") == "10.1.1"
    assert any("404" in r for r in (record.get("resolved") or []))
    assert record.get("next_best_step")
    assert record.get("governance") == "No autonomous action"


def test_continuity_renderer_specific_resume():
    seed_default_continuity(session_id="render-test")
    rendered = render_continuity_resume(session_id="render-test")
    text = rendered.get("resume_text", "")
    assert "Human API" in text or "10.1.1" in text
    assert "404" in text or "mcFetch" in text
    assert "No autonomous action" in text
    assert "Continuing where we left off" not in text


def test_continue_where_we_left_off_chat():
    seed_default_continuity(session_id="chat-continuity")
    result = resolve_chat_turn("continue where we left off", session_id="chat-continuity")
    assert "humanapi" in result.reply.lower() or "404" in result.reply or "mcfetch" in result.reply.lower()
    assert "Governed assistance — I recommend" not in result.reply


def test_conversation_thread_merged_into_resume():
    seed_default_continuity(session_id="thread-merge")
    record_conversation_thread(
        session_id="thread-merge",
        topics=["Railway restart verification"],
        unresolved=["deployment evidence reliability"],
    )
    resume = resume_conversation(session_id="thread-merge")
    text = resume.get("resume_text", "").lower()
    assert "railway" in text or "deployment evidence" in text


def test_trust_controls_transparency():
    seed_default_continuity(session_id="trust-test")
    controls = get_trust_controls(session_id="trust-test")
    assert controls.get("ok") is True
    assert controls.get("controls", {}).get("delete_continuity_memory") is True
    mem = controls.get("continuity_memory") or {}
    assert (mem.get("record") or {}).get("phase") == "10.1.1"


def test_delete_operator_memory():
    seed_default_continuity(session_id="delete-test")
    deleted = delete_all_operator_memory(session_id="delete-test")
    assert deleted.get("ok") is True
    assert not load_continuity_memory(session_id="delete-test").get("phase")


def test_human_continuity_api():
    client = TestClient(app)
    r = client.get("/api/v1/human/continuity?session_id=default")
    assert r.status_code == 200
    body = r.json()
    assert body.get("resume", {}).get("ok") is True
    assert "404" in body.get("resume", {}).get("resume_text", "") or "mcFetch" in body.get("resume", {}).get("resume_text", "")


def test_human_trust_controls_api():
    client = TestClient(app)
    r = client.get("/api/v1/human/trust-controls?session_id=default")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_custom_phase_recorded():
    set_active_phase(session_id="custom", phase="10.1.2", focus="Memory realism polish")
    record_resolved_issue(session_id="custom", issue="Continuity renderer replaces generic resume placeholders")
    rendered = render_continuity_resume(session_id="custom")
    assert "10.1.2" in rendered.get("resume_text", "")
    assert "Continuity renderer" in rendered.get("resume_text", "")

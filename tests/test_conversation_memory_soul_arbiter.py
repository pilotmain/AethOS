# SPDX-License-Identifier: Apache-2.0
"""Regression tests for conversation memory, soul/identity answering, and the arbiter.

Covers the three handoff sections:
  §1 conversation summary memory (SQLite recap) + continuity recall path
  §2 soul / identity answering from SOUL.md (no deflection)
  §3 Multi-Model Arbiter lifecycle + the arbiter_run chat tool (honest preconditions)
"""

from __future__ import annotations

import asyncio
import json

import pytest

from aethos_core.config import get_settings


# ── §1 — conversation summary memory ────────────────────────────────────────


@pytest.fixture
def conversation_memory(tmp_path, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "conversation_memory_enabled", True, raising=False)
    monkeypatch.setattr(s, "conversation_memory_dir", str(tmp_path / "conv_mem"), raising=False)
    monkeypatch.setattr(s, "vector_memory_enabled", False, raising=False)
    from aethos_core.memory import conversation_summary_memory as mem

    mem.reset_for_tests()
    yield mem
    mem.reset_for_tests()


def test_conversation_memory_records_and_recaps(conversation_memory) -> None:
    mem = conversation_memory
    sid = "memtest"
    mem.record_turn(session_id=sid, user_text="Let's discuss the deployment plan for the api service", reply="Sure.", intent="general")
    mem.record_turn(session_id=sid, user_text="What about adding Redis caching?", reply="Here's how.", intent="general")

    summary = mem.get_session_summary(sid)
    assert summary["turn_count"] == 2
    assert "deployment plan" in summary["summary"].lower()
    assert "redis" in summary["summary"].lower()

    recap = mem.compose_conversation_recap_text(sid)
    assert recap is not None
    assert "redis" in recap.lower()
    assert "deployment plan" in recap.lower()


def test_conversation_memory_redacts_secrets(conversation_memory) -> None:
    mem = conversation_memory
    sid = "memsecret"
    mem.record_turn(
        session_id=sid,
        user_text="my token is sk-ABCDEF1234567890ABCDEF1234567890 keep it",
        reply="ok",
        intent="general",
    )
    summary = mem.get_session_summary(sid)
    assert "sk-ABCDEF1234567890ABCDEF1234567890" not in summary["summary"]


def test_conversation_memory_recap_does_not_record_meta_turns(conversation_memory) -> None:
    mem = conversation_memory
    sid = "memmeta"
    # A recap/soul reply should never be folded back into the running summary.
    mem.record_turn(session_id=sid, user_text="what did we discuss", reply="...", intent="continuity_session_recall")
    mem.record_turn(session_id=sid, user_text="show me your soul", reply="...", intent="soul_identity")
    assert mem.get_session_summary(sid)["turn_count"] == 0


def test_continuity_recall_includes_conversation_memory(conversation_memory) -> None:
    mem = conversation_memory
    sid = "recalltest"
    mem.record_turn(session_id=sid, user_text="we planned the Stripe billing integration", reply="ok", intent="general")

    from aethos_core.continuity_intelligence.conversational_identity_runtime import (
        compose_conversational_identity_reply,
    )

    reply = compose_conversational_identity_reply("what did we discuss", session_id=sid)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "continuity_session_recall"
    assert "stripe billing" in body.lower()
    assert meta.get("conversation_recall") == "true"


# ── §2 — soul / identity answering ──────────────────────────────────────────


@pytest.mark.parametrize(
    "prompt",
    [
        "show me your soul",
        "what do you value",
        "how were you created",
        "what is your purpose",
        "tell me about yourself",
    ],
)
def test_soul_identity_prompts_answer_from_soul(prompt: str) -> None:
    from aethos_core.continuity_intelligence.conversational_identity_runtime import (
        compose_conversational_identity_reply,
        is_identity_soul_prompt,
    )

    assert is_identity_soul_prompt(prompt)
    reply = compose_conversational_identity_reply(prompt, session_id="soultest")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "soul_identity"
    assert meta.get("source") == "SOUL.md"
    # A genuine answer, not a therapist-style deflection.
    assert "what made you ask" not in body.lower()
    assert "AethOS" in body
    assert len(body) > 120


def test_capability_question_is_not_soul() -> None:
    from aethos_core.continuity_intelligence.conversational_identity_runtime import is_identity_soul_prompt

    assert not is_identity_soul_prompt("what are you capable of?")
    assert not is_identity_soul_prompt("what can you do")
    # "who are you" / "who created you" are handled by the platform-identity path.
    assert not is_identity_soul_prompt("who are you")
    assert not is_identity_soul_prompt("who created you")


def test_identity_front_door_intent_routes_to_soul() -> None:
    from aethos_core.chat.front_door_intent import classify_front_door_intent, compose_front_door_reply

    assert classify_front_door_intent("how were you created") == "identity"
    assert classify_front_door_intent("what do you value") == "identity"

    composed = compose_front_door_reply("identity", text="show me your soul", session_id="fd")
    assert composed is not None
    body, intent, _meta = composed
    assert intent == "soul_identity"
    assert "AethOS" in body


# ── §3 — Multi-Model Arbiter ────────────────────────────────────────────────


def _fake_sync_complete(provider: str, model_id: str, prompt: str, tenant_id: str | None = None) -> dict:
    if "peer-review" in prompt or "accuracy_score" in prompt:
        return {
            "text": json.dumps(
                {
                    "accuracy_score": 0.9,
                    "completeness_score": 0.85,
                    "reasoning_score": 0.9,
                    "recommended": True,
                    "critique": "Clear and well reasoned.",
                }
            ),
            "input_tokens": 5,
            "output_tokens": 5,
            "used_llm": True,
            "error": None,
        }
    return {
        "text": f"A grounded answer from {model_id}.",
        "input_tokens": 5,
        "output_tokens": 8,
        "used_llm": True,
        "error": None,
    }


@pytest.fixture
def arbiter_ready(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "arbiter_enabled", True, raising=False)
    monkeypatch.setattr(s, "arbiter_blind_critique", True, raising=False)
    monkeypatch.setattr(s, "arbiter_max_rounds", 1, raising=False)
    monkeypatch.setattr(s, "local_llm_enabled", True, raising=False)
    monkeypatch.setattr(s, "local_llm_base_url", "http://localhost:11434", raising=False)
    monkeypatch.setattr(s, "arbiter_model_pool", "local:model-a,local:model-b", raising=False)
    from aethos_core.arbiter import dispatcher

    monkeypatch.setattr(dispatcher, "_sync_complete", _fake_sync_complete)
    yield s


def test_arbiter_lifecycle_smoke(arbiter_ready) -> None:
    from aethos_core.arbiter.service import run_arbiter_session

    pool = [
        {"provider": "local", "model_id": "model-a", "label": "Model A"},
        {"provider": "local", "model_id": "model-b", "label": "Model B"},
    ]
    session = asyncio.run(
        run_arbiter_session("Should we cache this endpoint at the edge?", model_pool_override=pool)
    )
    assert session.status.value in {"completed", "no_consensus"}
    assert len([r for r in session.responses if not r.error]) == 2
    assert session.rounds_completed >= 2  # dispatch + critique
    assert session.critiques  # cross-critique happened
    assert session.consensus is not None
    assert session.artifact_id  # artifact stored for the audit trail


def test_arbiter_run_tool_disabled_states_precondition(monkeypatch) -> None:
    s = get_settings()
    monkeypatch.setattr(s, "arbiter_enabled", False, raising=False)
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    out = json.loads(execute_agent_tool("arbiter_run", {"prompt": "compare X and Y"}, session_id="default"))
    assert out["ok"] is False
    assert out["error"] == "arbiter_disabled"
    assert "ARBITER_ENABLED" in out["hint"]


def test_arbiter_run_schema_gated_by_flag(monkeypatch) -> None:
    s = get_settings()
    from aethos_core.execution_brain.agent_tool_executor import agent_tool_schemas

    monkeypatch.setattr(s, "arbiter_enabled", False, raising=False)
    assert "arbiter_run" not in {t["name"] for t in agent_tool_schemas()}

    monkeypatch.setattr(s, "arbiter_enabled", True, raising=False)
    assert "arbiter_run" in {t["name"] for t in agent_tool_schemas()}


def test_arbiter_run_tool_full_run(arbiter_ready) -> None:
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    out = json.loads(
        execute_agent_tool(
            "arbiter_run",
            {"prompt": "Which caching strategy is safest for production?"},
            session_id="default",
        )
    )
    assert out["ok"] is True
    assert out["responding_models"] == 2
    assert out["consensus"] is not None
    assert out["panel"] == "Arbiter"  # real sidebar label (was the wrong "Multi-model arbiter")

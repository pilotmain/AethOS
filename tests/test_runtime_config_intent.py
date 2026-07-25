# SPDX-License-Identifier: Apache-2.0
"""Runtime provider/model question routing — broad phrasing."""

from __future__ import annotations

from aethos_core.chat.handlers import resolve_handler
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_thread_memory.thread_reply_composer import compose_operational_thread_followup
from aethos_core.runtime.runtime_config_intent import is_runtime_provider_config_question
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_classifier import classify_runtime_prompt


def test_broad_model_phrasing_detected():
    samples = [
        "can you check which anthropic model you are using now?",
        "what model are we using",
        "which LLM is configured?",
        "tell me the active claude model",
        "runtime config",
        "what provider powers this session?",
    ]
    for text in samples:
        assert is_runtime_provider_config_question(text), text


def test_model_eval_not_config_question():
    assert not is_runtime_provider_config_question("run blind model eval on gpt vs claude")


def test_classify_provider_attribution_flexible_phrasing():
    assert classify_runtime_prompt("can you check which anthropic model you are using now?") == (
        "provider_attribution_response"
    )


def test_thread_followup_yields_for_model_question():
    reply = compose_operational_thread_followup(
        "can you check which anthropic model you are using now?",
        session_id="no-thread",
    )
    assert reply is None


def test_resolve_handler_returns_model_not_stale_thread():
    handled = resolve_handler(
        "can you check which anthropic model you are using now?",
        session_id="cfg-intent",
    )
    assert handled is not None
    body, intent, _meta = handled
    assert intent in {"provider_attribution_response", "runtime_config_query"}
    assert "don't have an active operational mutation thread" not in body.lower()
    assert "claude" in body.lower() or "anthropic" in body.lower() or "model" in body.lower()


def test_chat_turn_regression():
    result = resolve_chat_turn(
        "can you check which anthropic model you are using now?",
        session_id="cfg-chat",
        apply_relational_layer=False,
    )
    assert result.intent in {"provider_attribution_response", "runtime_config_query"}
    assert "don't have an active operational mutation thread" not in result.reply.lower()


def test_surface_metadata_recorded_on_turn():
    """handoff §1/§11 — inbound surface is normalized and stamped on the turn meta."""
    result = resolve_chat_turn(
        "can you check which anthropic model you are using now?",
        session_id="cfg-surface",
        surface="Voice",
        apply_relational_layer=False,
    )
    assert result.meta.get("surface") == "voice"


def test_surface_defaults_to_webchat():
    result = resolve_chat_turn(
        "can you check which anthropic model you are using now?",
        session_id="cfg-surface-default",
        apply_relational_layer=False,
    )
    assert result.meta.get("surface") == "webchat"

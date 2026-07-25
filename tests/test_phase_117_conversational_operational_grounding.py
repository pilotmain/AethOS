# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7 — Conversational operational grounding tests."""

from __future__ import annotations

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.continuity_reconstruction.prompt_inference import infer_continuity_intent
from aethos_core.continuity_reconstruction.thread_recovery import reconstruct_operational_thread
from aethos_core.conversation.legacy_polish_api import orchestrate_operational_grounding
from aethos_core.conversation.legacy_polish_api import synthesize_grounded_operational_reply
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.conversation.polish_compat import is_generic_ai_response, reshape_generic_response
from aethos_core.governance_restraint_runtime.restraint_runtime import assess_governance_restraint
from aethos_core.operational_context_memory.context_store import persist_operational_context
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.conversation.operational_memory import clear_operational_memory_for_tests, persist_investigation, record_focus_recovery


def _seed_session(session_id: str = "test-grounding") -> None:
    clear_operational_memory_for_tests()
    record_focus_recovery(session_id=session_id, focus="replay continuity durability", channel="telegram")
    persist_investigation(session_id=session_id, investigation="deployment recovery stabilization")
    persist_operational_context(
        session_id=session_id,
        context={
            "deployment_subject": "Railway production deployment",
            "replay_concern": "replay continuity durability",
            "latest_recovery_narrative": "Recovery progressing across verification windows.",
        },
    )


def test_conversational_operational_grounding_aggregate():
    _seed_session()
    state = assess_conversational_operational_grounding(session_id="test-grounding", channel="telegram")
    assert state["phase"] == "11.8.2"
    assert state["ok"] is True
    assert "operational grounding" in state["summary"].lower()
    assert "continuity collapse" in state["narrative"].lower()


def test_infer_continuity_intent():
    improved = infer_continuity_intent("Has the situation improved?")
    assert improved["continuity_prompt"] is True
    assert improved["intent"] == "situation_improved"
    deployment = infer_continuity_intent("Did the deployment fully stabilize?")
    assert deployment["continuity_prompt"] is True
    assert deployment["intent"] == "deployment_stabilized"


def test_synthesize_grounded_operational_reply():
    _seed_session()
    result = synthesize_grounded_operational_reply(
        user_text="Has the situation improved?",
        session_id="test-grounding",
        channel="telegram",
    )
    assert result is not None
    assert result["grounded"] is True
    assert "signals" in result["reply"].lower() or "trajectory" in result["reply"].lower()
    assert "approval-gated" not in result["reply"].lower()


def test_anti_generic_ai_reshape():
    _seed_session()
    thread = reconstruct_operational_thread(session_id="test-grounding", channel="telegram")
    generic = "I'd need more context about which specific deployment you're referring to."
    assert is_generic_ai_response(generic) is True
    reshaped = reshape_generic_response(generic, context=thread, intent="deployment_stabilized")
    assert "operationally stable" in reshaped.lower()
    assert "approval-gated" not in reshaped.lower()


def test_governance_restraint_suppression():
    restraint = assess_governance_restraint(intent="situation_improved", channel="telegram", grounded=True)
    assert restraint["suppress_footer"] is True
    assert restraint["visibility"] == "none"


def test_orchestrate_operational_grounding():
    _seed_session()
    grounding = orchestrate_operational_grounding(session_id="test-grounding", channel="telegram")
    assert grounding["grounded"] is True
    assert "continuity" in grounding["summary"].lower()


def test_resolve_chat_turn_grounded():
    _seed_session("test-chat-grounding")
    result = resolve_chat_turn(
        "Did the deployment fully stabilize?",
        session_id="test-chat-grounding",
        channel="telegram",
    )
    assert "stabiliz" in result.reply.lower() or "mismatch" in result.reply.lower() or "confirme" in result.reply.lower()
    assert "approval-gated" not in result.reply.lower()
    assert result.meta.get("lane") in {"operational_grounding", "agent_runtime"} or result.intent in {
        "deployment_stabilized",
        "agent_runtime",
    }


def test_telegram_thinking_activity_type():
    from aethos_core.channels.activity import infer_channel_activity_type

    assert infer_channel_activity_type("Has recovery stabilized?") == "operational_grounding"


def test_capability_matrix_conversational_operational_grounding():
    matrix = build_capability_truth_matrix()
    cog = next((r for r in matrix if r.get("id") == "conversational_operational_grounding"), None)
    assert cog is not None and cog["verification_coverage_pct"] >= 89

# SPDX-License-Identifier: Apache-2.0
"""Part B regression corpus — pilotmain.com multi-turn conversation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aethos_core.chat.chat_intent_gate import classify_chat_turn_gate, is_meta_complaint_turn
from aethos_core.chat.chat_turn_steps import try_operational_fast_path_turn, try_single_loop_turn
from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent
from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.progression_compat import (
    append_optional_rest_hint,
    reset_rest_nudge_state_for_tests,
)
from aethos_core.execution_brain.agent_runtime import AgentRuntimeResult
from aethos_core.identity.trust_language import LIGHT_TRUST_REMINDER
from aethos_core.memory.conversation_summary_memory import reset_for_tests as reset_conversation_memory


SESSION = "sess-pilotmain-corpus"
SUMMARY_BODY = (
    "# pilotmain.com\n\nPilotMain is an AI operations platform. "
    "It helps teams deploy and govern agents."
)
IMPROVED_1 = (
    "PilotMain is a governed AI operations layer for teams who ship fast but need "
    "approval gates, provider inventory, and chat-first control."
)
IMPROVED_2 = (
    "Think of PilotMain as your operator cockpit: one chat surface, governed mutations, "
    "and live visibility across Railway, Vercel, and GitHub."
)
ACK_REPEAT = (
    "You're right — I'll give you a fresh take instead of repeating the scrape."
)
TWO_PAGE_PROSE = (
    "## PilotMain — two-page overview\n\n"
    "PilotMain is a governed AI operations platform built for teams that ship agents "
    "into production without losing control. The chat surface is the primary control plane: "
    "operators ask in natural language, AethOS grounds answers in live provider state, and "
    "every mutation routes through approval gates before anything touches Railway, Vercel, or GitHub.\n\n"
    "## Architecture and governance\n\n"
    "Under the hood, AethOS maintains provider inventory, deployment targets, credential vault "
    "hydration, and Mission Control visibility. Multi-tenant isolation keeps each organization's "
    "sessions, secrets, and audit trails separate. The agent runtime can call read-only tools "
    "immediately while writes always create governed preflights the operator approves in Mission Control.\n\n"
    "## Operator experience\n\n"
    "Mission Control surfaces orchestration, jobs, connections, and canvas renders alongside chat. "
    "Conversation memory rolls forward so follow-ups like 'expand that' or 'give me a better description' "
    "stay on the same subject without re-asking. Hosted deployments configure capabilities through "
    "Railway variables — not local .env files on the operator's laptop."
)
SINGLE_LOOP_SESSION = "sess-single-loop-corpus"


@pytest.fixture(autouse=True)
def _clean_memory(tmp_path, monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "conversation_memory_dir", str(tmp_path / "conv_mem"))
    get_settings.cache_clear()
    reset_conversation_memory()
    reset_rest_nudge_state_for_tests()
    yield
    reset_conversation_memory()
    reset_rest_nudge_state_for_tests()
    get_settings.cache_clear()


def _mock_summary_provider():
    from aethos_core.research.research_provider import WebsiteSummary

    summary = WebsiteSummary(
        ok=True,
        url="https://pilotmain.com",
        title="PilotMain",
        meta_description="AI operations platform.",
        visible_text_preview=SUMMARY_BODY,
        artifact_ids=["art-1"],
        confidence="high",
    )
    provider = MagicMock()
    provider.summarize_url.return_value = summary
    return provider


def _run_corpus():
    turns = [
        "summarize pilotmain.com",
        "please give me the summary here in chat",
        "no I'm talking about pilotmain.com",
        "would you agree with the description or suggest better",
        "give me a better description",
        "why are you repeating the same description",
        "why aren't you responding",
    ]
    replies: list[str] = []
    intents: list[str] = []

    llm_replies = [IMPROVED_1, IMPROVED_1, IMPROVED_1, IMPROVED_1, IMPROVED_2, ACK_REPEAT + " " + IMPROVED_2, "I'm here — what would you like next on pilotmain.com?"]
    llm_idx = 0

    def fake_complete(user_text, *, session_id=SESSION, channel="chat", system_overlay=None, **kwargs):
        from aethos_core.provider.completion import ProviderResult

        nonlocal llm_idx
        text = llm_replies[min(llm_idx, len(llm_replies) - 1)]
        llm_idx += 1
        return ProviderResult(text=text, provider="test", model="test", used_llm=True)

    from aethos_core.config import get_settings

    settings = get_settings()
    with patch(
        "aethos_core.research.research_provider.get_research_provider",
        return_value=_mock_summary_provider(),
    ), patch(
        "aethos_core.provider.completion.complete_chat",
        side_effect=fake_complete,
    ), patch.object(settings, "agent_runtime_enabled", True), patch.object(
        settings, "conversation_memory_enabled", True
    ), patch.object(settings, "chat_single_loop_enabled", False), patch.object(
        settings, "aethos_onboarding_enabled", False
    ):
        for text in turns:
            result = resolve_chat_turn(text, session_id=SESSION, interaction_mode="agent")
            replies.append(result.reply or "")
            intents.append(result.intent or "")

    return replies, intents


def test_part_b_corpus_pilotmain_multi_turn():
    replies, intents = _run_corpus()

    assert "pilotmain" in replies[0].lower()
    assert "pilotmain" in replies[1].lower()
    assert "what do you want to summarize" not in replies[1].lower()
    assert "pilotmain" in replies[2].lower()
    assert "don't see the description" not in replies[3].lower()
    assert "deployment recovery" not in replies[4].lower()
    assert replies[4] != replies[0]
    assert "deployment target registry" not in replies[6].lower()
    assert "responding` is not" not in replies[6].lower()
    assert all("pilotmain" in r.lower() or "here" in r.lower() for r in replies[3:])


def test_responding_is_not_deployment_target():
    assert is_meta_complaint_turn("why aren't you responding")
    gate = classify_chat_turn_gate("why aren't you responding", session_id=SESSION)
    assert gate.intent == "follow_up"
    assert detect_explicit_mutation_intent("why aren't you responding") is None
    assert create_mutation_preflight_job_reply("why aren't you responding") is None


def test_rest_nudge_at_most_once_per_session():
    reset_rest_nudge_state_for_tests()
    hits = 0
    for _ in range(30):
        out = append_optional_rest_hint("ok", session_id=SESSION)
        if "---" in out and "rest" in out.lower() or "sleep" in out.lower():
            hits += 1
    assert hits <= 1


def test_conversational_gate_blocks_operational_scramble():
    gate = classify_chat_turn_gate("give me a better description", session_id=SESSION)
    assert gate.intent == "follow_up"
    with patch("aethos_core.chat.cognition_exception_boundary.safe_resolve_operational_turn") as scramble:
        result = try_operational_fast_path_turn(
            "give me a better description",
            session_id=SESSION,
            channel="chat",
            emotional_context=None,
        )
        scramble.assert_not_called()
    assert result is None or result.intent.startswith("conversational")


def _mock_agent_runtime_side_effect(replies: list[str]):
    idx = 0

    def _fake(
        text,
        *,
        session_id="default",
        channel="chat",
        model_override=None,
        tenant_id=None,
        surface="webchat",
    ):
        nonlocal idx
        body = replies[min(idx, len(replies) - 1)]
        idx += 1
        return AgentRuntimeResult(
            reply=body,
            used_llm=True,
            provider="test",
            model="test",
            meta={
                "lane": "agent_runtime",
                "session_id": session_id,
                "suppress_governance_footer": "true",
            },
        )

    return _fake


def _run_single_loop_corpus():
    turns = [
        "summarize pilotmain.com",
        "expand this into two pages",
        "im still waiting",
        "give me a better description",
        "why are you repeating",
        "why aren't you responding",
    ]
    agent_replies = [
        SUMMARY_BODY,
        TWO_PAGE_PROSE,
        "Here is the full two-page write-up you asked for on pilotmain.com.\n\n" + TWO_PAGE_PROSE,
        IMPROVED_2,
        ACK_REPEAT + " " + IMPROVED_1,
        "I'm here — still working on pilotmain.com. What would you like next?",
    ]
    replies: list[str] = []

    from aethos_core.config import get_settings

    settings = get_settings()
    with patch(
        "aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn",
        side_effect=_mock_agent_runtime_side_effect(agent_replies),
    ), patch("aethos_core.chat.chat_turn_steps.try_operational_fast_path_turn") as scramble, patch.object(
        settings, "agent_runtime_enabled", True
    ), patch.object(settings, "conversation_memory_enabled", True), patch.object(
        settings, "chat_single_loop_enabled", True
    ), patch.object(settings, "aethos_onboarding_enabled", False), patch.object(
        settings, "canvas_surface_enabled", True
    ):
        for text in turns:
            result = resolve_chat_turn(text, session_id=SINGLE_LOOP_SESSION, interaction_mode="chat")
            replies.append(result.reply or "")
            scramble.assert_not_called()

    return replies


def test_single_loop_corpus_pilotmain_and_two_page():
    replies = _run_single_loop_corpus()

    assert "pilotmain" in replies[0].lower()
    assert "operational report" not in replies[1].lower()
    assert len(replies[1]) > 400
    assert "pilotmain" in replies[2].lower()
    assert "deployment recovery" not in replies[3].lower()
    assert replies[3] != replies[0]
    assert "deployment target registry" not in replies[5].lower()
    assert "responding` is not" not in replies[5].lower()
    assert all("pilotmain" in r.lower() or "here" in r.lower() for r in replies[2:])


def test_single_loop_no_governance_footer_on_writing_turn():
    with patch(
        "aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn",
        return_value=AgentRuntimeResult(
            reply=TWO_PAGE_PROSE,
            used_llm=True,
            meta={"single_loop": "true", "suppress_governance_footer": "true"},
        ),
    ):
        from aethos_core.config import get_settings

        settings = get_settings()
        with patch.object(settings, "chat_single_loop_enabled", True), patch.object(
            settings, "agent_runtime_enabled", True
        ), patch.object(settings, "conversation_memory_enabled", True):
            result = resolve_chat_turn(
                "expand this into two pages about pilotmain.com",
                session_id=SINGLE_LOOP_SESSION,
            )
    assert LIGHT_TRUST_REMINDER not in (result.reply or "")


def test_single_loop_rest_nudge_not_on_every_reply():
    reset_rest_nudge_state_for_tests()
    nudge_hits = 0
    with patch(
        "aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn",
        return_value=AgentRuntimeResult(reply="ok", meta={"suppress_governance_footer": "true"}),
    ):
        from aethos_core.config import get_settings

        settings = get_settings()
        with patch.object(settings, "chat_single_loop_enabled", True), patch.object(
            settings, "agent_runtime_enabled", True
        ), patch.object(settings, "conversation_memory_enabled", True):
            for _ in range(20):
                result = resolve_chat_turn("tell me more about pilotmain.com", session_id=SINGLE_LOOP_SESSION)
                if "---" in (result.reply or "") and (
                    "rest" in (result.reply or "").lower() or "sleep" in (result.reply or "").lower()
                ):
                    nudge_hits += 1
    assert nudge_hits == 0


def test_single_loop_canvas_render_command():
    from aethos_core.canvas.canvas_store import clear_canvas_for_tests, get_canvas_state
    from aethos_core.execution_brain.agent_runtime import run_agent_runtime_turn

    clear_canvas_for_tests()
    from aethos_core.config import get_settings

    settings = get_settings()
    with patch.object(settings, "chat_single_loop_enabled", True), patch.object(
        settings, "agent_runtime_enabled", True
    ), patch.object(settings, "conversation_memory_enabled", True), patch.object(
        settings, "canvas_surface_enabled", True
    ), patch(
        "aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn",
        side_effect=run_agent_runtime_turn,
    ), patch(
        "aethos_core.execution_brain.agent_runtime.should_use_agent_runtime",
        return_value=True,
    ), patch(
        "aethos_core.provider.completion.provider_configured",
        return_value=True,
    ), patch(
        "aethos_core.provider.completion.complete_chat",
    ) as mock_chat:
        from aethos_core.provider.completion import ProviderResult

        mock_chat.return_value = ProviderResult(
            text="Rendered a job timeline to the Canvas — open the Canvas tab to view.",
            used_llm=True,
            provider="anthropic",
            model="claude-test",
        )
        result = resolve_chat_turn(
            "render a job timeline on the canvas",
            session_id=SINGLE_LOOP_SESSION,
        )
    assert result.intent == "agent_runtime"
    canvas_state = get_canvas_state(session_id=SINGLE_LOOP_SESSION)
    assert canvas_state["view_count"] == 1
    assert canvas_state["views"][0]["view_type"] in {"job_timeline", "table"}


def test_single_loop_subject_persists_with_memory_only():
    """Corpus item 7 — pilotmain subject carries without extra memory flags."""
    from aethos_core.config import get_settings
    from aethos_core.memory.conversation_summary_memory import get_session_summary, record_turn

    settings = get_settings()
    record_turn(
        session_id=SINGLE_LOOP_SESSION,
        user_text="summarize pilotmain.com",
        reply=SUMMARY_BODY[:200],
        intent="agent_runtime",
    )
    row = get_session_summary(SINGLE_LOOP_SESSION)
    summary_text = str(row.get("summary") or "")
    assert summary_text and "pilotmain" in summary_text.lower()

    with patch(
        "aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn",
        return_value=AgentRuntimeResult(
            reply=IMPROVED_2,
            used_llm=True,
            meta={"suppress_governance_footer": "true"},
        ),
    ):
        with patch.object(settings, "chat_single_loop_enabled", True), patch.object(
            settings, "agent_runtime_enabled", True
        ), patch.object(settings, "conversation_memory_enabled", True), patch.object(
            settings, "vector_memory_enabled", False
        ):
            result = resolve_chat_turn(
                "give me a better description",
                session_id=SINGLE_LOOP_SESSION,
            )
    assert "pilotmain" in (result.reply or "").lower() or "governed" in (result.reply or "").lower()


def test_single_loop_mutation_gate_blocks_scramble():
    with patch(
        "aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn",
        return_value=AgentRuntimeResult(reply=IMPROVED_1, meta={"suppress_governance_footer": "true"}),
    ), patch("aethos_core.chat.cognition_exception_boundary.safe_resolve_operational_turn") as scramble:
        result = try_single_loop_turn(
            "give me a better description",
            session_id=SINGLE_LOOP_SESSION,
            channel="chat",
        )
        scramble.assert_not_called()
    assert result is not None
    assert str(result.meta.get("single_loop") or "") == "true"

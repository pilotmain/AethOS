# SPDX-License-Identifier: Apache-2.0
"""Conversational turns — memory-aware LLM answers without operational router scramble."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aethos_core.chat.chat_intent_gate import ChatTurnGate
    from aethos_core.chat.service import ChatTurnResult


_CONVERSATIONAL_OVERLAY = (
    "You are answering in AethOS chat. Use the conversation memory below.\n"
    "- For follow-ups, continue the SAME topic — never ask what to summarize if the subject is known.\n"
    "- For 'better description' / 'suggest better', WRITE a new improved marketing-style description "
    "from prior content — do not re-print the raw scrape verbatim.\n"
    "- For meta complaints ('why repeating', 'why not responding'), acknowledge briefly and answer normally.\n"
    "- Never mention deployment target registries, mutation preflights, or enabling memory flags.\n"
    "- Never treat words like 'responding' or 'description' as service names."
)


def _conversational_overlay(session_id: str) -> str:
    from aethos_core.chat.conversation_context import compose_conversation_llm_context

    ctx = compose_conversation_llm_context(session_id)
    if not ctx:
        return _CONVERSATIONAL_OVERLAY
    return f"{_CONVERSATIONAL_OVERLAY}\n\n{ctx}"


def try_conversational_turn(
    text: str,
    *,
    session_id: str,
    channel: str,
    gate: "ChatTurnGate",
) -> "ChatTurnResult | None":
    from aethos_core.chat.chat_intent_gate import ChatTurnGate
    from aethos_core.chat.service import ChatTurnResult
    from aethos_core.chat.web_intelligence import execute_web_intelligence, is_web_intelligence_request
    from aethos_core.provider.completion import complete_chat

    raw = (text or "").strip()
    if not raw:
        return None

    overlay = _conversational_overlay(session_id)

    # Fresh summarize/inspect with explicit URL/domain — web lane, then memory records it.
    if gate.intent == "question" and is_web_intelligence_request(raw):
        from aethos_core.chat.conversation_context import extract_topic_from_text

        if extract_topic_from_text(raw) or gate.topic:
            web = execute_web_intelligence(raw, session_id=session_id, channel=channel)
            if web is not None:
                body, intent, meta = web
                meta = dict(meta)
                meta["lane"] = "conversational_web"
                meta["session_id"] = session_id
                return ChatTurnResult(
                    reply=body,
                    intent=intent,
                    provider_stream=False,
                    used_llm=False,
                    meta={k: str(v) for k, v in meta.items()},
                )

    if gate.intent == "chitchat":
        overlay = overlay + "\nReply in one or two short, warm sentences."

    prov = complete_chat(
        raw,
        session_id=session_id,
        channel=channel,
        system_overlay=overlay,
    )
    intent = "conversational_follow_up" if gate.intent == "follow_up" else "conversational_answer"
    if gate.intent == "chitchat":
        intent = "chitchat"
    meta = {
        "lane": "conversational_turn",
        "route_id": "chat_intent_gate",
        "chat_gate_intent": gate.intent,
        "session_id": session_id,
        "topic": gate.topic or "",
    }
    return ChatTurnResult(
        reply=prov.text,
        intent=intent,
        provider_stream=False,
        used_llm=prov.used_llm,
        meta=meta,
    )

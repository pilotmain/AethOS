# SPDX-License-Identifier: Apache-2.0
"""Conversation memory block for LLM context — rolling summary + recent turns + topic."""

from __future__ import annotations

import re

_DOMAIN_RX = re.compile(
    r"\b([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b",
    re.I,
)

_TOPIC_HINT_RX = re.compile(
    r"\b(?:about|summarize|summary of|talking about|referring to|for)\s+([a-z0-9][a-z0-9.-]*\.[a-z]{2,})",
    re.I,
)


def extract_topic_from_text(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    from aethos_core.research.website_summary import extract_url_from_text

    url = extract_url_from_text(raw)
    if url:
        return url.replace("https://", "").replace("http://", "").strip("/")
    m = _TOPIC_HINT_RX.search(raw)
    if m:
        return m.group(1).lower()
    domains = _DOMAIN_RX.findall(raw)
    if domains:
        return domains[0].lower()
    return None


def extract_session_topic(session_id: str) -> str | None:
    """Best-effort current subject from stored conversation memory."""
    from aethos_core.memory.conversation_summary_memory import get_recent_turns, get_session_summary

    sid = (session_id or "default").strip() or "default"
    for turn in reversed(get_recent_turns(sid, limit=12)):
        topic = extract_topic_from_text(str(turn.get("user_text") or ""))
        if topic:
            return topic
        topic = extract_topic_from_text(str(turn.get("reply_preview") or ""))
        if topic:
            return topic
    summary = str(get_session_summary(sid).get("summary") or "")
    return extract_topic_from_text(summary)


def compose_conversation_llm_context(session_id: str, *, max_turns: int = 8) -> str:
    """Rolling summary + recent verbatim turns + resolved topic for the model."""
    from aethos_core.memory.conversation_summary_memory import (
        conversation_memory_enabled,
        get_recent_turns,
        get_session_summary,
    )

    if not conversation_memory_enabled():
        return ""

    sid = (session_id or "default").strip() or "default"
    parts: list[str] = [
        "Conversation memory (core — always on; do not ask the operator to enable flags):",
    ]
    row = get_session_summary(sid)
    summary = str(row.get("summary") or "").strip()
    if summary:
        parts.append(f"Rolling summary:\n{summary[:3500]}")
    turns = get_recent_turns(sid, limit=max_turns)
    if turns:
        parts.append("Recent turns (verbatim):")
        for t in turns[-max_turns:]:
            user = str(t.get("user_text") or "").strip().replace("\n", " ")
            reply = str(t.get("reply_preview") or "").strip().replace("\n", " ")
            if user:
                parts.append(f"- User: {user[:280]}")
            if reply:
                parts.append(f"  Assistant: {reply[:280]}")
    topic = extract_session_topic(sid)
    if topic:
        parts.append(f"Current topic/subject: {topic}")
        parts.append(
            "Follow-ups like 'better description', 'the same', 'why repeating', or "
            "'why aren't you responding' refer to this topic — never treat bare words "
            "like 'responding' as deployment targets."
        )
    if len(parts) <= 1:
        return ""
    return "\n".join(parts)

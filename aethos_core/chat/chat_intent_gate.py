# SPDX-License-Identifier: Apache-2.0
"""Single deterministic chat turn gate — one primary intent per turn."""

from __future__ import annotations

import re
from dataclasses import dataclass

_CHITCHAT_RX = re.compile(
    r"^(?:hi|hello|hey|good (?:morning|afternoon|evening)|thanks|thank you|yo|sup)[!.?\s]*$",
    re.I,
)

_FOLLOW_UP_RX = re.compile(
    r"(?:"
    r"\b(?:better|improved?|another|different|same)\b.{0,24}\b(?:description|summary|one|answer|version)\b|"
    r"\b(?:would you|do you)\s+(?:agree|suggest)\b|"
    r"\bgive me (?:a |the )?(?:better|improved?|another)\b|"
    r"\b(?:talking|referring) about\b|"
    r"\bno[, ]+i(?:'m| am) talking about\b|"
    r"\bthe same (?:description|summary|thing)\b|"
    r"\bhere in chat\b|"
    r"\bwhy (?:are you|do you keep)\s+repeat(?:ing)?\b|"
    r"\bwhy aren't you responding\b|"
    r"\bwhy (?:won't|won't you|don't you) respond\b|"
    r"\bstop repeating\b"
    r")",
    re.I,
)

_QUESTION_RX = re.compile(
    r"(?:^|\b)("
    r"how\s+do\s+i|how\s+to|where\s+do\s+i|what\s+is|what\s+are|can\s+you\s+tell|explain|"
    r"summarize|summarise|summary of|tell me about|look up|research|compare|inspect|analyze|analyse"
    r")\b",
    re.I,
)

_NON_DEPLOYMENT_TOKENS = frozenset(
    {
        "responding",
        "response",
        "repeating",
        "repeat",
        "description",
        "summary",
        "better",
        "same",
        "talking",
        "chat",
        "pilotmain",
    }
)


@dataclass(frozen=True)
class ChatTurnGate:
    intent: str  # command | follow_up | question | chitchat
    topic: str | None = None
    command_kind: str | None = None


def is_meta_complaint_turn(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(
        re.search(
            r"\bwhy (?:are you|do you keep) repeat(?:ing)?\b|"
            r"\bwhy aren't you responding\b|"
            r"\bwhy (?:won't|don't) you respond\b",
            raw,
            re.I,
        )
    )


def is_follow_up_turn(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if is_meta_complaint_turn(raw):
        return True
    if _FOLLOW_UP_RX.search(raw):
        return True
    from aethos_core.chat.conversation_context import extract_session_topic

    if extract_session_topic(session_id) and not _QUESTION_RX.search(raw):
        short = len(raw.split()) <= 14
        vague = bool(re.search(r"\b(?:that|it|this|same|better|here)\b", raw, re.I))
        if short and vague:
            return True
    return False


def is_explicit_command_turn(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if is_meta_complaint_turn(raw) or is_follow_up_turn(raw, session_id=session_id):
        return False
    if _CHITCHAT_RX.match(raw):
        return False
    from aethos_core.chat.informational_turn_classifier import is_explicit_operational_tool_command
    from aethos_core.chat.front_door_intent import is_canvas_render_request
    from aethos_core.agents.runtime.planner import is_command_center_orchestration_request

    if is_canvas_render_request(raw):
        return True
    if is_command_center_orchestration_request(raw, session_id=session_id):
        return True
    if is_explicit_operational_tool_command(raw):
        return True
    from aethos_core.chat.chat_turn_steps import classify_primary_intent

    primary = classify_primary_intent(raw, session_id=session_id)
    if primary in {"mutation", "deploy", "orchestration"}:
        return True
    from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent

    if detect_explicit_mutation_intent(raw, session_id=session_id) is not None:
        return True
    return False


def classify_chat_turn_gate(text: str, *, session_id: str = "default") -> ChatTurnGate:
    """Assign exactly one primary intent with clear precedence."""
    from aethos_core.chat.conversation_context import extract_session_topic, extract_topic_from_text

    raw = (text or "").strip()
    topic = extract_topic_from_text(raw) or extract_session_topic(session_id)

    if _CHITCHAT_RX.match(raw):
        return ChatTurnGate(intent="chitchat", topic=topic)

    if is_meta_complaint_turn(raw) or is_follow_up_turn(raw, session_id=session_id):
        return ChatTurnGate(intent="follow_up", topic=topic)

    if is_explicit_command_turn(raw, session_id=session_id):
        from aethos_core.chat.front_door_intent import is_canvas_render_request
        from aethos_core.agents.runtime.planner import is_command_center_orchestration_request
        from aethos_core.chat.chat_turn_steps import classify_primary_intent

        kind = classify_primary_intent(raw, session_id=session_id)
        if is_canvas_render_request(raw):
            kind = "canvas"
        if is_command_center_orchestration_request(raw, session_id=session_id):
            kind = "orchestration"
        return ChatTurnGate(intent="command", topic=topic, command_kind=kind)

    if _QUESTION_RX.search(raw) or topic:
        return ChatTurnGate(intent="question", topic=topic)

    return ChatTurnGate(intent="question", topic=topic)


def gate_blocks_operational_scramble(gate: ChatTurnGate) -> bool:
    return gate.intent != "command"


def token_is_safe_conversational(token: str) -> bool:
    t = (token or "").strip().lower()
    return t in _NON_DEPLOYMENT_TOKENS or len(t) < 6

# SPDX-License-Identifier: Apache-2.0
"""Safety short-circuit helpers — follow-up / meta-complaint detection (§D2)."""

from __future__ import annotations

import re

_FOLLOW_UP_RX = re.compile(
    r"\b(continue|keep going|go on|what about|and then|same thing|try again|one more)\b",
    re.I,
)
_QUESTION_RX = re.compile(r"\?|\b(what|why|how|when|where|who|can you|could you)\b", re.I)


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

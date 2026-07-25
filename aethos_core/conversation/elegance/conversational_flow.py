# SPDX-License-Identifier: Apache-2.0
"""Conversational flow — companion-style interaction."""

from __future__ import annotations

from aethos_core.conversation.elegance.calm_responses import calm_tone
from aethos_core.conversation.elegance.pacing_engine import pace_response
from aethos_core.conversation.elegance.premium_language import refine_language
from aethos_core.conversation.elegance.progressive_depth import trim_depth
from aethos_core.conversation.elegance.recommendation_followups import add_followups


def apply_conversational_flow(text: str, *, include_followups: bool = False) -> str:
    text = calm_tone(text)
    text = refine_language(text)
    text = pace_response(text)
    text = trim_depth(text)
    if include_followups:
        text = add_followups(text)
    return text.strip()

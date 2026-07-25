# SPDX-License-Identifier: Apache-2.0
"""Warmth engine — human-centered response shaping."""

from __future__ import annotations

from typing import Any


def apply_warmth(
    reply: str,
    *,
    emotional_context: dict[str, Any],
    include_governance_footer: bool = True,
    intent: str | None = None,
    lane: str | None = None,
) -> str:
    """Shape reply with relational warmth and identity convergence."""
    from aethos_core.identity.identity_runtime import align_outbound_reply

    mode = (emotional_context.get("mode") or {}).get("mode") or "companion"
    signals = emotional_context.get("signals") or {}
    text = reply.strip()

    if mode == "crisis":
        prefix = "I'm here with you. Let's focus on what matters right now.\n\n"
        text = prefix + text
    elif mode == "companion" and signals.get("frustrated"):
        prefix = "I hear the frustration — let's take this one step at a time.\n\n"
        text = prefix + text
    elif mode == "mentor" and signals.get("confused"):
        prefix = "Happy to walk through this clearly.\n\n"
        text = prefix + text
    elif mode == "executive":
        lines = text.split("\n")
        text = "**Summary**\n\n" + "\n".join(lines[:8])
        if len(lines) > 8:
            text += "\n\n*(Full detail available on request.)*"

    return align_outbound_reply(
        text,
        emotional_context=emotional_context,
        intent=intent,
        lane=lane,
        include_governance_footer=include_governance_footer,
    )


def reduce_verbosity(reply: str, *, max_paragraphs: int = 4) -> str:
    parts = [p.strip() for p in reply.split("\n\n") if p.strip()]
    if len(parts) <= max_paragraphs:
        return reply
    return "\n\n".join(parts[:max_paragraphs]) + "\n\n*(Additional detail available — ask if you want more.)*"

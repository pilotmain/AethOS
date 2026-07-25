# SPDX-License-Identifier: Apache-2.0
"""Conversational pacing — rhythm, compression, decisiveness balance."""

from __future__ import annotations

from typing import Any

# Above this confidence: lead with a clear operational read, uncertainty secondary.
_DECISIVE_THRESHOLD = 0.58
# Below this: short honest uncertainty, no operational report tone.
_HESITANT_THRESHOLD = 0.52


def pacing_profile(*, confidence: float, channel: str = "chat", certainty_tier: str = "moderate") -> dict[str, Any]:
    if confidence >= _DECISIVE_THRESHOLD:
        mode = "decisive"
    elif confidence >= _HESITANT_THRESHOLD:
        mode = "balanced"
    else:
        mode = "honest_brief"
    telegram = channel == "telegram" or channel.startswith("tg")
    return {
        "mode": mode,
        "compress": telegram or mode == "honest_brief",
        "max_paragraphs": 3 if telegram else 5,
        "lead_with_read": mode == "decisive",
        "summary": f"Conversational pacing: {mode}.",
    }


def decisive_uncertainty_lead(*, subject: str) -> str:
    """Honest but not hesitant — operational decisiveness with bounded uncertainty."""
    return f"Most likely you're asking about **{subject}**. "


def brief_low_confidence_reply(*, alt_subject: str | None = None) -> str:
    hint = f" Could also be **{alt_subject}**." if alt_subject else ""
    return (
        f"I don't have a strong enough thread match to call this definitively.{hint}\n\n"
        "Name the deployment, recovery window, or replay concern and I'll reconstruct precisely."
    )


def compress_for_channel(text: str, *, channel: str = "chat", max_paragraphs: int = 4) -> str:
    if channel not in {"telegram", "chat"} and not channel.startswith("tg"):
        return text
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(parts) <= max_paragraphs:
        return text
    return "\n\n".join(parts[:max_paragraphs])

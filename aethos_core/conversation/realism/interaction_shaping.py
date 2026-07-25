# SPDX-License-Identifier: Apache-2.0
"""Interaction shaping — low-friction Telegram and chat polish."""

from __future__ import annotations

import re
from typing import Any

_FORMULAIC_PHRASES = (
    "extended monitoring remains active",
    "verification windows",
    "dependency convergence",
    "topology convergence",
    "sustained verification",
    "operational resilience",
    "across extended operational horizons",
)

_BANNED_REPORT_OPENERS = (
    "operational systems continuously evaluated",
    "based on the recovery actions taken, i need to assess",
)


def shape_interaction(
    text: str,
    *,
    channel: str = "chat",
    pacing: dict[str, Any] | None = None,
) -> str:
    """Apply low-friction shaping — calm, fluid, not operational report generator."""
    shaped = text.strip()
    lower = shaped.lower()

    for opener in _BANNED_REPORT_OPENERS:
        if opener in lower:
            shaped = re.sub(re.escape(opener), "", shaped, flags=re.IGNORECASE).strip()

    # Collapse triple newlines
    shaped = re.sub(r"\n{3,}", "\n\n", shaped)

    pacing = pacing or {}
    if pacing.get("compress"):
        from aethos_core.conversation.realism.conversational_pacing import compress_for_channel

        shaped = compress_for_channel(
            shaped,
            channel=channel,
            max_paragraphs=int(pacing.get("max_paragraphs") or 3),
        )

    # Telegram: prefer conversational flow over dense bullet walls
    if channel == "telegram" or channel.startswith("tg"):
        lines = shaped.split("\n")
        bullet_count = sum(1 for ln in lines if ln.strip().startswith("- "))
        if bullet_count > 5:
            # Keep first 4 bullets max
            kept: list[str] = []
            bullets = 0
            for ln in lines:
                if ln.strip().startswith("- ") and bullets >= 4:
                    continue
                if ln.strip().startswith("- "):
                    bullets += 1
                kept.append(ln)
            shaped = "\n".join(kept)

    return shaped.strip()


def score_formulaic_density(text: str) -> dict[str, Any]:
    lower = text.lower()
    hits = sum(1 for phrase in _FORMULAIC_PHRASES if phrase in lower)
    dense = hits >= 2
    return {
        "formulaic_hits": hits,
        "dense": dense,
        "summary": "Prose reads naturally varied." if not dense else "Formulaic operational phrasing detected.",
    }

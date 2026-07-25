# SPDX-License-Identifier: Apache-2.0
"""Polish runtime — conversational realism polish orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.realism.conversational_pacing import pacing_profile
from aethos_core.conversation.realism.interaction_shaping import score_formulaic_density, shape_interaction
from aethos_core.conversation.realism.narrative_diversification import assess_narrative_entropy
from aethos_core.conversation.realism.semantic_diversification import assess_semantic_diversification
from aethos_core.conversation.realism.realism_runtime import assess_conversational_realism


def orchestrate_conversational_polish(
    *,
    reply: str = "",
    session_id: str = "default",
    channel: str = "chat",
    confidence: float = 0.6,
    certainty_tier: str = "moderate",
) -> dict[str, Any]:
    pacing = pacing_profile(confidence=confidence, channel=channel, certainty_tier=certainty_tier)
    shaped = shape_interaction(reply, channel=channel, pacing=pacing) if reply else ""
    formulaic = score_formulaic_density(shaped) if shaped else {"dense": False}
    semantic = assess_semantic_diversification()
    entropy = assess_narrative_entropy()
    realism = assess_conversational_realism(sample=shaped)

    polish_qualified = (
        realism.get("realism_active")
        and semantic.get("semantic_variants_enabled")
        and entropy.get("rotation_enabled")
        and not formulaic.get("dense")
    )

    return {
        "pacing": pacing,
        "semantic_diversification": semantic,
        "narrative_entropy": entropy,
        "formulaic_density": formulaic,
        "shaped_reply": shaped,
        "polish_qualified": polish_qualified,
        "summary": "Conversational realism polish active — semantic variation, pacing, and low-friction shaping enabled.",
    }


def assess_conversational_realism_polish(
    *,
    session_id: str = "default",
    channel: str = "chat",
    confidence: float = 0.6,
) -> dict[str, Any]:
    polish = orchestrate_conversational_polish(session_id=session_id, channel=channel, confidence=confidence)
    return {"ok": True, "phase": "11.7.3", **polish}

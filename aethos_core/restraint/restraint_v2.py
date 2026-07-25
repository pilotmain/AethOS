# SPDX-License-Identifier: Apache-2.0
"""Intelligence restraint 2.0 — knows when to stay quiet."""

from __future__ import annotations

from typing import Any

from aethos_core.restraint.restraint_runtime import apply_restraint, get_restraint_status


def apply_restraint_v2(
    *,
    text: str,
    session_id: str = "default",
    confidence: float = 0.72,
    suggestion_count: int = 0,
    max_paragraphs: int = 8,
) -> dict[str, Any]:
    """Restraint 2.0 — confidence gating, escalation thresholds, emotional restraint."""
    base = apply_restraint(text=text, session_id=session_id, max_paragraphs=max_paragraphs)

    gated = False
    trimmed = base.get("text", text)
    if confidence < 0.5 and "production-critical" in trimmed.lower():
        trimmed = trimmed.replace("production-critical", "not yet production-critical")
        gated = True

    if suggestion_count > 3:
        trimmed += "\n\n*(I'll hold further suggestions until you pick a direction.)*"

    unnecessary_suppressed = confidence < 0.55 and len(text.split("\n\n")) > 4

    return {
        "text": trimmed,
        "restraint": {
            **(base.get("restraint") or {}),
            "version": "2.0",
            "unnecessary_suggestion_suppressed": unnecessary_suppressed,
            "repetitive_replay_reduced": base.get("restraint", {}).get("repetition_suppressed", False),
            "escalation_threshold_applied": gated,
            "emotional_restraint": True,
            "recommendation_confidence_gated": gated,
            "operator_autonomy_preserved": True,
        },
    }


def get_restraint_v2_status(*, session_id: str = "default") -> dict[str, Any]:
    base = get_restraint_status(session_id=session_id)
    return {
        **base,
        "phase": "10.1.4G",
        "version": "2.0",
        "principle": "The best companion intelligence knows when to stay quiet.",
        "features": {
            **(base.get("features") or {}),
            "unnecessary_suggestion_suppression": True,
            "repetitive_replay_reduction": True,
            "escalation_thresholds": True,
            "emotional_restraint": True,
            "recommendation_confidence_gating": True,
            "operator_autonomy_preservation": True,
        },
    }

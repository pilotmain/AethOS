# SPDX-License-Identifier: Apache-2.0
"""Presence timing — human-like response pacing metadata."""

from __future__ import annotations

from typing import Any


LIVING_INTENT_LANES = frozenset({
    "conversation_resume",
    "operational_copilot",
    "live_presence_nudge",
    "teamwork_room",
    "living_intelligence",
    "ambient_presence",
    "operational_presence",
    "relational_state",
    "lifeos_domain",
    "collaboration_session",
})


def build_response_timing(*, intent: str = "generative_answer", phase_count: int = 2) -> dict[str, Any]:
    """Adaptive typing cadence and phased reply metadata."""
    streaming = intent in LIVING_INTENT_LANES or intent == "operational_copilot"
    return {
        "adaptive_typing_cadence_ms": 120 if streaming else 80,
        "streaming_operational_thought": streaming,
        "phased_reply": True,
        "phases": phase_count,
        "interruption_recovery": True,
        "collaboration_pacing": "calm",
    }


def should_skip_governance_footer(*, intent: str | None = None, lane: str | None = None) -> bool:
    """Living intelligence replies should not feel templated."""
    if lane in ("living_intelligence", "relational_intelligence", "presence_intelligence"):
        return True
    if intent in LIVING_INTENT_LANES:
        return True
    return False

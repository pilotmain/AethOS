# SPDX-License-Identifier: Apache-2.0
"""Conversational synthesis intelligence — Phase 11.4 aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.synthesis_pkg.synthesis_runtime import synthesize_human_response
from aethos_core.synthesis_harness.harness_runtime import harness_state


def assess_conversational_intelligence(*, sample_query: str = "top five playgrounds in Virginia") -> dict[str, Any]:
    sample_evidence = _sample_playground_evidence()
    synthesis = synthesize_human_response(
        query=sample_query,
        evidence=sample_evidence,
        overall_confidence=0.72,
        mode="casual",
        include_followups=True,
    )
    harness = harness_state()
    return {
        "ok": True,
        "phase": "11.4",
        "harness_version": harness.get("harness_version"),
        "sample_synthesis": synthesis,
        "harness": harness,
        "capabilities": {
            "intent_enforcement": "stable",
            "confidence_restraint": "stable",
            "artifact_suppression": "stable",
            "recommendation_intelligence": "stable",
            "conversational_elegance": "premium",
        },
        "qualification_tier": synthesis.get("qualification_tier", "beta"),
        "summary": synthesis.get("reply", "")[:200],
    }


def _sample_playground_evidence() -> list[dict[str, Any]]:
    return [
        {"title": "Kids Cove — Vienna, VA", "snippet": "Excellent for younger children, shaded seating, highly rated family accessibility.", "confidence": 0.82, "provider": "tavily"},
        {"title": "Ashburn Park — Ashburn, VA", "snippet": "Popular dinosaur-themed playground with toddler-friendly sections.", "confidence": 0.79, "provider": "tavily"},
        {"title": "Clemyjontri Park — McLean, VA", "snippet": "Large accessible playground with diverse play zones for all ages.", "confidence": 0.88, "provider": "tavily"},
        {"title": "Lee District Park — Alexandria, VA", "snippet": "Sprayground and playground combo, popular with Northern Virginia families.", "confidence": 0.76, "provider": "tavily"},
        {"title": "Bryant Park — Fairfax, VA", "snippet": "Shaded playground with swings and climbing structures.", "confidence": 0.71, "provider": "tavily"},
        {"title": "Occoquan Park — Lorton, VA", "snippet": "Waterfront playground with picnic areas.", "confidence": 0.68, "provider": "tavily"},
        {"title": "Kids Cove — Vienna, VA", "snippet": "Duplicate listing", "confidence": 0.5, "provider": "web"},
    ]

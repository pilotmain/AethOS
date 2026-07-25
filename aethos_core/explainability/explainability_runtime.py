# SPDX-License-Identifier: Apache-2.0
"""Explainability runtime — aggregate operational explanations."""

from __future__ import annotations

from typing import Any

from aethos_core.explainability.confidence_reasoning import explain_confidence_change
from aethos_core.explainability.governance_reasoning import explain_governance_escalation
from aethos_core.explainability.recommendation_reasoning import explain_recommendation
from aethos_core.explainability.replay_reasoning import explain_replay_gaps


def build_explainability_bundle(
    *,
    reliability: dict[str, Any],
    governance: dict[str, Any],
    recommendations: list[dict[str, Any]] | None = None,
    correlation: dict[str, Any] | None = None,
    replay_confidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build explainability bundle for all operational decisions."""
    confidence = reliability.get("confidence_detail") or {}
    replay_integrity = reliability.get("replay_integrity") or {}

    rec_explanations = [
        explain_recommendation(r, correlation=correlation) for r in (recommendations or [])[:4]
    ]

    return {
        "confidence": explain_confidence_change(confidence=confidence, reliability=reliability),
        "governance": explain_governance_escalation(governance),
        "replay": explain_replay_gaps(replay_integrity=replay_integrity, replay_confidence=replay_confidence),
        "recommendations": rec_explanations,
        "truth_state": reliability.get("truth_state"),
        "readonly": True,
    }

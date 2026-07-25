# SPDX-License-Identifier: Apache-2.0
"""Confidence translation — telemetry to human language."""

from __future__ import annotations

from aethos_core.human_trust.confidence_language import human_confidence_phrase
from aethos_core.human_trust.uncertainty_narratives import uncertainty_narrative


def translate_confidence(*, score: float, query: str = "", mode: str = "casual") -> str:
    if mode in ("engineering", "operator", "debug"):
        label = "high" if score >= 0.75 else "medium" if score >= 0.5 else "low"
        return f"Overall confidence: {label} / {score:.2f}"
    if score >= 0.55:
        return human_confidence_phrase(overall=score, query=query)
    return uncertainty_narrative(confidence=score)

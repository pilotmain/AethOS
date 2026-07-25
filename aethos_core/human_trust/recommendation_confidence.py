# SPDX-License-Identifier: Apache-2.0
"""Recommendation confidence — conversational certainty."""

from __future__ import annotations

from aethos_core.human_trust.confidence_language import human_confidence_phrase
from aethos_core.human_trust.uncertainty_narratives import uncertainty_narrative


def recommendation_confidence_phrase(*, overall: float, query: str) -> str:
    if overall >= 0.55:
        return human_confidence_phrase(overall=overall, query=query)
    return uncertainty_narrative(confidence=overall)

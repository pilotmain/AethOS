# SPDX-License-Identifier: Apache-2.0
"""Source weighting — trust scoring."""

from __future__ import annotations

_TRUSTED = frozenset({"tavily", "official", "gov", "edu"})


def weight_sources(*, confidence: float, provider: str = "") -> float:
    boost = 0.1 if any(t in provider.lower() for t in _TRUSTED) else 0.0
    return min(1.0, confidence + boost)

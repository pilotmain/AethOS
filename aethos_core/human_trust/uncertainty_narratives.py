# SPDX-License-Identifier: Apache-2.0
"""Uncertainty narratives — graceful uncertainty."""

from __future__ import annotations


def uncertainty_narrative(*, confidence: float) -> str:
    if confidence >= 0.7:
        return "These recommendations consistently appeared across trusted sources."
    if confidence >= 0.45:
        return "These options appeared across several sources, though details varied somewhat."
    return "I found some relevant options, but source agreement was limited — treat these as a starting point."

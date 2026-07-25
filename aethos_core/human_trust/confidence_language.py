# SPDX-License-Identifier: Apache-2.0
"""Confidence language — human confidence phrasing."""

from __future__ import annotations


def human_confidence_phrase(*, overall: float, query: str = "") -> str:
    if "playground" in query.lower() or "family" in query.lower() or "travel" in query.lower():
        return "highly rated family and travel sources"
    if overall >= 0.75:
        return "trusted regional and specialist sources"
    if overall >= 0.5:
        return "multiple reputable sources"
    return "available sources, with some variation in detail"

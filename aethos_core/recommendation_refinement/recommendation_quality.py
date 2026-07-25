# SPDX-License-Identifier: Apache-2.0
"""Recommendation quality — recommendation scoring."""

from __future__ import annotations

from typing import Any


def score_recommendation_quality(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return {"quality_score": 0.0, "summary": "No recommendations to score."}
    avg = sum(float(i.get("score") or 0) for i in items) / len(items)
    has_location = sum(1 for i in items if i.get("location")) / len(items)
    score = min(1.0, avg * 0.7 + has_location * 0.3)
    return {
        "quality_score": round(score, 2),
        "item_count": len(items),
        "summary": "Recommendation quality stable." if score >= 0.65 else "Recommendation quality building.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Operational trajectory — long-term stability trends."""

from __future__ import annotations

from typing import Any


def assess_operational_trajectory(*, memory: dict[str, Any]) -> dict[str, Any]:
    trend = memory.get("confidence", {}).get("trend") or "stable"
    incidents = memory.get("incidents", {}).get("count", 0)
    trajectory = "stable" if trend == "stable" and incidents < 5 else "watch" if incidents < 10 else "degrading"
    return {
        "trajectory": trajectory,
        "confidence_trend": trend,
        "summary": f"Long-term operational trajectory: {trajectory}.",
    }

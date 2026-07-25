# SPDX-License-Identifier: Apache-2.0
"""Bounded confidence normalization — never report confidence higher than reality."""

from __future__ import annotations

from typing import Any

MAX_CONFIDENCE = 0.96
MIN_CONFIDENCE = 0.25


def normalize_confidence(
    raw: float,
    *,
    telemetry_quality: str = "medium",
    stale_sources: int = 0,
    conflicting_evidence: bool = False,
    replay_gaps: int = 0,
) -> dict[str, Any]:
    """Apply bounded correction to raw confidence scores."""
    conf = float(raw)
    penalties: list[str] = []

    if telemetry_quality == "low":
        conf -= 0.12
        penalties.append("low telemetry quality")
    elif telemetry_quality == "medium" and stale_sources >= 1:
        conf -= 0.06
        penalties.append("partially stale telemetry")

    if stale_sources >= 2:
        conf -= 0.1
        penalties.append(f"{stale_sources} stale sources")

    if conflicting_evidence:
        conf -= 0.15
        penalties.append("conflicting evidence")

    if replay_gaps >= 1:
        conf -= min(0.08 * replay_gaps, 0.2)
        penalties.append(f"{replay_gaps} replay gap(s)")

    bounded = round(max(MIN_CONFIDENCE, min(conf, MAX_CONFIDENCE)), 2)
    return {
        "raw_confidence": round(raw, 2),
        "bounded_confidence": bounded,
        "confidence": "bounded",
        "penalties": penalties,
        "degraded": bounded < raw - 0.05,
    }

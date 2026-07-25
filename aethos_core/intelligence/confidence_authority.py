# SPDX-License-Identifier: Apache-2.0
"""Confidence authority — bounded operational trust scoring."""

from __future__ import annotations

from time import time
from typing import Any


def score_anomaly_confidence(
    *,
    event_count: int,
    recurring: bool = False,
    correlated_evidence: int = 0,
    memory_reinforcement: int = 0,
) -> float:
    base = min(0.55 + event_count * 0.08, 0.92)
    if recurring:
        base = min(base + 0.12, 0.95)
    base = min(base + correlated_evidence * 0.05, 0.97)
    base = min(base + memory_reinforcement * 0.03, 0.98)
    return round(max(0.35, min(base, 0.98)), 2)


def score_recommendation_confidence(
    *,
    anomaly_confidence: float,
    telemetry_quality: str = "medium",
    evidence_freshness_hours: float | None = None,
) -> float:
    quality_boost = {"high": 0.08, "medium": 0.04, "low": 0.0}.get(telemetry_quality, 0.02)
    conf = anomaly_confidence + quality_boost
    if evidence_freshness_hours is not None:
        if evidence_freshness_hours > 24:
            conf -= 0.15
        elif evidence_freshness_hours > 6:
            conf -= 0.06
    return round(max(0.3, min(conf, 0.96)), 2)


def assess_telemetry_quality(
    *,
    event_count: int,
    stale_sources: int = 0,
    provider_errors: int = 0,
) -> dict[str, Any]:
    if event_count == 0:
        level = "low"
    elif stale_sources >= 2 or provider_errors >= 2:
        level = "low"
    elif event_count >= 5 and stale_sources == 0:
        level = "high"
    else:
        level = "medium"
    return {
        "telemetry_quality": level,
        "event_count": event_count,
        "stale_sources": stale_sources,
        "provider_errors": provider_errors,
    }


def evidence_freshness_hours(last_observed_at: float | None) -> float | None:
    if not last_observed_at:
        return None
    return max(0.0, (time() - float(last_observed_at)) / 3600.0)


def operational_trust_summary(
    *,
    anomalies: list[dict[str, Any]],
    telemetry: dict[str, Any],
) -> dict[str, Any]:
    if not anomalies:
        return {"operational_trust": "stable", "confidence": 0.72, "summary": "No active anomalies."}
    high = sum(1 for a in anomalies if str(a.get("severity")) == "high")
    if high >= 2:
        return {"operational_trust": "degraded", "confidence": 0.88, "summary": f"{high} high-severity anomalies active."}
    if high == 1:
        return {"operational_trust": "watch", "confidence": 0.81, "summary": "One high-severity anomaly requires review."}
    return {"operational_trust": "watch", "confidence": 0.75, "summary": "Elevated signals detected — review recommended."}

# SPDX-License-Identifier: Apache-2.0
"""System-wide operational trust scoring."""

from __future__ import annotations

from typing import Any


def compute_reliability_scores(
    *,
    observations: dict[str, Any] | None = None,
    reliability: dict[str, Any] | None = None,
    attention_quality: dict[str, Any] | None = None,
    governance: dict[str, Any] | None = None,
    correlation: dict[str, Any] | None = None,
    fatigue: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute multi-dimensional operational trust scores (0–1)."""
    obs = observations or {}
    rel = reliability or {}
    tel_fresh = obs.get("telemetry_freshness") or {}
    stale = bool(tel_fresh.get("stale"))
    age = float(tel_fresh.get("age_hours") or 0)

    telemetry_quality = 0.85 if not stale and age < 6 else 0.55 if not stale else 0.35
    truth = str(rel.get("truth_state") or "operationally_unknown")
    execution_reliability = {
        "verified_healthy": 0.92,
        "execution_unverified": 0.55,
        "degraded_confidence": 0.45,
        "verification_failed": 0.25,
        "replay_incomplete": 0.4,
        "operationally_unknown": 0.35,
    }.get(truth, 0.4)

    gov = governance or {}
    governance_health = 0.88 if not gov.get("escalated") else 0.62 if gov.get("cooldown_active") else 0.72
    replay_integrity = 0.9 if str((rel.get("replay_integrity") or {}).get("integrity")) == "healthy" else 0.5

    events = obs.get("events") or []
    dep_fail = sum(1 for e in events if "deployment" in str(e.get("category", "")).lower())
    wf_fail = sum(1 for e in events if "workflow" in str(e.get("category", "")).lower())
    provider_stability = max(0.3, 0.9 - dep_fail * 0.08 - wf_fail * 0.06)

    bounded = float(rel.get("bounded_confidence") or 0.5)
    operational_confidence = round(bounded * 0.6 + execution_reliability * 0.4, 2)

    inflation = float((attention_quality or {}).get("urgency_inflation_ratio") or 0)
    passive = int((attention_quality or {}).get("passive_count") or 0)
    total_signals = max(passive + int((attention_quality or {}).get("high_signal_count") or 0), 1)
    signal_noise_ratio = round(min(1.0, passive / total_signals + inflation * 0.5), 2)
    recommendation_quality = max(0.4, 1.0 - signal_noise_ratio * 0.4)

    fatigue_score = float((fatigue or {}).get("fatigue_score") or 0.2)
    correlation_strength = float((correlation or {}).get("correlation_strength") or 0.5)

    dimensions = {
        "telemetry_quality": round(telemetry_quality, 2),
        "execution_reliability": round(execution_reliability, 2),
        "governance_health": round(governance_health, 2),
        "replay_integrity": round(replay_integrity, 2),
        "provider_stability": round(provider_stability, 2),
        "operational_confidence": operational_confidence,
        "recommendation_quality": round(recommendation_quality, 2),
        "signal_noise_ratio": signal_noise_ratio,
        "correlation_strength": round(correlation_strength, 2),
        "fatigue_score": round(fatigue_score, 2),
    }
    global_score = round(
        sum(
            dimensions[k] * w
            for k, w in (
                ("telemetry_quality", 0.12),
                ("execution_reliability", 0.18),
                ("governance_health", 0.12),
                ("replay_integrity", 0.12),
                ("provider_stability", 0.12),
                ("operational_confidence", 0.18),
                ("recommendation_quality", 0.08),
                ("signal_noise_ratio", -0.08),
            )
        ),
        2,
    )
    global_score = max(0.2, min(global_score, 0.95))

    return {
        "dimensions": dimensions,
        "global_reliability_score": global_score,
        "trust_level": _trust_level(global_score),
        "readonly": True,
    }


def _trust_level(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.6:
        return "moderate"
    if score >= 0.4:
        return "degraded"
    return "low"

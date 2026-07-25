# SPDX-License-Identifier: Apache-2.0
"""Confidence integrity — evidence-bounded operational honesty."""

from __future__ import annotations

from typing import Any


def assess_confidence_integrity(
    *,
    raw_confidence: float = 0.72,
    telemetry_quality: str = "medium",
    stale_sources: int = 0,
    conflicting_evidence: bool = False,
    replay_gaps: int = 0,
    verified: bool = False,
) -> dict[str, Any]:
    """Unified confidence integrity assessment."""
    from aethos_core.reliability.confidence_normalization import normalize_confidence

    normalized = normalize_confidence(
        raw_confidence,
        telemetry_quality=telemetry_quality,
        stale_sources=stale_sources,
        conflicting_evidence=conflicting_evidence,
        replay_gaps=replay_gaps,
    )

    bounded = float(normalized.get("bounded_confidence") or raw_confidence)
    if not verified and bounded > 0.75:
        bounded = min(bounded, 0.72)
        normalized["penalties"] = list(normalized.get("penalties") or []) + ["execution unverified — confidence capped"]

    if verified:
        integrity = "evidence_bound"
        summary = "Confidence is evidence-bound and aligned with verified operational reality."
    elif normalized.get("degraded"):
        integrity = "degraded"
        summary = (
            "Operational indicators improved, though extended verification is still recommended "
            "before declaring full stabilization."
        )
    else:
        integrity = "bounded"
        summary = "Confidence bounded by available evidence — verification weighting applied."

    return {
        "ok": True,
        "integrity": integrity,
        "raw_confidence": normalized.get("raw_confidence"),
        "bounded_confidence": round(bounded, 2),
        "penalties": normalized.get("penalties") or [],
        "degraded": normalized.get("degraded") or integrity == "degraded",
        "verified_weight_applied": verified,
        "summary": summary,
        "principle": "Confidence must never exceed operational verification reality.",
    }

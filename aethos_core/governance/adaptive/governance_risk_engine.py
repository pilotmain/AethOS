# SPDX-License-Identifier: Apache-2.0
"""Governance risk engine — operational risk scoring for adaptive policy."""

from __future__ import annotations

from typing import Any


def score_governance_risk(
    *,
    anomalies: list[dict[str, Any]] | None = None,
    pressure: dict[str, Any] | None = None,
    reliability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score operational risk for adaptive governance decisions."""
    high = sum(1 for a in (anomalies or []) if str(a.get("severity")) == "high")
    pres = pressure or {}
    rel = reliability or {}
    truth = str(rel.get("truth_state") or "")

    risk = 0.2
    risk += high * 0.12
    risk += float(pres.get("pressure_score") or 0) * 0.3
    if truth in ("verification_failed", "degraded_confidence"):
        risk += 0.15
    if truth == "replay_incomplete":
        risk += 0.1

    level = "low"
    if risk >= 0.65:
        level = "high"
    elif risk >= 0.4:
        level = "medium"

    return {
        "risk_score": round(min(risk, 0.95), 2),
        "risk_level": level,
        "high_anomaly_count": high,
        "summary": f"Governance risk {level} (score={risk:.2f}).",
    }

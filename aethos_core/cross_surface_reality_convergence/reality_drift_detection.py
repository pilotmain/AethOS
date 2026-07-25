# SPDX-License-Identifier: Apache-2.0
"""Reality drift detection — cross-surface operational contradictions."""

from __future__ import annotations

from typing import Any


def detect_reality_drift(
    *,
    alignment: dict[str, Any],
    bridge: dict[str, Any],
    reconciliation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Detect when surfaces disagree on operational reality."""
    reasons: list[str] = []
    drift_score = 0.0

    if not alignment.get("surfaces_aligned"):
        reasons.append("subject_misalignment")
        drift_score += 0.35

    competing = alignment.get("competing_subjects") or []
    if len(competing) >= 2:
        reasons.append("multiple_competing_subjects")
        drift_score += 0.2

    reconciliation = reconciliation or {}
    if reconciliation.get("contradictions"):
        reasons.extend(reconciliation["contradictions"])
        drift_score += 0.15 * len(reconciliation["contradictions"])

    bridge_surfaces = bridge.get("surfaces") or []
    if len(bridge_surfaces) >= 2 and alignment.get("active_surface_count", 0) >= 2:
        if alignment.get("alignment_score", 1.0) < 0.55:
            reasons.append("multi_surface_low_alignment")
            drift_score += 0.1

    drift_score = round(min(1.0, drift_score), 2)
    drift_detected = drift_score >= 0.35 or not alignment.get("surfaces_aligned", True)

    return {
        "drift_detected": drift_detected,
        "drift_score": drift_score,
        "drift_reasons": list(dict.fromkeys(reasons)),
        "summary": (
            "Cross-surface reality drift detected — reduce continuity confidence."
            if drift_detected
            else "Cross-surface reality stable — no significant drift."
        ),
    }

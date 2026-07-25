# SPDX-License-Identifier: Apache-2.0
"""Thread resurrection guard — penalize stale thread reactivation."""

from __future__ import annotations

from typing import Any

from aethos_core.continuity_reconstruction.continuity_decay import compute_continuity_decay


def assess_thread_resurrection(
    *,
    subject: str,
    category: str,
    bridge: dict[str, Any],
    age_hours: float,
) -> dict[str, Any]:
    """Detect when a decayed thread may be incorrectly resurrected by affinity overlap."""
    decay = compute_continuity_decay(age_hours=age_hours)
    current_focus = bridge.get("last_focus") or bridge.get("primary_subject") or ""
    stale = decay.get("stale", False)

    resurrected = False
    penalty = 0.0
    reasons: list[str] = []

    if stale and current_focus and subject.lower() != str(current_focus).lower():
        resurrected = True
        penalty = 0.15
        reasons.append("stale_subject_mismatch")

    investigations = bridge.get("active_investigations") or []
    if stale and subject in investigations and current_focus and subject.lower() not in str(current_focus).lower():
        resurrected = True
        penalty = max(penalty, 0.2)
        reasons.append("stale_investigation_resurrection")

    if decay.get("relevance_weight", 1.0) < 0.35 and category not in {"deployment", "provider"}:
        penalty = max(penalty, 0.1)
        reasons.append("low_relevance_category")

    return {
        "resurrection_risk": resurrected,
        "confidence_penalty": round(penalty, 2),
        "stale": stale,
        "reasons": reasons,
        "summary": "Thread resurrection guard clear." if not resurrected else "Stale thread resurrection risk — confidence penalized.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Operational truth — canonical truth state authority."""

from __future__ import annotations

from typing import Any

TRUTH_STATES = frozenset(
    {
        "verified_healthy",
        "execution_unverified",
        "replay_incomplete",
        "degraded_confidence",
        "verification_failed",
        "operationally_unknown",
    }
)


def resolve_truth_state(
    *,
    verification: dict[str, Any],
    replay: dict[str, Any],
    confidence: dict[str, Any],
    convergence: dict[str, Any],
) -> dict[str, Any]:
    """Resolve canonical operational truth state."""
    ver_integrity = str(verification.get("integrity") or "")
    replay_integrity = str(replay.get("integrity") or "")
    conf_bounded = float(confidence.get("bounded_confidence") or confidence.get("raw_confidence") or 0.5)
    conv_state = str(convergence.get("convergence_state") or "")

    if ver_integrity == "healthy" and replay_integrity == "healthy" and conf_bounded >= 0.7:
        truth_state = "verified_healthy"
    elif ver_integrity == "failed":
        truth_state = "verification_failed"
    elif conv_state == "execution_unverified":
        truth_state = "execution_unverified"
    elif replay_integrity in ("missing", "incomplete", "degraded"):
        truth_state = "replay_incomplete"
    elif confidence.get("degraded") or conf_bounded < 0.55:
        truth_state = "degraded_confidence"
    elif conv_state == "unknown" and conf_bounded < 0.45:
        truth_state = "operationally_unknown"
    elif conv_state in ("divergent_failures", "partial_convergence"):
        truth_state = "degraded_confidence"
    else:
        truth_state = "execution_unverified" if convergence.get("executed") else "operationally_unknown"

    return {
        "truth_state": truth_state,
        "executed": bool(convergence.get("executed")),
        "verified": bool(verification.get("verified")),
        "confidence": "bounded",
        "bounded_confidence": conf_bounded,
        "summary": _truth_summary(truth_state),
        "autonomous_execution_blocked": True,
    }


def _truth_summary(state: str) -> str:
    summaries = {
        "verified_healthy": "Operational state verified healthy with bounded confidence.",
        "execution_unverified": "Execution reported but verification incomplete.",
        "replay_incomplete": "Replay telemetry incomplete — causal chain uncertain.",
        "degraded_confidence": "Confidence degraded due to stale or conflicting evidence.",
        "verification_failed": "Verification failed — do not treat as successful.",
        "operationally_unknown": "Insufficient evidence for operational truth.",
    }
    return summaries.get(state, "Operational truth state undetermined.")

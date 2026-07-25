# SPDX-License-Identifier: Apache-2.0
"""Execution integrity — real execution validation signals."""

from __future__ import annotations

from typing import Any


def assess_execution_integrity() -> dict[str, Any]:
    """Fuse verification integrity with execution convergence."""
    verification: dict[str, Any] = {"integrity": "unverified", "verified": False}
    convergence: dict[str, Any] = {"convergence_state": "unknown", "executed": False}

    try:
        from aethos_core.reliability.verification_integrity import assess_verification_integrity

        verification = assess_verification_integrity()
    except Exception:
        pass

    try:
        from aethos_core.reliability.execution_convergence import assess_execution_convergence

        convergence = assess_execution_convergence()
    except Exception:
        pass

    executed = bool(convergence.get("executed"))
    verified = bool(verification.get("verified"))
    integrity = str(verification.get("integrity") or "unverified")

    if verified and integrity == "healthy":
        state = "verified"
        summary = "Execution integrity confirmed — operational verification aligned with substrate reality."
    elif executed and not verified:
        state = "execution_unverified"
        summary = (
            "Execution reported but operational verification incomplete. "
            "Do not treat as fully stabilized."
        )
    elif integrity == "failed":
        state = "verification_failed"
        summary = "Verification failed — execution truth not established."
    elif integrity == "degraded":
        state = "degraded"
        summary = "Execution integrity degraded — partial verification only."
    else:
        state = "unknown"
        summary = "Insufficient evidence for execution integrity assessment."

    return {
        "integrity_state": state,
        "executed": executed,
        "verified": verified,
        "verification_integrity": integrity,
        "convergence_state": str(convergence.get("convergence_state") or "unknown"),
        "summary": summary,
    }

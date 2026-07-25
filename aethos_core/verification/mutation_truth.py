# SPDX-License-Identifier: Apache-2.0
"""Mutation truth — actual mutation outcome proof."""

from __future__ import annotations

from typing import Any

from aethos_core.verification.execution_verifier import verify_execution_outcome


def assess_mutation_truth(*, mutation_job_id: str) -> dict[str, Any]:
    """Operational truth for a single governed mutation."""
    verification = verify_execution_outcome(mutation_job_id=mutation_job_id)
    lifecycle = str(verification.get("lifecycle_state") or "")
    verified = bool(verification.get("verified"))

    if verified and lifecycle in ("verification_verified", "verified"):
        truth = "verified"
    elif lifecycle in ("verification_pending", "execution_completed"):
        truth = "execution_unverified"
    elif lifecycle in ("verification_failed", "rollback_required"):
        truth = "verification_failed"
    else:
        truth = "operationally_unknown"

    return {
        **verification,
        "mutation_truth": truth,
        "stabilization_complete": verified,
        "honest_summary": verification.get("summary"),
    }

# SPDX-License-Identifier: Apache-2.0
"""Execution verifier — post-action operational validation with Tier 1 hardening."""

from __future__ import annotations

from typing import Any


def verify_execution_outcome(*, mutation_job_id: str) -> dict[str, Any]:
    """Verify mutation execution with provider hardening and reconciliation."""
    from aethos_core.runtime.jobs import job_store
    from aethos_core.reconciliation.mutation_reconciliation import reconcile_mutation
    from aethos_core.recovery_runtime.runtime import assess_recovery_state

    job = job_store.get(mutation_job_id)
    if not job:
        return {"ok": False, "error": "mutation_job_not_found"}

    reconciliation = reconcile_mutation(mutation_job_id=mutation_job_id)
    recovery = assess_recovery_state(mutation_job_id=mutation_job_id)
    verification = reconciliation.get("verification") or {}

    return {
        "ok": True,
        "mutation_job_id": mutation_job_id,
        "provider": job.params.get("provider"),
        "operation_type": job.params.get("operation_type"),
        "execution_state": job.params.get("execution_state") or job.status.value,
        "verification_state": job.params.get("verification_state"),
        "lifecycle_state": job.params.get("lifecycle_state"),
        "verified": bool(verification.get("verified")),
        "restart_verification": verification.get("restart_verification"),
        "restart_verification_state": job.params.get("restart_verification_state"),
        "transition_detected": verification.get("transition_detected"),
        "reconciled": bool(reconciliation.get("reconciled")),
        "checks": verification.get("checks") or [],
        "maturity": verification.get("maturity"),
        "verification_coverage_pct": verification.get("verification_coverage_pct"),
        "reconciliation": reconciliation,
        "recovery": recovery,
        "summary": recovery.get("narrative") or verification.get("summary") or reconciliation.get("summary"),
    }

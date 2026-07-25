# SPDX-License-Identifier: Apache-2.0
"""Mutation reliability — governed mutation operational trustworthiness."""

from __future__ import annotations

from typing import Any


def assess_mutation_reliability(*, mutation_job_id: str) -> dict[str, Any]:
    """Assess lifecycle, verification, escalation, and stabilization for a mutation."""
    from aethos_core.runtime.jobs import job_store
    from aethos_core.verification.mutation_truth import assess_mutation_truth

    job = job_store.get(mutation_job_id)
    if not job:
        return {"ok": False, "error": "mutation_job_not_found"}

    truth = assess_mutation_truth(mutation_job_id=mutation_job_id)
    escalation: dict[str, Any] = {}
    try:
        from aethos_core.governance.adaptive.mutation_escalation import assess_mutation_escalation

        escalation = assess_mutation_escalation(
            provider=str(job.params.get("provider") or ""),
            operation_type=str(job.params.get("operation_type") or ""),
        )
    except Exception:
        escalation = {"escalation_tier": "none"}

    lifecycle = str(job.params.get("lifecycle_state") or job.status.value)
    stabilized = bool(truth.get("stabilization_complete"))
    retry_recommended = lifecycle in ("verification_failed", "execution_completed") and not stabilized

    return {
        "ok": True,
        "mutation_job_id": mutation_job_id,
        "provider": job.params.get("provider"),
        "operation_type": job.params.get("operation_type"),
        "lifecycle_state": lifecycle,
        "execution_state": job.params.get("execution_state"),
        "verification_state": job.params.get("verification_state"),
        "mutation_truth": truth.get("mutation_truth"),
        "stabilization_complete": stabilized,
        "retry_recommended": retry_recommended,
        "rollback_available": lifecycle in ("verification_failed", "rollback_required"),
        "escalation": escalation,
        "verification_checks": truth.get("checks") or [],
        "honest_summary": truth.get("honest_summary"),
        "principle": "Execution is not complete until reality confirms stabilization.",
    }

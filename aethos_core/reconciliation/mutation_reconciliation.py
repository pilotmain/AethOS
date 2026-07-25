# SPDX-License-Identifier: Apache-2.0
"""Mutation reconciliation — execution vs reality alignment."""

from __future__ import annotations

from typing import Any


def reconcile_mutation(
    *,
    mutation_job_id: str,
    provider_result: dict[str, Any] | None = None,
    readonly_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from aethos_core.runtime.jobs import job_store
    from aethos_core.reconciliation.deployment_state_diff import diff_deployment_state
    from aethos_core.reconciliation.orphan_detection import detect_orphan_state
    from aethos_core.reconciliation.rollback_consistency import assess_rollback_consistency
    from aethos_core.reconciliation.stabilization_tracking import track_stabilization
    from aethos_core.reconciliation.mutation_timeout_recovery import assess_timeout_recovery
    from aethos_core.provider_hardening.verify import verify_provider_mutation

    job = job_store.get(mutation_job_id)
    if not job:
        return {"ok": False, "error": "mutation_job_not_found"}

    provider = str(job.params.get("provider") or "")
    operation = str(job.params.get("operation_type") or "")
    source_exec = job.params.get("mutation_execution") or {}
    if not isinstance(source_exec, dict):
        source_exec = {}
    provider_result = provider_result or source_exec.get("provider_result") or {}
    if not isinstance(provider_result, dict):
        provider_result = {}

    verification = verify_provider_mutation(
        provider=provider,
        operation_type=operation,
        provider_result=provider_result,
        readonly_artifact=readonly_artifact or {},
    )
    state_diff = diff_deployment_state(expected=source_exec, observed=provider_result, readonly=readonly_artifact or {})
    rollback = assess_rollback_consistency(provider_result=provider_result, readonly_artifact=readonly_artifact or {})
    orphan = detect_orphan_state(job=job, verification=verification)
    stabilization = track_stabilization(verification=verification, state_diff=state_diff)
    timeout = assess_timeout_recovery(job=job)

    aligned = (
        verification.get("verified")
        and not orphan.get("orphan_detected")
        and state_diff.get("aligned", False)
        and stabilization.get("stabilization_phase") != "failed"
    )

    return {
        "ok": True,
        "mutation_job_id": mutation_job_id,
        "provider": provider,
        "operation_type": operation,
        "reconciled": aligned,
        "verification": verification,
        "state_diff": state_diff,
        "rollback_consistency": rollback,
        "orphan_detection": orphan,
        "stabilization": stabilization,
        "timeout_recovery": timeout,
        "summary": (
            verification.get("summary")
            if aligned
            else "Mutation executed — operational reconciliation incomplete. Extended verification recommended."
        ),
        "principle": "A mutation is not trustworthy until operational reconciliation confirms it.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Enqueue readonly verification after governed mutations."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.orchestration.job_taxonomy import canonical_readonly_execution_job_type
from aethos_core.operations.mutations.lifecycle import VERIFICATION_PENDING, LIFECYCLE_VERIFICATION_RUNNING


def verification_operation_for_mutation(*, provider: str, operation_type: str) -> str | None:
    if provider == "railway":
        if operation_type in ("restart", "redeploy", "set_env_var"):
            return "list_deployments"
        return "project_details"
    if provider == "github":
        if operation_type == "workflow_rerun":
            return "workflow_runs"
        return "workflow_diagnostic"
    if provider == "vercel":
        if operation_type in ("redeploy", "restart", "set_env_var"):
            return "list_deployments"
        return "project_details"
    return None


def enqueue_mutation_verification(*, mutation_job: Any, execution_artifact: dict[str, Any]) -> Any | None:
    from aethos_core.runtime.jobs import job_store

    provider = str(mutation_job.params.get("provider") or "unknown")
    operation_type = str(mutation_job.params.get("operation_type") or "")
    verify_op = verification_operation_for_mutation(provider=provider, operation_type=operation_type)
    if not verify_op:
        return None

    target = mutation_job.params.get("target_name")
    title = f"Post-mutation verification — {verify_op.replace('_', ' ')}"
    if target:
        title += f" ({target})"

    params: dict[str, Any] = {
        "provider": provider,
        "operation_type": verify_op,
        "target_name": target,
        "read_only": True,
        "mutating": False,
        "verification_of_mutation_job_id": mutation_job.id,
        "source_mutation_execution": execution_artifact,
        "mutation_evidence": execution_artifact.get("evidence") or execution_artifact.get("provider_result"),
        "user_request": f"Verify mutation {operation_type} on {target or provider}",
    }
    credential_id = mutation_job.params.get("credential_id")
    if credential_id:
        params["credential_id"] = credential_id
    if mutation_job.params.get("auth_method"):
        params["auth_method"] = mutation_job.params["auth_method"]
    if mutation_job.params.get("auth_method_label"):
        params["auth_method_label"] = mutation_job.params["auth_method_label"]

    from aethos_core.operations.execution.execution_permissions import actions_for_operation

    params["approved_actions"] = actions_for_operation(verify_op, provider=provider)

    job = job_store.create(
        title=title,
        job_type=canonical_readonly_execution_job_type(provider),
        params=params,
        source="mutation_verification",
        session_id=mutation_job.session_id,
        auto_run=True,
    )
    mutation_job.params["verification_job_id"] = job.id
    mutation_job.params["verification_state"] = VERIFICATION_PENDING
    mutation_job.params["lifecycle_state"] = LIFECYCLE_VERIFICATION_RUNNING
    if execution_artifact.get("audit"):
        mutation_job.params["audit"] = execution_artifact["audit"]
    return job

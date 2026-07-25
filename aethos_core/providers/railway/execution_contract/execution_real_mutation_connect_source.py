# SPDX-License-Identifier: Apache-2.0
"""
FIX 109 — Real mutation executor (connect_source / GitHub binding only).

Never imports or calls the dry-run phase executor.
"""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    REAL_MUTATION_PHASES_FIX109,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    assess_railway_execution_enablement_policy,
    is_production_environment,
)
from aethos_core.providers.railway.execution_contract.execution_journal import save_execution_journal
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_MUTATION_FAILURE,
    STATUS_MUTATION_SKIPPED,
    STATUS_MUTATION_SUCCESS,
    phase_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import find_phase_receipt
from aethos_core.providers.railway.execution_contract.execution_real_mutation_support import (
    append_real_phase_history,
    record_real_phase_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_types import (
    RealMutationExecutionResult,
)
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    transition_journal_state,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    live_connect_github_source_authorization,
)

_CONNECT_SOURCE_PHASE = "connect_source"


def run_real_mutation_connect_source(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
) -> RealMutationExecutionResult:
    """
    Execute governed connect_source only (FIX 109). Stops after connect_source phase.

    Requires create_service to have produced railway_service_id on the journal.
    No env writes, no deploy trigger.
    """
    execution_id = str(journal.get("execution_id") or "")
    if not execution_id:
        return RealMutationExecutionResult(journal=journal, detail="No execution_id on journal.")

    current = str(journal.get("state") or "draft")
    if current in {"execution_completed", "execution_rolled_back"}:
        return RealMutationExecutionResult(
            journal=journal,
            detail="Execution already terminal; no new mutations performed.",
        )

    existing_receipt = find_phase_receipt(execution_id=execution_id, phase=_CONNECT_SOURCE_PHASE)
    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    repo = str(plan.get("repo") or "")
    branch = str(plan.get("branch") or "main")

    if phase_mutation_recorded(existing_receipt) or journal.get("github_source_bound"):
        from aethos_core.providers.railway.execution_contract.source_binding_verification import (
            verify_source_binding_readonly,
        )
        from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
            normalize_github_repository_slug,
        )

        repo_norm = normalize_github_repository_slug(repo)
        binding = journal.get("github_source_bound") if isinstance(journal.get("github_source_bound"), dict) else {}
        verification = None
        if service_id and environment_id and repo_norm:
            verification = verify_source_binding_readonly(
                environment_id=environment_id,
                service_id=service_id,
                expected_repository=repo_norm,
                expected_branch=branch,
                journal_binding=binding if binding else None,
            )
        if verification and verification.verified:
            journal["execution_mode"] = "enabled"
            journal["source_binding_verification"] = verification.to_dict()
            completed = list(journal.get("real_mutation_phases_completed") or [])
            for phase in REAL_MUTATION_PHASES_FIX109:
                if phase not in completed:
                    completed.append(phase)
            journal["real_mutation_phases_completed"] = completed
            journal = save_execution_journal(journal)
            return RealMutationExecutionResult(
                journal=journal,
                mutation_performed=False,
                idempotent_replay=True,
                service_id=service_id,
                executed_phases=[],
                detail="connect_source already performed for this execution; idempotent replay.",
            )
        journal = dict(journal)
        journal.pop("github_source_bound", None)
        journal.pop("source_binding_verification", None)

    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    if not assessed.allows_connect_source_mutation():
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="connect_source live mutation blocked by execution enablement policy.",
            errors=list(assessed.blocking_reason_messages),
        )

    environment = str(plan.get("environment") or "")
    from aethos_core.providers.railway.execution_contract.production_policy import (
        production_policy_forward_block_errors,
    )

    prod_errors = production_policy_forward_block_errors(
        environment=environment,
        phase="connect_source",
        user_text=user_text,
        execution_id=str(journal.get("execution_id") or ""),
        journal=journal,
        plan=plan,
    )
    if prod_errors:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Production connect_source blocked by production policy (FIX 117).",
            errors=prod_errors,
        )

    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    if not service_id:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="create_service must complete before connect_source.",
            errors=["railway_service_id_missing"],
        )
    if not environment_id:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="railway_environment_id missing on journal.",
            errors=["railway_environment_id_missing"],
        )

    if not journal.get("rollback_journal"):
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Rollback journal must exist before any real mutation.",
            errors=["rollback_journal_missing"],
        )

    from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
        normalize_github_repository_slug,
    )

    repo = normalize_github_repository_slug(str(plan.get("repo") or ""))
    branch = str(plan.get("branch") or "main")
    root_directory = str(plan.get("root_directory") or journal.get("root_directory") or "")
    if not repo:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Deployment plan is missing GitHub repository.",
            errors=["plan_repo_missing"],
        )

    journal["execution_mode"] = "enabled"
    journal = save_execution_journal(journal)

    idempotency_key = str(journal.get("idempotency_key") or "")
    prior_binding = journal.get("github_source_bound")
    prior_dict = dict(prior_binding) if isinstance(prior_binding, dict) else None

    from aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter import (
        connect_github_source,
    )

    with live_connect_github_source_authorization():
        bind_result = connect_github_source(
            environment_name=environment,
            environment_id=environment_id,
            service_id=service_id,
            repository=repo,
            branch=branch,
            idempotency_key=idempotency_key,
            existing_binding=prior_dict,
            root_directory=root_directory,
        )

    if not bind_result.ok:
        receipt = record_real_phase_receipt(
            execution_id=execution_id,
            phase=_CONNECT_SOURCE_PHASE,
            status=STATUS_MUTATION_FAILURE,
            mutation_performed=False,
            detail="; ".join(bind_result.errors) or "connect_source failed",
        )
        journal = append_real_phase_history(
            journal,
            phase=_CONNECT_SOURCE_PHASE,
            status="failed",
            receipt_id=str(receipt.get("receipt_id") or ""),
            mutation_performed=False,
        )
        try:
            journal = transition_journal_state(journal, to_state="execution_partial_failure")
            journal["rollback_available"] = True
        except IllegalExecutionTransitionError:
            journal["state"] = "execution_partial_failure"
            journal["rollback_available"] = True
        journal = save_execution_journal(journal)
        return RealMutationExecutionResult(
            journal=journal,
            detail="connect_source failed.",
            errors=list(bind_result.errors),
        )

    mutation_performed = bool(bind_result.mutation_performed)
    receipt_status = (
        STATUS_MUTATION_SUCCESS
        if mutation_performed
        else STATUS_MUTATION_SKIPPED
    )
    receipt = record_real_phase_receipt(
        execution_id=execution_id,
        phase=_CONNECT_SOURCE_PHASE,
        status=receipt_status,
        mutation_performed=mutation_performed,
        detail=bind_result.detail,
        replayed=bool(bind_result.idempotent_replay),
    )
    journal = append_real_phase_history(
        journal,
        phase=_CONNECT_SOURCE_PHASE,
        status="completed",
        receipt_id=str(receipt.get("receipt_id") or ""),
        mutation_performed=mutation_performed,
    )
    journal["github_source_bound"] = {
        "repository": bind_result.repository or repo,
        "branch": bind_result.branch or branch,
    }
    journal["connect_source_skip_deploys"] = True

    if mutation_performed or bind_result.idempotent_replay:
        from aethos_core.providers.railway.execution_contract.source_binding_verification import (
            verify_source_binding_readonly,
        )

        verification = verify_source_binding_readonly(
            environment_id=environment_id,
            service_id=service_id,
            expected_repository=repo,
            expected_branch=branch,
            journal_binding=dict(journal["github_source_bound"]),
        )
        journal["source_binding_verification"] = verification.to_dict()
        rollback = journal.get("rollback_journal")
        if isinstance(rollback, dict):
            from aethos_core.providers.railway.execution_contract.execution_rollback import (
                journal_rollback_phase,
            )

            journal["rollback_journal"] = journal_rollback_phase(
                rollback,
                action="disconnect_repo_source",
                status="planned",
                detail=f"Planned rollback for GitHub source `{repo}@{branch}` (FIX 110 adapter).",
            )

    completed = list(journal.get("real_mutation_phases_completed") or [])
    for phase in REAL_MUTATION_PHASES_FIX109:
        if phase not in completed:
            completed.append(phase)
    journal["real_mutation_phases_completed"] = completed

    try:
        journal = transition_journal_state(journal, to_state="execution_phase_connect_source")
        journal["rollback_available"] = True
    except IllegalExecutionTransitionError:
        journal["state"] = "execution_phase_connect_source"
        journal["rollback_available"] = True
    journal = save_execution_journal(journal)

    detail = bind_result.detail or "connect_source phase complete."
    if mutation_performed:
        detail = (
            f"{detail} FIX 109 stops after connect_source; "
            "env writes and deploy trigger are not performed."
        )
    return RealMutationExecutionResult(
        journal=journal,
        mutation_performed=mutation_performed,
        idempotent_replay=bool(bind_result.idempotent_replay),
        service_id=service_id,
        executed_phases=[_CONNECT_SOURCE_PHASE] if mutation_performed else [],
        detail=detail,
    )

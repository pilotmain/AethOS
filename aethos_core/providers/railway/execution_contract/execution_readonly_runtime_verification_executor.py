# SPDX-License-Identifier: Apache-2.0
"""
FIX 114 — Readonly runtime verification executor (verify_runtime only).

Never imports dry-run executor or deploy trigger adapter. Never re-triggers deploy.
"""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    VERIFY_RUNTIME_PHASE,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    assess_railway_execution_enablement_policy,
    is_production_environment,
)
from aethos_core.providers.railway.execution_contract.execution_journal import save_execution_journal
from aethos_core.providers.railway.execution_contract.execution_real_mutation_support import (
    append_real_phase_history,
    record_real_phase_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_VERIFICATION_READONLY_FAILURE,
    STATUS_VERIFICATION_READONLY_SKIPPED,
    STATUS_VERIFICATION_READONLY_SUCCESS,
    verification_readonly_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import find_phase_receipt
from aethos_core.providers.railway.execution_contract.execution_real_mutation_types import (
    RealMutationExecutionResult,
)
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    transition_journal_state,
)
from aethos_core.providers.railway.execution_contract.runtime_verification_readiness import (
    assess_runtime_verification_readiness,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    runtime_verification_authorization,
)


def run_readonly_runtime_verification(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
) -> RealMutationExecutionResult:
    """
    Execute governed readonly verify_runtime only (FIX 114).

    Requires live trigger_deploy and journal deployment_id. No deploy re-trigger.
    """
    execution_id = str(journal.get("execution_id") or "")
    if not execution_id:
        return RealMutationExecutionResult(journal=journal, detail="No execution_id on journal.")

    existing_receipt = find_phase_receipt(execution_id=execution_id, phase=VERIFY_RUNTIME_PHASE)
    if verification_readonly_recorded(existing_receipt) or journal.get("runtime_verification_performed"):
        journal = save_execution_journal(journal)
        return RealMutationExecutionResult(
            journal=journal,
            mutation_performed=False,
            idempotent_replay=True,
            service_id=str(journal.get("railway_service_id") or ""),
            executed_phases=[],
            detail="verify_runtime already recorded; idempotent replay.",
        )

    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    if not assessed.allows_verify_runtime_readonly():
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="verify_runtime blocked by execution enablement policy.",
            errors=list(assessed.blocking_reason_messages),
        )

    readiness = assess_runtime_verification_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )
    journal["runtime_verification_readiness"] = readiness.to_dict()
    journal = save_execution_journal(journal)

    if not readiness.ready_for_runtime_verification:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Runtime verification readiness gate blocked this check.",
            errors=list(readiness.blockers),
        )

    environment = str(plan.get("environment") or "")
    from aethos_core.providers.railway.execution_contract.production_policy import (
        production_policy_forward_block_errors,
    )

    prod_errors = production_policy_forward_block_errors(
        environment=environment,
        phase="verify_runtime",
        user_text=user_text,
        execution_id=str(journal.get("execution_id") or ""),
        journal=journal,
        plan=plan,
    )
    if prod_errors:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Production verify_runtime blocked by production policy (FIX 117).",
            errors=prod_errors,
        )

    service_id = str(journal.get("railway_service_id") or "")
    deployment_id = str(journal.get("railway_deployment_id") or "")
    if not deployment_id and isinstance(journal.get("deploy_trigger_metadata"), dict):
        deployment_id = str(journal["deploy_trigger_metadata"].get("deployment_id") or "")

    if not service_id or not deployment_id:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="trigger_deploy must record railway_service_id and railway_deployment_id first.",
            errors=["deployment_context_missing"],
        )

    from aethos_core.providers.railway.greenfield_adapters.verify_runtime_readonly_adapter import (
        verify_runtime_readonly,
    )

    prior = journal.get("runtime_verification") if isinstance(journal.get("runtime_verification"), dict) else None

    with runtime_verification_authorization():
        verify_result = verify_runtime_readonly(
            environment_name=environment,
            service_id=service_id,
            deployment_id=deployment_id,
            prior_verification=prior,
        )

    if not verify_result.ok:
        receipt = record_real_phase_receipt(
            execution_id=execution_id,
            phase=VERIFY_RUNTIME_PHASE,
            status=STATUS_VERIFICATION_READONLY_FAILURE,
            mutation_performed=False,
            detail="; ".join(verify_result.errors) or "runtime verification failed",
        )
        journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
        journal = save_execution_journal(journal)
        return RealMutationExecutionResult(
            journal=journal,
            detail="verify_runtime read failed.",
            errors=list(verify_result.errors),
        )

    receipt_status = (
        STATUS_VERIFICATION_READONLY_SUCCESS
        if verify_result.verified
        else STATUS_VERIFICATION_READONLY_SKIPPED
        if verify_result.idempotent_replay
        else STATUS_VERIFICATION_READONLY_FAILURE
    )
    receipt = record_real_phase_receipt(
        execution_id=execution_id,
        phase=VERIFY_RUNTIME_PHASE,
        status=receipt_status,
        mutation_performed=False,
        detail=verify_result.detail,
        replayed=bool(verify_result.idempotent_replay),
    )
    journal = append_real_phase_history(
        journal,
        phase=VERIFY_RUNTIME_PHASE,
        status="completed" if verify_result.verified else "failed",
        receipt_id=str(receipt.get("receipt_id") or ""),
        mutation_performed=False,
    )

    journal["runtime_verification"] = {
        "verified": verify_result.verified,
        "deployment_id": verify_result.deployment_id,
        "deployment_state": verify_result.deployment_state,
        "service_id": service_id,
        "readonly": True,
        "detail": verify_result.detail,
    }
    journal["runtime_verification_performed"] = True
    journal["ready_for_runtime_verification"] = verify_result.verified

    try:
        journal = transition_journal_state(journal, to_state="execution_phase_verify")
    except IllegalExecutionTransitionError:
        journal["state"] = "execution_phase_verify"

    if verify_result.verified:
        try:
            journal = transition_journal_state(journal, to_state="execution_completed")
        except IllegalExecutionTransitionError:
            journal["state"] = "execution_completed"

    journal = save_execution_journal(journal)

    detail = verify_result.detail or "verify_runtime complete."
    return RealMutationExecutionResult(
        journal=journal,
        mutation_performed=False,
        idempotent_replay=bool(verify_result.idempotent_replay),
        service_id=service_id,
        executed_phases=[VERIFY_RUNTIME_PHASE] if verify_result.verified else [],
        detail=detail,
    )

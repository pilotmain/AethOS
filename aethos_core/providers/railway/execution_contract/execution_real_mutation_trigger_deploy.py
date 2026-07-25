# SPDX-License-Identifier: Apache-2.0
"""
FIX 113 — Real mutation executor (trigger_deploy only).

Never imports dry-run executor. No runtime verification (FIX 114).
"""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
    assess_deploy_trigger_readiness,
)
from aethos_core.providers.railway.execution_contract.deploy_trigger_rollback_contract import (
    build_deploy_trigger_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    REAL_MUTATION_PHASES_FIX113,
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
    STATUS_MUTATION_FAILURE,
    STATUS_MUTATION_SKIPPED,
    STATUS_MUTATION_SUCCESS,
    phase_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import find_phase_receipt
from aethos_core.providers.railway.execution_contract.execution_real_mutation_types import (
    RealMutationExecutionResult,
)
from aethos_core.providers.railway.execution_contract.deploy_trigger_rollback_contract import (
    DEPLOY_TRIGGER_ROLLBACK_ACTION,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import journal_rollback_phase
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    transition_journal_state,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    live_trigger_deploy_authorization,
)

_TRIGGER_DEPLOY_PHASE = "trigger_deploy"


def run_real_mutation_trigger_deploy(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
) -> RealMutationExecutionResult:
    """
    Execute governed trigger_deploy only (FIX 113). Stops after deploy trigger.

    Requires deploy readiness gate, rollback journal, and live forward phases.
    No verify_runtime, no auto-promotion, no production.
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

    existing_receipt = find_phase_receipt(execution_id=execution_id, phase=_TRIGGER_DEPLOY_PHASE)
    existing_deployment_id = str(journal.get("railway_deployment_id") or "")
    if phase_mutation_recorded(existing_receipt) or existing_deployment_id:
        journal["execution_mode"] = "enabled"
        completed = list(journal.get("real_mutation_phases_completed") or [])
        for phase in REAL_MUTATION_PHASES_FIX113:
            if phase not in completed:
                completed.append(phase)
        journal["real_mutation_phases_completed"] = completed
        journal = save_execution_journal(journal)
        return RealMutationExecutionResult(
            journal=journal,
            mutation_performed=False,
            idempotent_replay=True,
            service_id=str(journal.get("railway_service_id") or ""),
            executed_phases=[],
            detail="trigger_deploy already performed for this execution; idempotent replay.",
        )

    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    if not assessed.allows_trigger_deploy_mutation():
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="trigger_deploy live mutation blocked by execution enablement policy.",
            errors=list(assessed.blocking_reason_messages),
        )

    readiness = assess_deploy_trigger_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )
    rollback_contract = build_deploy_trigger_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )
    journal["deploy_trigger_rollback_plan"] = rollback_contract.to_dict()
    journal["deploy_trigger_readiness"] = readiness.to_dict()
    journal = save_execution_journal(journal)

    if not readiness.ready_for_deploy_trigger:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Deploy trigger readiness gate blocked this mutation.",
            errors=list(readiness.blockers),
        )

    if not rollback_contract.rollback_plan_ready:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Deploy trigger rollback plan not ready.",
            errors=list(rollback_contract.blockers),
        )

    environment = str(plan.get("environment") or "")
    from aethos_core.providers.railway.execution_contract.production_policy import (
        production_policy_forward_block_errors,
    )

    prod_errors = production_policy_forward_block_errors(
        environment=environment,
        phase="trigger_deploy",
        user_text=user_text,
        execution_id=str(journal.get("execution_id") or ""),
        journal=journal,
        plan=plan,
    )
    if prod_errors:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Production trigger_deploy blocked by production policy (FIX 117).",
            errors=prod_errors,
        )

    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    if not service_id or not environment_id:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Prior phases must populate railway_service_id and railway_environment_id.",
            errors=["railway_target_ids_missing"],
        )

    rollback_journal = journal.get("rollback_journal")
    if isinstance(rollback_journal, dict):
        journal["rollback_journal"] = journal_rollback_phase(
            rollback_journal,
            action=DEPLOY_TRIGGER_ROLLBACK_ACTION,
            status="planned",
            detail="Planned disable_deploys rollback before live deploy trigger (FIX 113).",
        )

    journal["execution_mode"] = "enabled"
    journal = save_execution_journal(journal)

    idempotency_key = str(journal.get("idempotency_key") or "")

    from aethos_core.providers.railway.greenfield_adapters.trigger_deploy_adapter import (
        trigger_railway_deploy,
    )

    with live_trigger_deploy_authorization():
        deploy_result = trigger_railway_deploy(
            environment_name=environment,
            environment_id=environment_id,
            service_id=service_id,
            idempotency_key=idempotency_key,
            existing_deployment_id=existing_deployment_id,
        )

    if not deploy_result.ok:
        receipt = record_real_phase_receipt(
            execution_id=execution_id,
            phase=_TRIGGER_DEPLOY_PHASE,
            status=STATUS_MUTATION_FAILURE,
            mutation_performed=False,
            detail="; ".join(deploy_result.errors) or "trigger_deploy failed",
        )
        journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
        journal = save_execution_journal(journal)
        return RealMutationExecutionResult(
            journal=journal,
            detail="trigger_deploy failed.",
            errors=list(deploy_result.errors),
        )

    mutation_performed = bool(deploy_result.mutation_performed)
    receipt_status = (
        STATUS_MUTATION_SUCCESS if mutation_performed else STATUS_MUTATION_SKIPPED
    )
    receipt = record_real_phase_receipt(
        execution_id=execution_id,
        phase=_TRIGGER_DEPLOY_PHASE,
        status=receipt_status,
        mutation_performed=mutation_performed,
        detail=deploy_result.detail,
        replayed=bool(deploy_result.idempotent_replay),
    )
    journal = append_real_phase_history(
        journal,
        phase=_TRIGGER_DEPLOY_PHASE,
        status="completed",
        receipt_id=str(receipt.get("receipt_id") or ""),
        mutation_performed=mutation_performed,
    )

    if deploy_result.deployment_id:
        journal["railway_deployment_id"] = deploy_result.deployment_id
    if getattr(deploy_result, "deployment_url", ""):
        journal["deployment_url"] = deploy_result.deployment_url
    journal["deploy_trigger_metadata"] = {
        "graphql_operation": deploy_result.graphql_operation or "serviceInstanceRedeploy",
        "environment_id": environment_id,
        "service_id": service_id,
        "provider_request_id": deploy_result.provider_request_id or deploy_result.deployment_id,
        "deployment_id": deploy_result.deployment_id,
    }
    journal["deploy_triggered"] = True
    journal["ready_for_deploy_trigger"] = True
    journal["ready_for_runtime_verification"] = False
    journal["runtime_verification_performed"] = False

    completed = list(journal.get("real_mutation_phases_completed") or [])
    for phase in REAL_MUTATION_PHASES_FIX113:
        if phase not in completed:
            completed.append(phase)
    journal["real_mutation_phases_completed"] = completed

    try:
        journal = transition_journal_state(journal, to_state="execution_phase_trigger_deploy")
    except IllegalExecutionTransitionError:
        journal["state"] = "execution_phase_trigger_deploy"
    journal = save_execution_journal(journal)

    detail = deploy_result.detail or "trigger_deploy phase complete."
    if mutation_performed:
        detail = (
            f"{detail} FIX 113 stops after deploy trigger; "
            f"deployment_id=`{deploy_result.deployment_id}`. "
            "Runtime verification belongs to FIX 114."
        )
    return RealMutationExecutionResult(
        journal=journal,
        mutation_performed=mutation_performed,
        idempotent_replay=bool(deploy_result.idempotent_replay),
        service_id=service_id,
        executed_phases=[_TRIGGER_DEPLOY_PHASE] if mutation_performed else [],
        detail=detail,
    )

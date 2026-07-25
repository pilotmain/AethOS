# SPDX-License-Identifier: Apache-2.0
"""
FIX 112 — Real mutation executor (configure_env / secure-store env writes only).

Never imports dry-run executor. Never logs secret values.
"""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    CONFIGURE_ENV_FORWARD_PHASE,
    resolve_env_configure_groups,
)
from aethos_core.providers.railway.execution_contract.env_configure_rollback_contract import (
    build_env_configure_rollback_contract,
    group_version_fingerprint_for_plan,
)
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    REAL_MUTATION_PHASES_FIX112,
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
from aethos_core.providers.railway.execution_contract.execution_receipts import find_phase_group_receipt
from aethos_core.providers.railway.execution_contract.execution_real_mutation_types import (
    RealMutationExecutionResult,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import journal_rollback_phase
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    transition_journal_state,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    live_configure_env_authorization,
)


def _all_groups_complete(journal: dict[str, Any], *, plan: dict[str, Any]) -> bool:
    groups = journal.get("env_configure_groups")
    if not isinstance(groups, dict):
        return False
    for group_id, _names in resolve_env_configure_groups(plan):
        row = groups.get(group_id)
        if not isinstance(row, dict) or not row.get("recorded"):
            return False
    return True


def run_real_mutation_configure_env(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
) -> RealMutationExecutionResult:
    """
    Execute governed configure_env only (FIX 112). Stops after env groups are written.

    Requires live create_service + live connect_source verification and rollback plan.
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

    if _all_groups_complete(journal, plan=plan):
        journal["execution_mode"] = "enabled"
        completed = list(journal.get("real_mutation_phases_completed") or [])
        for phase in REAL_MUTATION_PHASES_FIX112:
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
            detail="configure_env already completed for this execution; idempotent replay.",
        )

    from aethos_core.operations.mutations.secrets import parse_env_var_from_request

    if parse_env_var_from_request(user_text):
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Chat-provided env secrets are not permitted for configure_env.",
            errors=["chat_secrets_forbidden"],
        )

    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    if not assessed.allows_configure_env_mutation():
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="configure_env live mutation blocked by execution enablement policy.",
            errors=list(assessed.blocking_reason_messages),
        )

    rollback_contract = build_env_configure_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )
    journal["env_configure_rollback_plan"] = rollback_contract.to_dict()
    journal = save_execution_journal(journal)

    if not rollback_contract.rollback_plan_ready:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Env configure rollback plan not ready; env writes blocked.",
            errors=list(rollback_contract.blockers),
        )

    environment = str(plan.get("environment") or "")
    from aethos_core.providers.railway.execution_contract.production_policy import (
        production_policy_forward_block_errors,
    )

    prod_errors = production_policy_forward_block_errors(
        environment=environment,
        phase="configure_env",
        user_text=user_text,
        execution_id=str(journal.get("execution_id") or ""),
        journal=journal,
        plan=plan,
    )
    if prod_errors:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Production configure_env blocked by production policy (FIX 117).",
            errors=prod_errors,
        )

    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    if not service_id or not environment_id:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="create_service and connect_source must complete before configure_env.",
            errors=["railway_service_or_environment_missing"],
        )

    rollback_journal = journal.get("rollback_journal")
    if isinstance(rollback_journal, dict):
        journal["rollback_journal"] = journal_rollback_phase(
            rollback_journal,
            action="revert_env_writes",
            status="planned",
            detail="Planned revert_env_writes before live env group writes (FIX 112).",
        )

    journal["execution_mode"] = "enabled"
    groups_state = dict(journal.get("env_configure_groups") or {})
    journal["env_configure_groups"] = groups_state
    journal = save_execution_journal(journal)

    from aethos_core.providers.railway.greenfield_adapters.configure_env_adapter import (
        configure_env_group,
    )

    any_mutation = False
    executed_groups: list[str] = []
    errors: list[str] = []

    with live_configure_env_authorization():
        for group_id, env_names in resolve_env_configure_groups(plan):
            existing = find_phase_group_receipt(
                execution_id=execution_id,
                phase=CONFIGURE_ENV_FORWARD_PHASE,
                receipt_group=group_id,
            )
            if phase_mutation_recorded(existing):
                groups_state[group_id] = dict(groups_state.get(group_id) or {})
                groups_state[group_id]["recorded"] = True
                continue

            fingerprint = group_version_fingerprint_for_plan(
                plan=plan,
                group_id=group_id,
                env_names=env_names,
            )
            group_result = configure_env_group(
                environment_name=environment,
                environment_id=environment_id,
                service_id=service_id,
                group_id=group_id,
                env_names=env_names,
                plan=plan,
                version_fingerprint=fingerprint,
                journal_group_state=groups_state.get(group_id) if isinstance(groups_state.get(group_id), dict) else None,
            )

            if not group_result.ok:
                receipt = record_real_phase_receipt(
                    execution_id=execution_id,
                    phase=CONFIGURE_ENV_FORWARD_PHASE,
                    status=STATUS_MUTATION_FAILURE,
                    mutation_performed=False,
                    detail=f"group `{group_id}` failed (no secret values logged)",
                    receipt_group=group_id,
                    env_var_names=list(env_names),
                )
                _ = receipt
                errors.extend(group_result.errors)
                journal = save_execution_journal(journal)
                return RealMutationExecutionResult(
                    journal=journal,
                    detail=f"configure_env group `{group_id}` failed.",
                    errors=errors,
                )

            mutation_performed = bool(group_result.mutation_performed)
            if mutation_performed:
                any_mutation = True
                executed_groups.append(group_id)

            status = (
                STATUS_MUTATION_SUCCESS
                if mutation_performed
                else STATUS_MUTATION_SKIPPED
            )
            receipt = record_real_phase_receipt(
                execution_id=execution_id,
                phase=CONFIGURE_ENV_FORWARD_PHASE,
                status=status,
                mutation_performed=mutation_performed,
                detail=group_result.detail,
                replayed=bool(group_result.idempotent_replay),
                receipt_group=group_id,
                env_var_names=list(group_result.env_names_written or env_names),
            )
            groups_state[group_id] = {
                "recorded": True,
                "env_names": list(group_result.env_names_written or env_names),
                "version_fingerprint": fingerprint,
                "mutation_performed": mutation_performed,
                "receipt_id": str(receipt.get("receipt_id") or ""),
            }
            journal = append_real_phase_history(
                journal,
                phase=CONFIGURE_ENV_FORWARD_PHASE,
                status="completed",
                receipt_id=str(receipt.get("receipt_id") or ""),
                mutation_performed=mutation_performed,
            )

    journal["env_configure_groups"] = groups_state
    journal["env_vars_configured"] = {
        "group_count": len(resolve_env_configure_groups(plan)),
        "groups": {
            gid: {"env_names": list(groups_state.get(gid, {}).get("env_names") or [])}
            for gid, _ in resolve_env_configure_groups(plan)
        },
    }

    from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
        assess_deploy_trigger_readiness,
    )
    from aethos_core.providers.railway.execution_contract.env_configure_verification import (
        verify_env_configure_readonly,
    )

    all_journal_names: list[str] = []
    for gid, _ in resolve_env_configure_groups(plan):
        row = groups_state.get(gid)
        if isinstance(row, dict):
            all_journal_names.extend(str(n) for n in row.get("env_names") or [])

    verification = verify_env_configure_readonly(
        environment_id=environment_id,
        service_id=service_id,
        journal_env_names=all_journal_names,
        plan=plan,
    )
    journal["env_configure_verification"] = verification.to_dict()

    deploy_ready = assess_deploy_trigger_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )
    journal["ready_for_deploy_trigger"] = deploy_ready.ready_for_deploy_trigger
    journal["deploy_trigger_readiness"] = deploy_ready.to_dict()

    completed = list(journal.get("real_mutation_phases_completed") or [])
    for phase in REAL_MUTATION_PHASES_FIX112:
        if phase not in completed:
            completed.append(phase)
    journal["real_mutation_phases_completed"] = completed

    try:
        journal = transition_journal_state(journal, to_state="execution_phase_configure_env")
        journal["rollback_available"] = True
    except IllegalExecutionTransitionError:
        journal["state"] = "execution_phase_configure_env"
        journal["rollback_available"] = True
    journal = save_execution_journal(journal)

    detail = (
        "configure_env phase complete (FIX 112). "
        "Deploy trigger not performed."
    )
    if executed_groups:
        detail = f"{detail} Groups written: {', '.join(executed_groups)}."
    return RealMutationExecutionResult(
        journal=journal,
        mutation_performed=any_mutation,
        idempotent_replay=not any_mutation and _all_groups_complete(journal, plan=plan),
        service_id=service_id,
        executed_phases=executed_groups,
        detail=detail,
    )

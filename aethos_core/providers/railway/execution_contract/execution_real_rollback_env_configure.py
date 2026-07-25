# SPDX-License-Identifier: Apache-2.0
"""
FIX 115 — Live rollback executor for configure_env (revert_env_writes only).

Never imports forward mutation executors or deploy trigger adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    CONFIGURE_ENV_ROLLBACK_ACTION,
    ENV_CONFIGURE_GROUPS,
)
from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
    REVERT_ENV_ROLLBACK_PHASE,
)
from aethos_core.providers.railway.execution_contract.env_configure_rollback_contract import (
    build_env_configure_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    assess_railway_execution_enablement_policy,
    is_rollback_blocked_environment,
)
from aethos_core.providers.railway.execution_contract.execution_journal import save_execution_journal
from aethos_core.providers.railway.execution_contract.execution_real_mutation_support import (
    record_real_phase_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_ROLLBACK_MUTATION_FAILURE,
    STATUS_ROLLBACK_MUTATION_SKIPPED,
    STATUS_ROLLBACK_MUTATION_SUCCESS,
    forward_live_configure_env_group_recorded,
    rollback_phase_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
    find_phase_group_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import journal_rollback_phase
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    live_revert_env_authorization,
)


@dataclass
class RealEnvRollbackResult:
    journal: dict[str, Any]
    mutation_performed: bool = False
    idempotent_replay: bool = False
    rollback_receipt_recorded: bool = False
    policy_blocked: bool = False
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def _configure_env_live_recorded(*, execution_id: str) -> bool:
    for group_id, _names in ENV_CONFIGURE_GROUPS:
        receipt = find_phase_group_receipt(
            execution_id=execution_id,
            phase="configure_env",
            receipt_group=group_id,
        )
        if forward_live_configure_env_group_recorded(receipt):
            return True
    return False


def run_real_revert_env_configure_rollback(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any] | None = None,
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
) -> RealEnvRollbackResult:
    plan = plan or {}
    execution_id = str(journal.get("execution_id") or "")
    if not execution_id:
        return RealEnvRollbackResult(
            journal=journal,
            detail="No execution_id on journal.",
            errors=["execution_id_missing"],
        )

    existing = find_phase_receipt(execution_id=execution_id, phase=REVERT_ENV_ROLLBACK_PHASE)
    if rollback_phase_recorded(existing):
        journal["env_configure_rollback_performed"] = True
        journal = save_execution_journal(journal)
        return RealEnvRollbackResult(
            journal=journal,
            idempotent_replay=True,
            rollback_receipt_recorded=True,
            detail="rollback_configure_env already recorded; idempotent replay.",
        )

    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    if not assessed.allows_revert_env_rollback():
        return RealEnvRollbackResult(
            journal=journal,
            policy_blocked=True,
            detail="revert_env_writes rollback blocked by execution enablement policy.",
            errors=list(assessed.blocking_reason_messages),
        )

    contract = build_env_configure_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )
    if not _configure_env_live_recorded(execution_id=execution_id):
        return RealEnvRollbackResult(
            journal=journal,
            policy_blocked=True,
            detail="Live configure_env receipt required before env rollback.",
            errors=["configure_env_live_required"],
        )

    environment = str(plan.get("environment") or "")
    if is_rollback_blocked_environment(environment):
        return RealEnvRollbackResult(
            journal=journal,
            policy_blocked=True,
            detail="Production env rollback is not permitted in FIX 115.",
            errors=["production environment blocked"],
        )

    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    journal_names: list[str] = []
    groups = journal.get("env_configure_groups")
    if isinstance(groups, dict):
        for group in groups.values():
            if isinstance(group, dict):
                journal_names.extend(str(n) for n in group.get("env_names") or [])

    from aethos_core.providers.railway.greenfield_adapters.revert_env_configure_adapter import (
        revert_env_writes,
    )

    with live_revert_env_authorization():
        revert_result = revert_env_writes(
            environment_name=environment,
            environment_id=environment_id,
            service_id=service_id,
            journal_env_names=journal_names,
        )

    if not revert_result.ok:
        receipt = record_real_phase_receipt(
            execution_id=execution_id,
            phase=REVERT_ENV_ROLLBACK_PHASE,
            status=STATUS_ROLLBACK_MUTATION_FAILURE,
            mutation_performed=False,
            detail="; ".join(revert_result.errors) or "revert_env_writes failed",
            rollback_phase=REVERT_ENV_ROLLBACK_PHASE,
            rollback_action=CONFIGURE_ENV_ROLLBACK_ACTION,
        )
        journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
        journal = save_execution_journal(journal)
        return RealEnvRollbackResult(
            journal=journal,
            detail="revert_env_writes failed.",
            errors=list(revert_result.errors),
        )

    mutation_performed = bool(revert_result.mutation_performed)
    receipt_status = (
        STATUS_ROLLBACK_MUTATION_SUCCESS
        if mutation_performed
        else STATUS_ROLLBACK_MUTATION_SKIPPED
    )
    receipt = record_real_phase_receipt(
        execution_id=execution_id,
        phase=REVERT_ENV_ROLLBACK_PHASE,
        status=receipt_status,
        mutation_performed=mutation_performed,
        detail=revert_result.detail,
        replayed=bool(revert_result.idempotent_replay),
        env_var_names=list(revert_result.env_names_reverted),
        rollback_phase=REVERT_ENV_ROLLBACK_PHASE,
        rollback_action=CONFIGURE_ENV_ROLLBACK_ACTION,
    )

    rollback_journal = journal.get("rollback_journal")
    if isinstance(rollback_journal, dict):
        journal["rollback_journal"] = journal_rollback_phase(
            rollback_journal,
            action=CONFIGURE_ENV_ROLLBACK_ACTION,
            status="completed" if mutation_performed else "skipped",
            detail=revert_result.detail,
        )

    journal["env_configure_rollback_performed"] = True
    journal["env_vars_reverted"] = {
        "env_names": list(revert_result.env_names_reverted),
        "readonly": True,
    }
    journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
    journal = save_execution_journal(journal)

    return RealEnvRollbackResult(
        journal=journal,
        mutation_performed=mutation_performed,
        idempotent_replay=bool(revert_result.idempotent_replay),
        rollback_receipt_recorded=True,
        detail=revert_result.detail or "revert_env_writes complete.",
    )

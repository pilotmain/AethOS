# SPDX-License-Identifier: Apache-2.0
"""
FIX 111 — Live rollback executor for connect_source (disconnect_repo_source only).

Never imports or calls the dry-run rollback executor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.connect_source_rollback_contract import (
    build_connect_source_rollback_contract,
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
    rollback_phase_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import journal_rollback_phase
from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
    CONNECT_SOURCE_ROLLBACK_ACTION,
    CONNECT_SOURCE_ROLLBACK_PHASE,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    live_disconnect_github_source_authorization,
)


@dataclass
class RealConnectSourceRollbackResult:
    journal: dict[str, Any]
    mutation_performed: bool = False
    idempotent_replay: bool = False
    rollback_receipt_recorded: bool = False
    policy_blocked: bool = False
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def run_real_disconnect_connect_source_rollback(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any] | None = None,
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
) -> RealConnectSourceRollbackResult:
    """
    Execute governed live disconnect_repo_source rollback for connect_source binding.

    Requires forward connect_source live mutation receipt. No env writes, no deploy trigger.
    """
    plan = plan or {}
    execution_id = str(journal.get("execution_id") or "")
    if not execution_id:
        return RealConnectSourceRollbackResult(
            journal=journal,
            detail="No execution_id on journal.",
            errors=["execution_id_missing"],
        )

    contract = build_connect_source_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )

    existing = find_phase_receipt(execution_id=execution_id, phase=CONNECT_SOURCE_ROLLBACK_PHASE)
    if rollback_phase_recorded(existing):
        journal["connect_source_rollback_performed"] = True
        journal["connect_source_rollback_mode"] = "enabled"
        journal = save_execution_journal(journal)
        return RealConnectSourceRollbackResult(
            journal=journal,
            idempotent_replay=True,
            rollback_receipt_recorded=True,
            detail="rollback_connect_source already recorded; idempotent replay.",
        )

    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    if not assessed.allows_disconnect_source_rollback():
        return RealConnectSourceRollbackResult(
            journal=journal,
            policy_blocked=True,
            detail="Live source disconnect rollback blocked by execution enablement policy.",
            errors=list(assessed.blocking_reason_messages),
        )

    if not contract.eligible_for_live_rollback:
        receipt = record_real_phase_receipt(
            execution_id=execution_id,
            phase=CONNECT_SOURCE_ROLLBACK_PHASE,
            status=STATUS_ROLLBACK_MUTATION_FAILURE,
            mutation_performed=False,
            detail="; ".join(contract.blocker_messages) or "live rollback not eligible",
        )
        journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
        journal = save_execution_journal(journal)
        return RealConnectSourceRollbackResult(
            journal=journal,
            detail="connect_source live rollback blocked.",
            errors=list(contract.blockers),
        )

    environment = str(plan.get("environment") or "")
    if is_rollback_blocked_environment(environment):
        return RealConnectSourceRollbackResult(
            journal=journal,
            policy_blocked=True,
            detail="Production disconnect rollback is not permitted.",
            errors=["production environment blocked for source disconnect"],
        )

    service_id = contract.service_id
    environment_id = contract.environment_id
    repo = contract.repository
    branch = contract.branch

    journal["execution_mode"] = "enabled"
    journal["connect_source_rollback_mode"] = "enabled"
    journal = save_execution_journal(journal)

    idempotency_key = str(journal.get("idempotency_key") or "")

    from aethos_core.providers.railway.greenfield_adapters.disconnect_github_source_adapter import (
        disconnect_github_source,
    )

    with live_disconnect_github_source_authorization():
        disconnect_result = disconnect_github_source(
            environment_name=environment,
            environment_id=environment_id,
            service_id=service_id,
            repository=repo,
            branch=branch,
            idempotency_key=idempotency_key,
        )

    if not disconnect_result.ok:
        receipt = record_real_phase_receipt(
            execution_id=execution_id,
            phase=CONNECT_SOURCE_ROLLBACK_PHASE,
            status=STATUS_ROLLBACK_MUTATION_FAILURE,
            mutation_performed=False,
            detail="; ".join(disconnect_result.errors) or "disconnect failed",
        )
        journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
        journal = save_execution_journal(journal)
        return RealConnectSourceRollbackResult(
            journal=journal,
            detail="disconnect_repo_source failed.",
            errors=list(disconnect_result.errors),
        )

    mutation_performed = bool(disconnect_result.mutation_performed)
    receipt_status = (
        STATUS_ROLLBACK_MUTATION_SUCCESS
        if mutation_performed
        else STATUS_ROLLBACK_MUTATION_SKIPPED
    )
    receipt = record_real_phase_receipt(
        execution_id=execution_id,
        phase=CONNECT_SOURCE_ROLLBACK_PHASE,
        status=receipt_status,
        mutation_performed=mutation_performed,
        detail=disconnect_result.detail,
        replayed=bool(disconnect_result.idempotent_replay),
    )

    rollback_journal = journal.get("rollback_journal")
    if isinstance(rollback_journal, dict):
        updated = journal_rollback_phase(
            rollback_journal,
            action=CONNECT_SOURCE_ROLLBACK_ACTION,
            status="completed" if mutation_performed else "skipped",
            detail=disconnect_result.detail,
        )
        for row in list(updated.get("actions") or []):
            if str(row.get("action") or "") == CONNECT_SOURCE_ROLLBACK_ACTION:
                row["status"] = "completed" if mutation_performed else "skipped"
                row["mutation_performed"] = mutation_performed
        journal["rollback_journal"] = updated

    binding = journal.get("github_source_bound") if isinstance(journal.get("github_source_bound"), dict) else {}
    journal["github_source_bound_rollback"] = dict(binding) if binding else {
        "repository": repo,
        "branch": branch,
    }
    if mutation_performed or disconnect_result.idempotent_replay:
        journal.pop("github_source_bound", None)
        journal["github_source_disconnected"] = True
    journal["connect_source_rollback_performed"] = True
    journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
    journal["rollback_available"] = True
    journal = save_execution_journal(journal)

    detail = disconnect_result.detail or "rollback_connect_source complete."
    if mutation_performed:
        detail = (
            f"{detail} FIX 111 stops after disconnect_repo_source; "
            "env writes and deploy trigger are not performed."
        )
    return RealConnectSourceRollbackResult(
        journal=journal,
        mutation_performed=mutation_performed,
        idempotent_replay=bool(disconnect_result.idempotent_replay),
        rollback_receipt_recorded=True,
        detail=detail,
    )

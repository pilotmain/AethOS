# SPDX-License-Identifier: Apache-2.0
"""
FIX 108 — Real mutation executor (create_service only).

Never imports or calls the dry-run phase executor. Simulation and dry-run paths
must remain separate to avoid accidental live infrastructure mutation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    REAL_MUTATION_PHASES_FIX108,
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
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
    record_execution_receipt,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    live_create_service_authorization,
)
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    transition_journal_state,
)
from aethos_core.providers.railway.greenfield_adapters.create_service_adapter import (
    create_railway_service,
)

_CREATE_SERVICE_PHASE = "create_service"


@dataclass
class RealMutationExecutionResult:
    journal: dict[str, Any]
    mutation_performed: bool = False
    idempotent_replay: bool = False
    service_id: str = ""
    executed_phases: list[str] = field(default_factory=list)
    detail: str = ""
    policy_blocked: bool = False
    errors: list[str] = field(default_factory=list)


def _record_real_phase_receipt(
    *,
    execution_id: str,
    phase: str,
    status: str,
    mutation_performed: bool,
    detail: str,
    replayed: bool = False,
) -> dict[str, Any]:
    started = datetime.now(UTC)
    started_mono = time.monotonic()
    duration_ms = max(int((time.monotonic() - started_mono) * 1000), 1)
    completed = datetime.now(UTC)
    return record_execution_receipt(
        execution_id=execution_id,
        phase=phase,
        status=status,
        mutation_performed=mutation_performed,
        detail=detail,
        started_at=started.isoformat(),
        completed_at=completed.isoformat(),
        duration_ms=duration_ms,
        replayed=replayed,
        skipped_existing=replayed and not mutation_performed,
    )


def _append_phase_history(
    journal: dict[str, Any],
    *,
    phase: str,
    status: str,
    receipt_id: str,
    mutation_performed: bool,
) -> dict[str, Any]:
    history = list(journal.get("phase_history") or [])
    history.append(
        {
            "phase": phase,
            "status": status,
            "receipt_id": receipt_id,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
    )
    journal["phase_history"] = history
    phases = list(journal.get("phases") or [])
    phases.append(
        {
            "phase": phase,
            "status": status,
            "mutation_performed": mutation_performed,
            "mode": "enabled",
            "receipt_id": receipt_id,
        }
    )
    journal["phases"] = phases
    return journal


def _ensure_execution_locked(journal: dict[str, Any]) -> dict[str, Any]:
    current = str(journal.get("state") or "draft")
    if current in {
        "execution_locked",
        "execution_phase_create_service",
        "execution_partial_failure",
    }:
        return journal
    try:
        if current == "simulation_complete":
            journal = transition_journal_state(journal, to_state="execution_requested")
            journal = save_execution_journal(journal)
            journal = transition_journal_state(journal, to_state="execution_locked")
            return save_execution_journal(journal)
        if current == "execution_requested":
            journal = transition_journal_state(journal, to_state="execution_locked")
            return save_execution_journal(journal)
    except IllegalExecutionTransitionError:
        pass
    return journal


def run_real_mutation_create_service(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
) -> RealMutationExecutionResult:
    """
    Execute governed create_service only (FIX 108). Stops after create_service phase.

    Downstream phases (connect_source, configure_env, trigger_deploy, verify_runtime)
    are intentionally not invoked.
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

    existing_receipt = find_phase_receipt(execution_id=execution_id, phase=_CREATE_SERVICE_PHASE)
    if phase_mutation_recorded(existing_receipt) or str(journal.get("railway_service_id") or "").strip():
        journal["execution_mode"] = "enabled"
        journal["real_mutation_phases_completed"] = list(REAL_MUTATION_PHASES_FIX108)
        journal = save_execution_journal(journal)
        return RealMutationExecutionResult(
            journal=journal,
            mutation_performed=False,
            idempotent_replay=True,
            service_id=str(journal.get("railway_service_id") or ""),
            executed_phases=[],
            detail="create_service already performed for this execution; idempotent replay.",
        )

    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    if not assessed.allows_real_mutation():
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Real Railway mutation blocked by execution enablement policy.",
            errors=list(assessed.blocking_reason_messages),
        )

    environment = str(plan.get("environment") or "")
    from aethos_core.providers.railway.execution_contract.production_policy import (
        production_policy_forward_block_errors,
    )

    prod_errors = production_policy_forward_block_errors(
        environment=environment,
        phase="create_service",
        user_text=user_text,
        execution_id=str(journal.get("execution_id") or ""),
        journal=journal,
        plan=plan,
    )
    if prod_errors:
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Production create_service blocked by production policy (FIX 117).",
            errors=prod_errors,
        )

    if not journal.get("rollback_journal"):
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Rollback journal must exist before any real mutation.",
            errors=["rollback_journal_missing"],
        )

    journal = _ensure_execution_locked(journal)
    journal["execution_mode"] = "enabled"
    journal = save_execution_journal(journal)

    project_name = str(plan.get("project") or "")
    service_name = str(plan.get("service_name") or plan.get("service") or "")
    idempotency_key = str(journal.get("idempotency_key") or "")

    with live_create_service_authorization():
        create_result = create_railway_service(
            project_name=project_name,
            environment_name=environment,
            service_name=service_name,
            idempotency_key=idempotency_key,
            existing_service_id=str(journal.get("railway_service_id") or ""),
        )

    if not create_result.ok:
        receipt = _record_real_phase_receipt(
            execution_id=execution_id,
            phase=_CREATE_SERVICE_PHASE,
            status=STATUS_MUTATION_FAILURE,
            mutation_performed=False,
            detail="; ".join(create_result.errors) or "create_service failed",
        )
        journal = _append_phase_history(
            journal,
            phase=_CREATE_SERVICE_PHASE,
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
            detail="create_service failed.",
            errors=list(create_result.errors),
        )

    mutation_performed = bool(create_result.mutation_performed)
    if mutation_performed:
        receipt_status = STATUS_MUTATION_SUCCESS
    elif create_result.idempotent_replay:
        receipt_status = STATUS_MUTATION_SKIPPED
    else:
        receipt_status = STATUS_MUTATION_SKIPPED
    receipt = _record_real_phase_receipt(
        execution_id=execution_id,
        phase=_CREATE_SERVICE_PHASE,
        status=receipt_status,
        mutation_performed=mutation_performed,
        detail=create_result.detail,
        replayed=bool(create_result.idempotent_replay),
    )
    journal = _append_phase_history(
        journal,
        phase=_CREATE_SERVICE_PHASE,
        status="completed",
        receipt_id=str(receipt.get("receipt_id") or ""),
        mutation_performed=mutation_performed,
    )
    if create_result.service_id:
        journal["railway_service_id"] = create_result.service_id
    elif create_result.ok:
        from aethos_core.providers.railway.greenfield_adapters.target_resolution import (
            find_service_in_project,
        )

        existing = find_service_in_project(
            project_id=str(create_result.project_id or journal.get("railway_project_id") or ""),
            service_name=service_name,
            environment_name=environment,
        )
        if existing and existing.get("service_id"):
            journal["railway_service_id"] = existing["service_id"]
            if not create_result.environment_id and existing.get("environment_id"):
                journal["railway_environment_id"] = existing["environment_id"]
    if create_result.project_id:
        journal["railway_project_id"] = create_result.project_id
    if create_result.environment_id:
        journal["railway_environment_id"] = create_result.environment_id
    journal["real_mutation_phases_completed"] = list(REAL_MUTATION_PHASES_FIX108)

    try:
        journal = transition_journal_state(journal, to_state="execution_phase_create_service")
        journal["rollback_available"] = True
    except IllegalExecutionTransitionError:
        journal["state"] = "execution_phase_create_service"
        journal["rollback_available"] = True
    journal = save_execution_journal(journal)

    detail = create_result.detail or "create_service phase complete."
    if mutation_performed:
        detail = (
            f"{detail} FIX 108 stops after create_service; "
            "connect_source, env writes, and deploy are not performed."
        )
    return RealMutationExecutionResult(
        journal=journal,
        mutation_performed=mutation_performed,
        idempotent_replay=bool(create_result.idempotent_replay),
        service_id=create_result.service_id,
        executed_phases=[_CREATE_SERVICE_PHASE] if mutation_performed else [],
        detail=detail,
    )

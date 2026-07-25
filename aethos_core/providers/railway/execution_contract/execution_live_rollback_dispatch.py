# SPDX-License-Identifier: Apache-2.0
"""
FIX 115 — Governed live rollback dispatch (isolated from forward execution).

Sequence: disconnect_repo_source → revert_env_writes → simulated disable/remove → finalize.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_context import acquire_execution_lock
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    assess_railway_execution_enablement_policy,
    extract_rollback_phrase_from_text,
    validate_rollback_phrase,
)
from aethos_core.providers.railway.execution_contract.execution_idempotency import derive_idempotency_key
from aethos_core.providers.railway.execution_contract.execution_journal import save_execution_journal
from aethos_core.providers.railway.execution_contract.execution_real_mutation_support import (
    record_real_phase_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_ROLLBACK_MUTATION_FAILURE,
    STATUS_ROLLBACK_MUTATION_SKIPPED,
    STATUS_ROLLBACK_SIMULATED_SKIPPED,
    rollback_phase_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_real_rollback_disconnect_executor import (
    run_real_disconnect_connect_source_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_real_rollback_env_configure import (
    run_real_revert_env_configure_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import journal_rollback_phase
from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
    CONNECT_SOURCE_ROLLBACK_ACTION,
    CONNECT_SOURCE_ROLLBACK_PHASE,
    DISABLE_DEPLOYS_ROLLBACK_ACTION,
    DISABLE_DEPLOYS_ROLLBACK_PHASE,
    REMOVE_SERVICE_ROLLBACK_ACTION,
    REMOVE_SERVICE_ROLLBACK_PHASE,
    REVERT_ENV_ROLLBACK_ACTION,
    REVERT_ENV_ROLLBACK_PHASE,
)
from aethos_core.providers.railway.execution_contract.execution_rollback_readiness import (
    assess_railway_rollback_readiness,
)
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    transition_journal_state,
)
from aethos_core.providers.railway.execution_contract.rollback_env_verification import (
    verify_rollback_env_readonly,
)
from aethos_core.providers.railway.execution_contract.source_binding_verification import (
    verify_source_binding_readonly,
)


@dataclass
class LiveRollbackOrchestrationResult:
    journal: dict[str, Any]
    mutation_performed: bool = False
    idempotent_replay: bool = False
    policy_blocked: bool = False
    partial_failure: bool = False
    rollback_completed: bool = False
    executed_phases: list[str] = field(default_factory=list)
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def _disconnect_complete(journal: dict[str, Any], *, execution_id: str) -> bool:
    if journal.get("connect_source_rollback_performed") or journal.get("github_source_disconnected"):
        return True
    receipt = find_phase_receipt(execution_id=execution_id, phase=CONNECT_SOURCE_ROLLBACK_PHASE)
    return rollback_phase_recorded(receipt)


def _revert_env_complete(journal: dict[str, Any], *, execution_id: str) -> bool:
    if journal.get("env_configure_rollback_performed"):
        return True
    receipt = find_phase_receipt(execution_id=execution_id, phase=REVERT_ENV_ROLLBACK_PHASE)
    return rollback_phase_recorded(receipt)


def _simulated_phase_recorded(*, execution_id: str, phase: str) -> bool:
    receipt = find_phase_receipt(execution_id=execution_id, phase=phase)
    return rollback_phase_recorded(receipt)


def _record_simulated_rollback_phase(
    *,
    execution_id: str,
    phase: str,
    action: str,
    journal: dict[str, Any],
) -> dict[str, Any]:
    receipt = record_real_phase_receipt(
        execution_id=execution_id,
        phase=phase,
        status=STATUS_ROLLBACK_SIMULATED_SKIPPED,
        mutation_performed=False,
        detail=f"{action} simulated only in FIX 115 (not executed).",
        rollback_phase=phase,
        rollback_action=action,
    )
    rollback_journal = journal.get("rollback_journal")
    if isinstance(rollback_journal, dict):
        journal["rollback_journal"] = journal_rollback_phase(
            rollback_journal,
            action=action,
            status="simulated",
            detail="simulated only",
        )
    return receipt


def run_single_live_rollback_phase(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
    session_id: str = "default",
) -> LiveRollbackOrchestrationResult:
    """Run at most one live rollback phase per invocation."""
    execution_id = str(journal.get("execution_id") or "")
    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    readiness = assess_railway_rollback_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )

    if not validate_rollback_phrase(phrase=extract_rollback_phrase_from_text(user_text)):
        return LiveRollbackOrchestrationResult(
            journal=journal,
            policy_blocked=True,
            detail="Governed rollback final phrase required.",
            errors=["rollback_phrase_required"],
        )

    if not readiness.ready_for_live_rollback and not (
        _disconnect_complete(journal, execution_id=execution_id)
        or _revert_env_complete(journal, execution_id=execution_id)
    ):
        return LiveRollbackOrchestrationResult(
            journal=journal,
            policy_blocked=True,
            detail="Rollback readiness gate not satisfied.",
            errors=list(readiness.blockers),
        )

    idempotency_key = str(journal.get("idempotency_key") or "") or derive_idempotency_key(plan=plan)
    lock_result = acquire_execution_lock(
        idempotency_key=idempotency_key,
        execution_id=execution_id,
        session_id=session_id,
        project=str(plan.get("project") or ""),
        environment=str(plan.get("environment") or ""),
        service_name=str(plan.get("service_name") or ""),
    )
    if not lock_result.get("ok"):
        return LiveRollbackOrchestrationResult(
            journal=journal,
            policy_blocked=True,
            detail="Could not acquire rollback execution lock.",
            errors=[str(lock_result.get("reason") or "lock_failed")],
        )

    if not _disconnect_complete(journal, execution_id=execution_id):
        if assessed.allows_disconnect_source_rollback():
            result = run_real_disconnect_connect_source_rollback(
                journal=journal,
                plan=plan,
                policy=assessed,
                user_text=user_text,
            )
            journal = result.journal
            if result.policy_blocked or (not result.mutation_performed and not result.idempotent_replay):
                if not result.idempotent_replay and not result.rollback_receipt_recorded:
                    return LiveRollbackOrchestrationResult(
                        journal=journal,
                        policy_blocked=result.policy_blocked,
                        partial_failure=True,
                        detail=result.detail,
                        errors=list(result.errors),
                    )
            return LiveRollbackOrchestrationResult(
                journal=journal,
                mutation_performed=result.mutation_performed,
                idempotent_replay=result.idempotent_replay,
                executed_phases=[CONNECT_SOURCE_ROLLBACK_PHASE],
                detail=result.detail,
            )
        return LiveRollbackOrchestrationResult(
            journal=journal,
            policy_blocked=True,
            detail="disconnect_repo_source rollback disabled.",
            errors=["disconnect_source_disabled"],
        )

    if not _revert_env_complete(journal, execution_id=execution_id):
        if assessed.allows_revert_env_rollback():
            result = run_real_revert_env_configure_rollback(
                journal=journal,
                plan=plan,
                policy=assessed,
                user_text=user_text,
            )
            journal = result.journal
            if result.errors and not result.idempotent_replay:
                return LiveRollbackOrchestrationResult(
                    journal=journal,
                    partial_failure=True,
                    detail=result.detail,
                    errors=list(result.errors),
                )
            return LiveRollbackOrchestrationResult(
                journal=journal,
                mutation_performed=result.mutation_performed,
                idempotent_replay=result.idempotent_replay,
                executed_phases=[REVERT_ENV_ROLLBACK_PHASE],
                detail=result.detail,
            )
        return LiveRollbackOrchestrationResult(
            journal=journal,
            policy_blocked=True,
            detail="revert_env_writes rollback disabled.",
            errors=["revert_env_disabled"],
        )

    if not _simulated_phase_recorded(execution_id=execution_id, phase=DISABLE_DEPLOYS_ROLLBACK_PHASE):
        _record_simulated_rollback_phase(
            execution_id=execution_id,
            phase=DISABLE_DEPLOYS_ROLLBACK_PHASE,
            action=DISABLE_DEPLOYS_ROLLBACK_ACTION,
            journal=journal,
        )
        journal = save_execution_journal(journal)
        return LiveRollbackOrchestrationResult(
            journal=journal,
            executed_phases=[DISABLE_DEPLOYS_ROLLBACK_PHASE],
            detail="disable_deploys recorded as simulated skip.",
        )

    if not _simulated_phase_recorded(execution_id=execution_id, phase=REMOVE_SERVICE_ROLLBACK_PHASE):
        _record_simulated_rollback_phase(
            execution_id=execution_id,
            phase=REMOVE_SERVICE_ROLLBACK_PHASE,
            action=REMOVE_SERVICE_ROLLBACK_ACTION,
            journal=journal,
        )
        journal = save_execution_journal(journal)
        return LiveRollbackOrchestrationResult(
            journal=journal,
            executed_phases=[REMOVE_SERVICE_ROLLBACK_PHASE],
            detail="remove_created_service recorded as simulated skip.",
        )

    if journal.get("rollback_completed"):
        return LiveRollbackOrchestrationResult(
            journal=journal,
            idempotent_replay=True,
            rollback_completed=True,
            detail="Rollback already finalized; idempotent replay.",
        )

    return _finalize_live_rollback(journal=journal, plan=plan, user_text=user_text)


def run_live_rollback_orchestration(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
    session_id: str = "default",
    max_steps: int = 6,
) -> LiveRollbackOrchestrationResult:
    """Run rollback phases in order until complete, failure, or step limit."""
    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    executed: list[str] = []
    mutation_performed = False
    detail_parts: list[str] = []

    current_journal = journal
    for _ in range(max_steps):
        step = run_single_live_rollback_phase(
            journal=current_journal,
            plan=plan,
            policy=assessed,
            user_text=user_text,
            session_id=session_id,
        )
        current_journal = step.journal
        executed.extend(step.executed_phases or [])
        mutation_performed = mutation_performed or step.mutation_performed
        if step.detail:
            detail_parts.append(step.detail)
        if step.partial_failure or (step.policy_blocked and not step.idempotent_replay):
            return LiveRollbackOrchestrationResult(
                journal=current_journal,
                mutation_performed=mutation_performed,
                policy_blocked=step.policy_blocked,
                partial_failure=True,
                executed_phases=executed,
                detail="; ".join(detail_parts) or step.detail,
                errors=list(step.errors),
            )
        if step.rollback_completed:
            return LiveRollbackOrchestrationResult(
                journal=current_journal,
                mutation_performed=mutation_performed,
                idempotent_replay=step.idempotent_replay,
                rollback_completed=True,
                executed_phases=executed,
                detail="; ".join(detail_parts) or step.detail,
            )
        if not step.executed_phases and step.idempotent_replay:
            finalized = _finalize_live_rollback(
                journal=current_journal,
                plan=plan,
                user_text=user_text,
            )
            finalized.executed_phases = executed
            return finalized

    return LiveRollbackOrchestrationResult(
        journal=current_journal,
        mutation_performed=mutation_performed,
        partial_failure=True,
        executed_phases=executed,
        detail="rollback orchestration step limit reached",
        errors=["rollback_step_limit"],
    )


def _finalize_live_rollback(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    user_text: str,
) -> LiveRollbackOrchestrationResult:
    execution_id = str(journal.get("execution_id") or "")
    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")

    binding_ok = bool(journal.get("github_source_disconnected")) or not journal.get("github_source_bound")
    if service_id and environment_id and journal.get("github_source_bound"):
        binding = verify_source_binding_readonly(
            environment_id=environment_id,
            service_id=service_id,
            journal_binding=journal.get("github_source_bound"),
        )
        binding_ok = bool(binding.verified)

    env_ok = True
    if service_id and environment_id:
        env_check = verify_rollback_env_readonly(
            environment_id=environment_id,
            service_id=service_id,
        )
        env_ok = bool(env_check.verified)
        journal["rollback_env_verification"] = env_check.__dict__

    journal["rollback_readonly_verification"] = {
        "source_disconnected": binding_ok,
        "env_names_absent": env_ok,
    }

    try:
        journal = transition_journal_state(journal, to_state="execution_rolled_back")
    except Exception:
        journal["state"] = "execution_rolled_back"

    rollback_journal = journal.get("rollback_journal")
    if isinstance(rollback_journal, dict):
        rollback_journal = dict(rollback_journal)
        rollback_journal["status"] = "completed"
        journal["rollback_journal"] = rollback_journal

    journal["rollback_completed"] = True
    journal["live_rollback_orchestration_performed"] = True
    journal = save_execution_journal(journal)

    if not binding_ok or not env_ok:
        receipt = record_real_phase_receipt(
            execution_id=execution_id,
            phase="rollback_finalize",
            status=STATUS_ROLLBACK_MUTATION_FAILURE,
            mutation_performed=False,
            detail="rollback finalize readonly verification failed",
        )
        journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
        journal = save_execution_journal(journal)
        return LiveRollbackOrchestrationResult(
            journal=journal,
            partial_failure=True,
            rollback_completed=False,
            detail="Rollback mutations recorded but readonly verification failed.",
            errors=["rollback_verification_failed"],
        )

    return LiveRollbackOrchestrationResult(
        journal=journal,
        rollback_completed=True,
        detail="Governed live rollback orchestration complete.",
    )

# SPDX-License-Identifier: Apache-2.0
"""
FIX 118 — Production shadow orchestration (isolated from staging dry-run and live executors).

Never imports live mutation adapters or execution_dry_run_executor.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.production_shadow_contract_models import (
    FORWARD_SHADOW_PHASES,
    PRODUCTION_SHADOW_EXECUTION_MODE,
    PRODUCTION_VERIFICATION_SHADOW_PHASE,
    ROLLBACK_SHADOW_PHASES,
)
from aethos_core.providers.railway.execution_contract.production_verification_service import (
    run_production_shadow_runtime_verification,
)
from aethos_core.providers.railway.execution_contract.production_shadow_gate import (
    assess_production_shadow_gate,
    assess_production_shadow_rollback_gate,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    get_or_create_shadow_journal,
    save_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_shadow_receipts import (
    find_shadow_phase_receipt,
    list_shadow_receipts,
    record_shadow_receipt,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    assess_railway_production_policy,
)

_FORBIDDEN_IMPORT_TOKENS = (
    "execution_real_mutation_dispatch",
    "execution_real_mutation_executor",
    "execution_dry_run_executor",
    "create_service_adapter",
    "connect_github_source",
    "trigger_railway_deploy",
    "revert_env_configure_adapter",
    "execution_live_rollback_dispatch",
)


@dataclass
class ProductionShadowOrchestrationResult:
    journal: dict[str, Any]
    executed_phases: list[str] = field(default_factory=list)
    skipped_phases: list[str] = field(default_factory=list)
    policy_blocked: bool = False
    shadow_completed: bool = False
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def assert_shadow_executor_isolation() -> bool:
    """Static guard — shadow executor must not import live/staging mutation paths."""
    module = sys.modules.get(__name__)
    path = getattr(module, "__file__", None)
    if not path:
        return True
    import_lines = [
        line
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    blob = "\n".join(import_lines)
    return all(token not in blob for token in _FORBIDDEN_IMPORT_TOKENS)


def _append_shadow_phase(journal: dict[str, Any], *, phase: str, receipt_id: str) -> dict[str, Any]:
    phases = list(journal.get("phases") or [])
    phases.append(
        {
            "phase": phase,
            "status": "shadow_rehearsal_success",
            "mutation_performed": False,
            "mode": PRODUCTION_SHADOW_EXECUTION_MODE,
            "receipt_id": receipt_id,
        }
    )
    journal["phases"] = phases
    return journal


def _run_shadow_phase(
    *,
    execution_id: str,
    phase: str,
    policy_blockers: list[str],
) -> tuple[dict[str, Any], bool]:
    existing = find_shadow_phase_receipt(execution_id=execution_id, phase=phase)
    if existing:
        receipt = record_shadow_receipt(
            execution_id=execution_id,
            phase=phase,
            status="shadow_rehearsal_replay",
            detail=f"shadow replay: {phase}",
            replayed=True,
            skipped_existing=True,
            policy_checks_passed=not policy_blockers,
            policy_blockers=policy_blockers,
        )
        return receipt, True

    receipt = record_shadow_receipt(
        execution_id=execution_id,
        phase=phase,
        status="shadow_rehearsal_success",
        detail=f"production shadow rehearsal: {phase}",
        policy_checks_passed=not policy_blockers,
        policy_blockers=policy_blockers,
    )
    return receipt, False


def run_production_shadow_forward(
    *,
    execution_id: str,
    plan: dict[str, Any],
    session_id: str = "",
    user_text: str = "",
) -> ProductionShadowOrchestrationResult:
    gate = assess_production_shadow_gate(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
    )
    if not gate.ready:
        return ProductionShadowOrchestrationResult(
            journal={},
            policy_blocked=True,
            detail="Production shadow forward rehearsal blocked by policy gate.",
            blockers=gate.blockers,
        )

    journal, _created = get_or_create_shadow_journal(
        execution_id=execution_id,
        plan=plan,
        session_id=session_id,
    )
    policy = assess_railway_production_policy(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
        journal=journal,
    )
    policy_blockers = list(policy.blockers)

    executed: list[str] = []
    skipped: list[str] = []

    for phase in FORWARD_SHADOW_PHASES:
        if phase == PRODUCTION_VERIFICATION_SHADOW_PHASE:
            verify_result = run_production_shadow_runtime_verification(
                execution_id=execution_id,
                plan=plan,
                shadow_journal=journal,
                user_text=user_text,
                orchestrating_forward=True,
            )
            journal = verify_result.journal
            receipt_id = str(verify_result.receipt.get("receipt_id") or "")
            journal = _append_shadow_phase(
                journal,
                phase=phase,
                receipt_id=receipt_id,
            )
            executed.append(phase)
            continue

        receipt, was_skip = _run_shadow_phase(
            execution_id=execution_id,
            phase=phase,
            policy_blockers=policy_blockers,
        )
        if phase == "trigger_deploy_shadow":
            journal["shadow_deploy_context"] = {
                "deployment_id": "shadow-deploy-sim",
                "deployment_state": "success",
            }
            journal = save_shadow_journal(journal)
        journal = _append_shadow_phase(
            journal,
            phase=phase,
            receipt_id=str(receipt.get("receipt_id") or ""),
        )
        if was_skip:
            skipped.append(phase)
        else:
            executed.append(phase)

    journal["state"] = "shadow_forward_completed"
    journal["forward_shadow_completed"] = True
    journal["live_mutation_boundary"] = "blocked"
    journal = save_shadow_journal(journal)

    return ProductionShadowOrchestrationResult(
        journal=journal,
        executed_phases=executed,
        skipped_phases=skipped,
        shadow_completed=True,
        detail=(
            "Production shadow forward rehearsal completed. "
            "All phases recorded with mutation_performed=false."
        ),
    )


def run_production_shadow_rollback(
    *,
    execution_id: str,
    plan: dict[str, Any],
    session_id: str = "",
    user_text: str = "",
) -> ProductionShadowOrchestrationResult:
    from aethos_core.providers.railway.execution_contract.production_rollback_escalation import (
        assess_rollback_escalation_gate,
        create_or_refresh_escalation_from_verification,
        mark_shadow_rehearsal_completed,
    )

    journal = get_or_create_shadow_journal(
        execution_id=execution_id,
        plan=plan,
        session_id=session_id,
    )[0]

    create_or_refresh_escalation_from_verification(
        execution_id=execution_id,
        plan=plan,
        session_id=session_id,
    )
    escalation_gate = assess_rollback_escalation_gate(
        execution_id=execution_id,
        plan=plan,
        user_text=user_text,
        session_id=session_id,
    )
    if not escalation_gate.ready_for_shadow_rehearsal:
        return ProductionShadowOrchestrationResult(
            journal=journal,
            policy_blocked=True,
            detail="Production shadow rollback blocked by rollback escalation framework (FIX 120).",
            blockers=escalation_gate.blockers,
        )

    gate = assess_production_shadow_rollback_gate(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
        journal=journal,
    )
    if not gate.ready:
        return ProductionShadowOrchestrationResult(
            journal=journal,
            policy_blocked=True,
            detail="Production shadow rollback rehearsal blocked by policy gate.",
            blockers=gate.blockers,
        )

    policy = assess_railway_production_policy(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
        journal=journal,
    )
    policy_blockers = list(policy.blockers)

    executed: list[str] = []
    skipped: list[str] = []

    for phase in ROLLBACK_SHADOW_PHASES:
        receipt, was_skip = _run_shadow_phase(
            execution_id=execution_id,
            phase=phase,
            policy_blockers=policy_blockers,
        )
        journal = _append_shadow_phase(
            journal,
            phase=phase,
            receipt_id=str(receipt.get("receipt_id") or ""),
        )
        if was_skip:
            skipped.append(phase)
        else:
            executed.append(phase)

    # Orchestration capstone receipt
    cap_receipt, cap_skip = _run_shadow_phase(
        execution_id=execution_id,
        phase="rollback_shadow",
        policy_blockers=policy_blockers,
    )
    journal = _append_shadow_phase(
        journal,
        phase="rollback_shadow",
        receipt_id=str(cap_receipt.get("receipt_id") or ""),
    )
    if cap_skip:
        skipped.append("rollback_shadow")
    else:
        executed.append("rollback_shadow")

    journal["state"] = "shadow_rollback_completed"
    journal["rollback_shadow_completed"] = True
    journal["rollback_escalation"] = "manual_only"
    journal = save_shadow_journal(journal)

    _ = list_shadow_receipts(execution_id=execution_id)

    mark_shadow_rehearsal_completed(execution_id=execution_id, session_id=session_id)
    journal["rollback_escalation_state"] = "shadow_rehearsal_completed"
    journal = save_shadow_journal(journal)

    return ProductionShadowOrchestrationResult(
        journal=journal,
        executed_phases=executed,
        skipped_phases=skipped,
        shadow_completed=True,
        detail=(
            "Production shadow rollback rehearsal completed (escalation manual-only). "
            "mutation_performed=false on all receipts. Escalation audit trail updated."
        ),
    )

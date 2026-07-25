# SPDX-License-Identifier: Apache-2.0
"""Dry-run phase executor — journal + receipt simulation, no Railway API mutations."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    EXECUTION_PHASES,
    PHASE_TO_STATE,
    ExecutionPhaseName,
)
from aethos_core.providers.railway.execution_contract.execution_journal import save_execution_journal
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
    list_execution_receipts,
    record_execution_receipt,
    record_rollback_simulation_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    transition_journal_state,
)

_SIMULATED_FAILURE_RX = re.compile(
    r"\b(?:simulate|execute)\s+railway\s+service\s+creation\s+with\s+([\w_]+)\s+failure\b",
    re.I,
)


@dataclass
class DryRunPhaseExecutionResult:
    journal: dict[str, Any]
    executed_phases: list[str] = field(default_factory=list)
    skipped_phases: list[str] = field(default_factory=list)
    simulated_phase_count: int = 0
    partial_failure: bool = False
    failure_phase: str = ""
    all_phases_skipped: bool = False
    detail: str = ""


def parse_simulated_failure_phase(text: str) -> str | None:
    """Extract phase name from `simulate railway service creation with <phase> failure`."""
    match = _SIMULATED_FAILURE_RX.search((text or "").strip())
    if not match:
        return None
    phase = match.group(1).strip().lower()
    if phase in EXECUTION_PHASES:
        return phase
    aliases = {
        "verify": "verify_runtime",
        "verify_runtime_health": "verify_runtime",
        "deploy": "trigger_deploy",
        "trigger": "trigger_deploy",
        "env": "configure_env",
        "source": "connect_source",
        "service": "create_service",
    }
    return aliases.get(phase)


def _advance_to_phase_state(journal: dict[str, Any], *, phase: ExecutionPhaseName) -> dict[str, Any]:
    target_state = PHASE_TO_STATE[phase]
    current = str(journal.get("state") or "draft")
    if current == target_state:
        return journal
    try:
        return transition_journal_state(journal, to_state=target_state)  # type: ignore[arg-type]
    except IllegalExecutionTransitionError:
        return journal


def _ensure_execution_locked(journal: dict[str, Any]) -> dict[str, Any]:
    current = str(journal.get("state") or "draft")
    if current in {"execution_locked", *PHASE_TO_STATE.values(), "execution_completed", "execution_partial_failure"}:
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


def _append_phase_history(
    journal: dict[str, Any],
    *,
    phase: str,
    status: str,
    receipt_id: str,
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
            "mutation_performed": False,
            "mode": "dry_run",
            "receipt_id": receipt_id,
        }
    )
    journal["phases"] = phases
    return journal


def _record_dry_run_phase_receipt(
    *,
    execution_id: str,
    phase: str,
    status: str,
    skipped_existing: bool = False,
    replayed: bool = False,
    detail: str = "",
) -> dict[str, Any]:
    started = datetime.now(UTC)
    started_mono = time.monotonic()
    duration_ms = max(int((time.monotonic() - started_mono) * 1000), 1)
    completed = datetime.now(UTC)
    return record_execution_receipt(
        execution_id=execution_id,
        phase=phase,
        status=status,
        mutation_performed=False,
        detail=detail,
        started_at=started.isoformat(),
        completed_at=completed.isoformat(),
        duration_ms=duration_ms,
        skipped_existing=skipped_existing,
        replayed=replayed,
    )


def run_dry_run_phase_execution(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any] | None = None,
    failure_phase: str | None = None,
    user_text: str = "",
) -> DryRunPhaseExecutionResult:
    """
    Simulate governed execution phases one at a time (dry_run mode only).

    Persists journal state transitions and per-phase receipts. Never calls Railway APIs.
    """
    _ = plan
    simulated_failure = failure_phase or parse_simulated_failure_phase(user_text)
    execution_id = str(journal.get("execution_id") or "")
    if not execution_id:
        return DryRunPhaseExecutionResult(journal=journal, detail="No execution_id on journal.")

    current = str(journal.get("state") or "draft")
    if current in {"execution_completed", "execution_rolled_back"}:
        skipped = [p for p in EXECUTION_PHASES if find_phase_receipt(execution_id=execution_id, phase=p)]
        return DryRunPhaseExecutionResult(
            journal=journal,
            skipped_phases=skipped,
            simulated_phase_count=len(skipped),
            all_phases_skipped=bool(skipped),
            detail=_format_skip_detail(skipped),
        )

    if current == "execution_partial_failure":
        skipped = [p for p in EXECUTION_PHASES if find_phase_receipt(execution_id=execution_id, phase=p)]
        return DryRunPhaseExecutionResult(
            journal=journal,
            skipped_phases=skipped,
            partial_failure=True,
            failure_phase=str(journal.get("dry_run_failure_phase") or simulated_failure or ""),
            simulated_phase_count=len(skipped),
            all_phases_skipped=True,
            detail="Execution is in partial_failure; no new simulated phases were executed.",
        )

    journal = _ensure_execution_locked(journal)
    journal["execution_mode"] = "dry_run"
    journal = save_execution_journal(journal)

    executed: list[str] = []
    skipped: list[str] = []

    for phase in EXECUTION_PHASES:
        existing = find_phase_receipt(execution_id=execution_id, phase=phase)
        if existing:
            skipped.append(phase)
            journal = _advance_to_phase_state(journal, phase=phase)  # type: ignore[arg-type]
            continue

        if simulated_failure and phase == simulated_failure:
            journal = _advance_to_phase_state(journal, phase=phase)  # type: ignore[arg-type]
            receipt = _record_dry_run_phase_receipt(
                execution_id=execution_id,
                phase=phase,
                status="simulated_failure",
                detail=f"dry_run simulated failure at {phase}",
            )
            journal = _append_phase_history(
                journal,
                phase=phase,
                status="failed",
                receipt_id=str(receipt.get("receipt_id") or ""),
            )
            journal["dry_run_failure_phase"] = phase
            try:
                journal = transition_journal_state(journal, to_state="execution_partial_failure")
                journal["rollback_available"] = True
            except IllegalExecutionTransitionError:
                journal["state"] = "execution_partial_failure"
                journal["rollback_available"] = True
            journal = save_execution_journal(journal)
            record_rollback_simulation_receipts(
                execution_id=execution_id,
                completed_phases=executed,
            )
            return DryRunPhaseExecutionResult(
                journal=journal,
                executed_phases=executed + [phase],
                skipped_phases=skipped,
                simulated_phase_count=len(list_execution_receipts(execution_id=execution_id)),
                partial_failure=True,
                failure_phase=phase,
                detail=f"Dry-run simulated failure at phase `{phase}`. Rollback receipts recorded.",
            )

        journal = _advance_to_phase_state(journal, phase=phase)  # type: ignore[arg-type]
        receipt = _record_dry_run_phase_receipt(
            execution_id=execution_id,
            phase=phase,
            status="simulated_success",
            detail="dry_run phase simulation",
        )
        journal = _append_phase_history(
            journal,
            phase=phase,
            status="completed",
            receipt_id=str(receipt.get("receipt_id") or ""),
        )
        journal = save_execution_journal(journal)
        executed.append(phase)

    try:
        if str(journal.get("state") or "") != "execution_completed":
            journal = transition_journal_state(journal, to_state="execution_completed")
            journal["rollback_available"] = False
            journal = save_execution_journal(journal)
    except IllegalExecutionTransitionError:
        journal = save_execution_journal(journal)

    all_skipped = bool(skipped) and not executed
    detail = _format_skip_detail(skipped) if all_skipped else (
        "Dry-run phases simulated step-by-step." if executed else _format_skip_detail(skipped)
    )
    return DryRunPhaseExecutionResult(
        journal=journal,
        executed_phases=executed,
        skipped_phases=skipped,
        simulated_phase_count=len(list_execution_receipts(execution_id=execution_id)),
        all_phases_skipped=all_skipped,
        detail=detail,
    )


def _format_skip_detail(skipped: list[str]) -> str:
    if not skipped:
        return ""
    lines = ["Execution already simulated for:"]
    lines.extend(f"- {phase}" for phase in skipped)
    lines.append("")
    lines.append("No new simulated phases were executed.")
    return "\n".join(lines)

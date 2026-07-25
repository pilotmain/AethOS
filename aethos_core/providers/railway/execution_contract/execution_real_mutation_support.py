# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for real-mutation executors (not used by dry-run)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_journal import save_execution_journal
from aethos_core.providers.railway.execution_contract.execution_receipts import record_execution_receipt
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    transition_journal_state,
)


def record_real_phase_receipt(
    *,
    execution_id: str,
    phase: str,
    status: str,
    mutation_performed: bool,
    detail: str,
    replayed: bool = False,
    receipt_group: str = "",
    env_var_names: list[str] | None = None,
    rollback_phase: str = "",
    rollback_action: str = "",
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
        receipt_group=receipt_group,
        env_var_names=env_var_names,
        rollback_phase=rollback_phase,
        rollback_action=rollback_action,
    )


def append_real_phase_history(
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


def ensure_execution_locked(journal: dict[str, Any]) -> dict[str, Any]:
    current = str(journal.get("state") or "draft")
    if current in {
        "execution_locked",
        "execution_phase_create_service",
        "execution_phase_connect_source",
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

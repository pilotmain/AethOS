# SPDX-License-Identifier: Apache-2.0
"""Rollback contract and journal for Railway execution."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    ROLLBACK_ACTIONS,
)
from aethos_core.providers.railway.execution_contract.execution_journal import save_execution_journal


def build_rollback_journal(*, execution_id: str) -> dict[str, Any]:
    """Plan rollback actions before any future mutation (contract-only today)."""
    now = datetime.now(UTC).isoformat()
    return {
        "rollback_id": f"rback-{uuid.uuid4().hex[:12]}",
        "execution_id": execution_id,
        "created_at": now,
        "status": "planned",
        "executable": False,
        "actions": [
            {
                "action": action,
                "status": "planned",
                "journaled_at": now,
                "mutation_performed": False,
            }
            for action in ROLLBACK_ACTIONS
        ],
        "phases": [],
    }


def attach_rollback_journal(journal: dict[str, Any]) -> dict[str, Any]:
    execution_id = str(journal.get("execution_id") or "")
    rollback = build_rollback_journal(execution_id=execution_id)
    updated = dict(journal)
    updated["rollback_journal"] = rollback
    updated["rollback_ready"] = True
    updated["rollback_available"] = True
    return save_execution_journal(updated)


def journal_rollback_phase(
    rollback_journal: dict[str, Any],
    *,
    action: str,
    status: str,
    detail: str = "",
) -> dict[str, Any]:
    updated = dict(rollback_journal)
    phases = list(updated.get("phases") or [])
    phases.append(
        {
            "action": action,
            "status": status,
            "detail": detail,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
    )
    updated["phases"] = phases
    return updated


def mark_rollback_executed(journal: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.railway.execution_contract.execution_state_machine import (
        transition_journal_state,
    )

    updated = dict(journal)
    rollback = dict(updated.get("rollback_journal") or {})
    rollback["status"] = "simulated"
    for row in list(rollback.get("actions") or []):
        row["status"] = "simulated"
        row["mutation_performed"] = False
    updated["rollback_journal"] = rollback
    if str(updated.get("state")) == "execution_partial_failure":
        updated = transition_journal_state(updated, to_state="execution_rolled_back")
    return save_execution_journal(updated)

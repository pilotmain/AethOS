# SPDX-License-Identifier: Apache-2.0
"""FIX 110 — connect_source rollback contract (read-only planning)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    forward_live_connect_source_mutation_recorded,
    phase_mutation_recorded,
    rollback_phase_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
    list_rollback_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
    CONNECT_SOURCE_FORWARD_PHASE,
    CONNECT_SOURCE_ROLLBACK_ACTION,
    CONNECT_SOURCE_ROLLBACK_PHASE,
    CONNECT_SOURCE_ROLLBACK_STEPS,
    REAL_ROLLBACK_ACTIONS_FIX111,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
    is_railway_mutation_kill_switch_active,
)


@dataclass(frozen=True)
class ConnectSourceRollbackContract:
    execution_id: str
    rollback_phase: str
    rollback_action: str
    forward_phase: str
    repository: str
    branch: str
    service_id: str
    environment_id: str
    dry_run_only: bool
    live_rollback_enabled: bool
    kill_switch_active: bool
    forward_phase_recorded: bool
    forward_live_mutation_recorded: bool
    rollback_receipt_recorded: bool
    eligible_for_dry_run_rollback: bool
    eligible_for_live_rollback: bool
    steps: tuple[str, ...] = CONNECT_SOURCE_ROLLBACK_STEPS
    future_live_actions: tuple[str, ...] = REAL_ROLLBACK_ACTIONS_FIX111
    blockers: list[str] = field(default_factory=list)
    blocker_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "rollback_phase": self.rollback_phase,
            "rollback_action": self.rollback_action,
            "forward_phase": self.forward_phase,
            "repository": self.repository,
            "branch": self.branch,
            "service_id": self.service_id,
            "environment_id": self.environment_id,
            "dry_run_only": self.dry_run_only,
            "live_rollback_enabled": self.live_rollback_enabled,
            "kill_switch_active": self.kill_switch_active,
            "forward_phase_recorded": self.forward_phase_recorded,
            "forward_live_mutation_recorded": self.forward_live_mutation_recorded,
            "rollback_receipt_recorded": self.rollback_receipt_recorded,
            "eligible_for_dry_run_rollback": self.eligible_for_dry_run_rollback,
            "eligible_for_live_rollback": self.eligible_for_live_rollback,
            "steps": list(self.steps),
            "future_live_actions": list(self.future_live_actions),
            "blockers": list(self.blockers),
            "blocker_messages": list(self.blocker_messages),
        }


def build_connect_source_rollback_contract(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
) -> ConnectSourceRollbackContract:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")
    binding = journal.get("github_source_bound") if isinstance(journal.get("github_source_bound"), dict) else {}
    repo = str(binding.get("repository") or plan.get("repo") or "")
    branch = str(binding.get("branch") or plan.get("branch") or "main")
    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")

    forward_receipt = (
        find_phase_receipt(execution_id=execution_id, phase=CONNECT_SOURCE_FORWARD_PHASE)
        if execution_id
        else None
    )
    rollback_receipt = (
        find_phase_receipt(execution_id=execution_id, phase=CONNECT_SOURCE_ROLLBACK_PHASE)
        if execution_id
        else None
    )
    forward_recorded = bool(journal.get("github_source_bound")) or phase_mutation_recorded(
        forward_receipt
    ) or (
        forward_receipt is not None
        and str(forward_receipt.get("status") or "") in {"simulated_success", "mutation_success", "mutation_skipped"}
    )
    forward_live_recorded = forward_live_connect_source_mutation_recorded(forward_receipt)
    rollback_recorded = rollback_phase_recorded(rollback_receipt)

    blockers: list[str] = []
    messages: list[str] = []
    if not execution_id:
        blockers.append("execution_id_missing")
        messages.append("No execution_id — enroll execution journal first.")
    if not forward_recorded:
        blockers.append("connect_source_not_recorded")
        messages.append("connect_source forward phase has not been recorded; nothing to roll back.")
    if rollback_recorded:
        blockers.append("rollback_already_recorded")
        messages.append("rollback_connect_source receipt already exists (idempotent replay).")

    from aethos_core.config import get_settings

    live_enabled = bool(getattr(get_settings(), "railway_greenfield_disconnect_source_enabled", False))
    kill_switch = is_railway_mutation_kill_switch_active()

    eligible_dry = bool(execution_id and forward_recorded and not rollback_recorded)
    live_blockers: list[str] = []
    live_messages: list[str] = []
    if not forward_live_recorded:
        live_blockers.append("forward_live_connect_source_required")
        live_messages.append(
            "Live rollback requires a forward connect_source mutation receipt (mutation_performed)."
        )
    if not live_enabled:
        live_blockers.append("disconnect_source_disabled")
        live_messages.append("railway_greenfield_disconnect_source_enabled=false (default).")
    if kill_switch:
        live_blockers.append("mutation_kill_switch")
        live_messages.append("Railway greenfield mutation kill switch is active.")
    if not service_id:
        live_blockers.append("service_id_missing")
    if not environment_id:
        live_blockers.append("environment_id_missing")

    eligible_live = bool(
        execution_id
        and forward_live_recorded
        and not rollback_recorded
        and live_enabled
        and not kill_switch
        and service_id
        and environment_id
    )

    return ConnectSourceRollbackContract(
        execution_id=execution_id,
        rollback_phase=CONNECT_SOURCE_ROLLBACK_PHASE,
        rollback_action=CONNECT_SOURCE_ROLLBACK_ACTION,
        forward_phase=CONNECT_SOURCE_FORWARD_PHASE,
        repository=repo,
        branch=branch,
        service_id=service_id,
        environment_id=environment_id,
        dry_run_only=not live_enabled,
        live_rollback_enabled=live_enabled,
        kill_switch_active=kill_switch,
        forward_phase_recorded=forward_recorded,
        forward_live_mutation_recorded=forward_live_recorded,
        rollback_receipt_recorded=rollback_recorded,
        eligible_for_dry_run_rollback=eligible_dry,
        eligible_for_live_rollback=eligible_live,
        blockers=blockers + live_blockers,
        blocker_messages=messages + live_messages,
    )


def list_connect_source_rollback_timeline(
    *,
    execution_id: str,
) -> list[dict[str, Any]]:
    """Ordered rollback receipts for connect_source scope."""
    rows = list_rollback_receipts(execution_id=execution_id)
    return [r for r in rows if str(r.get("phase") or "") == CONNECT_SOURCE_ROLLBACK_PHASE] or rows

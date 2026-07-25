# SPDX-License-Identifier: Apache-2.0
"""FIX 115 — readiness gate for governed live rollback orchestration."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.connect_source_rollback_contract import (
    build_connect_source_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    load_execution_lock,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    ROLLBACK_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
    extract_rollback_phrase_from_text,
    is_rollback_blocked_environment,
    validate_rollback_phrase,
)
from aethos_core.providers.railway.execution_contract.execution_idempotency import derive_idempotency_key
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    forward_live_connect_source_mutation_recorded,
    forward_live_configure_env_group_recorded,
    phase_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_group_receipt,
    find_phase_receipt,
    list_forward_phase_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
    DISABLE_DEPLOYS_ROLLBACK_ACTION,
    REMOVE_SERVICE_ROLLBACK_ACTION,
    REVERT_ENV_ROLLBACK_ACTION,
)
from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    ENV_CONFIGURE_GROUPS,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
    is_railway_mutation_kill_switch_active,
)

_ROLLBACK_READINESS_RX = re.compile(
    r"\b(?:check|show)\s+railway\s+rollback\s+readiness\b",
    re.I,
)
_ROLLBACK_WHY_RX = re.compile(
    r"\bwhy\s+can'?t\s+railway\s+rollback\s+start\??",
    re.I,
)


@dataclass(frozen=True)
class RailwayRollbackReadiness:
    ready_for_live_rollback: bool
    staging_only: bool
    live_forward_execution_exists: bool
    rollback_contract_present: bool
    rollback_lock_available: bool
    disconnect_source_enabled: bool
    revert_env_enabled: bool
    production_target: bool
    rollback_phrase_present: bool
    kill_switch_active: bool
    phases_available: tuple[str, ...] = ()
    phases_simulated_only: tuple[str, ...] = ()
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready_for_live_rollback": self.ready_for_live_rollback,
            "staging_only": self.staging_only,
            "live_forward_execution_exists": self.live_forward_execution_exists,
            "rollback_contract_present": self.rollback_contract_present,
            "rollback_lock_available": self.rollback_lock_available,
            "disconnect_source_enabled": self.disconnect_source_enabled,
            "revert_env_enabled": self.revert_env_enabled,
            "production_target": self.production_target,
            "rollback_phrase_present": self.rollback_phrase_present,
            "kill_switch_active": self.kill_switch_active,
            "phases_available": list(self.phases_available),
            "phases_simulated_only": list(self.phases_simulated_only),
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def is_railway_rollback_readiness_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(_ROLLBACK_READINESS_RX.search(raw) or _ROLLBACK_WHY_RX.search(raw))


def _forward_live_exists(execution_id: str, journal: dict[str, Any]) -> bool:
    if not execution_id:
        return False
    forward = list_forward_phase_receipts(execution_id=execution_id)
    for receipt in forward:
        if phase_mutation_recorded(receipt) and bool(receipt.get("mutation_performed")):
            return True
    if str(journal.get("railway_service_id") or "").strip():
        connect = find_phase_receipt(execution_id=execution_id, phase="connect_source")
        if forward_live_connect_source_mutation_recorded(connect):
            return True
    return False


def assess_railway_rollback_readiness(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
    user_text: str = "",
) -> RailwayRollbackReadiness:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")
    environment = str(plan.get("environment") or journal.get("environment") or "")

    policy = assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    connect_contract = build_connect_source_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )
    idempotency_key = str(journal.get("idempotency_key") or "")
    if not idempotency_key and plan:
        idempotency_key = derive_idempotency_key(plan=plan)
    lock = load_execution_lock(idempotency_key=idempotency_key) if idempotency_key else None
    lock_available = lock is None or str(lock.get("execution_id") or "") == execution_id

    production_target = is_rollback_blocked_environment(environment)
    staging_only = not production_target
    forward_exists = _forward_live_exists(execution_id, journal)
    rollback_contract = bool(journal.get("rollback_journal"))
    disconnect_enabled = policy.allows_disconnect_source_rollback()
    revert_enabled = policy.allows_revert_env_rollback()
    phrase_present = validate_rollback_phrase(phrase=extract_rollback_phrase_from_text(user_text))
    kill_switch = is_railway_mutation_kill_switch_active()

    phases_available: list[str] = []
    if disconnect_enabled and connect_contract.forward_live_mutation_recorded:
        phases_available.append("disconnect_repo_source")
    configure_live = False
    for group_id, _names in ENV_CONFIGURE_GROUPS:
        receipt = find_phase_group_receipt(
            execution_id=execution_id,
            phase="configure_env",
            receipt_group=group_id,
        )
        if forward_live_configure_env_group_recorded(receipt):
            configure_live = True
            break
    if revert_enabled and configure_live:
        phases_available.append("revert_env_writes")

    phases_simulated = [DISABLE_DEPLOYS_ROLLBACK_ACTION, REMOVE_SERVICE_ROLLBACK_ACTION]

    blockers: list[str] = []
    messages: list[str] = []
    if production_target:
        blockers.append("production_rollback_blocked")
        messages.append(
            "Production rollback is not permitted. Escalation is manual-only "
            "(incident commander + operator quorum); autonomous rollback is prohibited."
        )
    if kill_switch:
        blockers.append("mutation_kill_switch_active")
    if not forward_exists:
        blockers.append("forward_live_execution_required")
        messages.append("At least one live forward mutation receipt is required.")
    if not rollback_contract:
        blockers.append("rollback_contract_missing")
    if not lock_available:
        blockers.append("rollback_lock_unavailable")
    if not disconnect_enabled and not revert_enabled:
        blockers.append("rollback_flags_disabled")
        messages.append(
            "Enable RAILWAY_GREENFIELD_DISCONNECT_SOURCE_ENABLED and/or "
            "RAILWAY_GREENFIELD_REVERT_ENV_ENABLED."
        )
    if not phrase_present:
        blockers.append("rollback_phrase_required")
        messages.append(f"Rollback requires exact phrase: {ROLLBACK_FINAL_PHRASE}")

    ready = bool(
        staging_only
        and forward_exists
        and rollback_contract
        and lock_available
        and (disconnect_enabled or revert_enabled)
        and not production_target
        and not kill_switch
        and phrase_present
        and not blockers
    )

    if ready:
        messages.append("Rollback readiness gate passed (no rollback executed).")

    return RailwayRollbackReadiness(
        ready_for_live_rollback=ready,
        staging_only=staging_only,
        live_forward_execution_exists=forward_exists,
        rollback_contract_present=rollback_contract,
        rollback_lock_available=lock_available,
        disconnect_source_enabled=disconnect_enabled,
        revert_env_enabled=revert_enabled,
        production_target=production_target,
        rollback_phrase_present=phrase_present,
        kill_switch_active=kill_switch,
        phases_available=tuple(phases_available),
        phases_simulated_only=tuple(phases_simulated),
        blockers=blockers,
        messages=messages,
    )

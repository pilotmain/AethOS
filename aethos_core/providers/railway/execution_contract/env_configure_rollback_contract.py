# SPDX-License-Identifier: Apache-2.0
"""FIX 112 — configure_env rollback contract (plan before any live write)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    CONFIGURE_ENV_ROLLBACK_ACTION,
    CONFIGURE_ENV_ROLLBACK_STEPS,
    resolve_env_configure_groups,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    forward_live_connect_source_mutation_recorded,
    phase_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
)
from aethos_core.providers.railway.execution_contract.source_binding_status import (
    assess_railway_source_binding_status,
)
from aethos_core.providers.railway.env_value_readiness.env_rotation_metadata import (
    load_rotation_metadata,
)
from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
    build_target_key_for_plan,
)


@dataclass(frozen=True)
class EnvConfigureRollbackContract:
    execution_id: str
    rollback_action: str
    rollback_plan_ready: bool
    ready_for_env_writes: bool
    forward_create_service_recorded: bool
    forward_connect_source_live_recorded: bool
    groups: tuple[tuple[str, tuple[str, ...]], ...] = ()
    steps: tuple[str, ...] = CONFIGURE_ENV_ROLLBACK_STEPS
    blockers: list[str] = field(default_factory=list)
    blocker_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "rollback_action": self.rollback_action,
            "rollback_plan_ready": self.rollback_plan_ready,
            "ready_for_env_writes": self.ready_for_env_writes,
            "forward_create_service_recorded": self.forward_create_service_recorded,
            "forward_connect_source_live_recorded": self.forward_connect_source_live_recorded,
            "groups": [{"group_id": g, "env_names": list(names)} for g, names in self.groups],
            "steps": list(self.steps),
            "blockers": list(self.blockers),
            "blocker_messages": list(self.blocker_messages),
        }


def env_group_version_fingerprint(
    *,
    target_key: str,
    env_names: tuple[str, ...],
) -> str:
    """Idempotency metadata from rotation hints — no secret values."""
    hints = load_rotation_metadata(target_key)
    parts: list[str] = []
    for name in env_names:
        upper = name.upper()
        row = hints.get(upper) or hints.get(name) or {}
        parts.append(
            f"{upper}:{row.get('rotation_state', 'unknown')}:{row.get('last_updated_days', '')}"
        )
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def build_env_configure_rollback_contract(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
) -> EnvConfigureRollbackContract:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")

    create_receipt = (
        find_phase_receipt(execution_id=execution_id, phase="create_service") if execution_id else None
    )
    connect_receipt = (
        find_phase_receipt(execution_id=execution_id, phase="connect_source") if execution_id else None
    )
    create_recorded = bool(journal.get("railway_service_id")) or phase_mutation_recorded(create_receipt)
    connect_live = forward_live_connect_source_mutation_recorded(connect_receipt)

    binding_status = assess_railway_source_binding_status(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )

    blockers: list[str] = []
    messages: list[str] = []
    if not execution_id:
        blockers.append("execution_id_missing")
        messages.append("No execution_id — enroll execution journal first.")
    if not create_recorded:
        blockers.append("create_service_required")
        messages.append("Live create_service must complete before env writes.")
    if not connect_live:
        blockers.append("connect_source_live_required")
        messages.append("Live connect_source mutation receipt required before env writes.")
    if not binding_status.ready_for_env_writes:
        blockers.append("source_binding_not_verified")
        messages.append("Source binding verification must pass before env writes.")
    if not journal.get("rollback_journal"):
        blockers.append("rollback_journal_missing")
        messages.append("Rollback journal must exist before configure_env.")

    rollback_plan_ready = bool(
        execution_id
        and create_recorded
        and connect_live
        and binding_status.ready_for_env_writes
        and journal.get("rollback_journal")
        and not blockers
    )

    if rollback_plan_ready:
        messages.append(
            f"Rollback plan ready: `{CONFIGURE_ENV_ROLLBACK_ACTION}` documented before env writes."
        )

    return EnvConfigureRollbackContract(
        execution_id=execution_id,
        rollback_action=CONFIGURE_ENV_ROLLBACK_ACTION,
        rollback_plan_ready=rollback_plan_ready,
        ready_for_env_writes=binding_status.ready_for_env_writes,
        forward_create_service_recorded=create_recorded,
        forward_connect_source_live_recorded=connect_live,
        groups=resolve_env_configure_groups(plan),
        blockers=blockers,
        blocker_messages=messages,
    )


def group_version_fingerprint_for_plan(
    *,
    plan: dict[str, Any],
    group_id: str,
    env_names: tuple[str, ...],
) -> str:
    _ = group_id
    return env_group_version_fingerprint(
        target_key=build_target_key_for_plan(plan),
        env_names=env_names,
    )

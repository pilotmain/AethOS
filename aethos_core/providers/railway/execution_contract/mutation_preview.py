# SPDX-License-Identifier: Apache-2.0
"""Read-only preview of what a governed live create_service mutation would do."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    phase_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
)
from aethos_core.providers.railway.greenfield_adapters.greenfield_mutation_scope import (
    STAGING_ONLY_ENVIRONMENTS,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
    is_railway_mutation_kill_switch_active,
)
from aethos_core.providers.railway.greenfield_adapters.target_resolution import (
    resolve_railway_create_targets,
    service_name_exists_in_project,
)


@dataclass(frozen=True)
class RailwayMutationPreview:
    would_mutate: bool
    operation: str
    project_name: str
    environment_name: str
    service_name: str
    resolved_project_id: str = ""
    resolved_environment_id: str = ""
    service_already_exists: bool = False
    idempotent_replay: bool = False
    kill_switch_active: bool = False
    execution_mode: str = "disabled"
    policy: RailwayExecutionEnablementPolicy | None = None
    blockers: list[str] = field(default_factory=list)
    blocker_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "would_mutate": self.would_mutate,
            "operation": self.operation,
            "project_name": self.project_name,
            "environment_name": self.environment_name,
            "service_name": self.service_name,
            "resolved_project_id": self.resolved_project_id,
            "resolved_environment_id": self.resolved_environment_id,
            "service_already_exists": self.service_already_exists,
            "idempotent_replay": self.idempotent_replay,
            "kill_switch_active": self.kill_switch_active,
            "execution_mode": self.execution_mode,
            "blockers": list(self.blockers),
            "blocker_messages": list(self.blocker_messages),
        }


def _create_service_complete(journal: dict[str, Any], *, execution_id: str) -> bool:
    if str(journal.get("railway_service_id") or "").strip():
        return True
    if execution_id:
        receipt = find_phase_receipt(execution_id=execution_id, phase="create_service")
        return phase_mutation_recorded(receipt)
    return False


def assess_railway_mutation_preview(
    *,
    plan: dict[str, Any] | None,
    user_text: str = "",
    execution_id: str = "",
    journal: dict[str, Any] | None = None,
) -> RailwayMutationPreview:
    """Describe the next single live mutation phase that would run (read-only)."""
    plan = plan or {}
    journal = journal or {}
    project_name = str(plan.get("project") or "")
    environment_name = str(plan.get("environment") or "")
    service_name = str(plan.get("service_name") or plan.get("service") or "")
    repo = str(plan.get("repo") or "")
    branch = str(plan.get("branch") or "main")
    policy = assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    kill_switch = is_railway_mutation_kill_switch_active()
    blockers: list[str] = []
    messages: list[str] = []

    env_norm = environment_name.strip().lower()
    if env_norm and env_norm not in STAGING_ONLY_ENVIRONMENTS:
        blockers.append("environment_not_staging")
        messages.append(
            "Live greenfield mutations are limited to staging environments "
            f"({', '.join(sorted(STAGING_ONLY_ENVIRONMENTS))})."
        )

    if kill_switch:
        blockers.append("mutation_kill_switch_active")
        messages.append("Emergency mutation kill switch is active.")

    next_phase = "create_service"
    if _create_service_complete(journal, execution_id=execution_id):
        next_phase = "connect_source"

    if next_phase == "create_service":
        if not policy.allows_real_mutation():
            blockers.append("policy_blocks_live_mutation")
            messages.extend(policy.blocking_reason_messages)
    else:
        if not policy.allows_connect_source_mutation():
            blockers.append("connect_source_disabled")
            messages.append(
                "connect_source requires RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED=true "
                "and full execution enablement."
            )
            if not policy.allows_real_mutation():
                messages.extend(policy.blocking_reason_messages)

    create_receipt = (
        find_phase_receipt(execution_id=execution_id, phase="create_service") if execution_id else None
    )
    connect_receipt = (
        find_phase_receipt(execution_id=execution_id, phase="connect_source") if execution_id else None
    )
    journal_service_id = str(journal.get("railway_service_id") or "")
    idempotent_replay = False
    service_exists = False
    resolved_project_id = str(journal.get("railway_project_id") or "")
    resolved_environment_id = str(journal.get("railway_environment_id") or "")

    if next_phase == "create_service":
        idempotent_replay = bool(journal_service_id) or phase_mutation_recorded(create_receipt)
        if project_name and environment_name and not resolved_environment_id:
            targets = resolve_railway_create_targets(
                project_name=project_name,
                environment_name=environment_name,
            )
            if targets.ok:
                resolved_project_id = targets.project_id
                resolved_environment_id = targets.environment_id
                if service_name:
                    service_exists = service_name_exists_in_project(
                        project_id=targets.project_id,
                        service_name=service_name,
                    )
            elif not idempotent_replay:
                blockers.append("target_resolution_failed")
                messages.extend(targets.errors)
        if service_exists:
            idempotent_replay = True
        if idempotent_replay:
            blockers.append("idempotent_replay")
            messages.append("create_service would be skipped (idempotent replay).")
        operation = "railway.serviceCreate (empty service only)"
        policy_ok = policy.allows_real_mutation()
    else:
        idempotent_replay = bool(journal.get("github_source_bound")) or phase_mutation_recorded(
            connect_receipt
        )
        if not journal_service_id:
            blockers.append("create_service_required")
            messages.append("create_service must complete before connect_source.")
        if not repo:
            blockers.append("plan_repo_missing")
            messages.append("Deployment plan is missing GitHub repository.")
        if idempotent_replay:
            blockers.append("idempotent_replay")
            messages.append("connect_source would be skipped (idempotent replay).")
        operation = f"railway.connect_source ({repo}@{branch}, skipDeploys=true)"
        policy_ok = policy.allows_connect_source_mutation()

    would_mutate = (
        not kill_switch
        and policy.mode == "enabled"
        and policy_ok
        and env_norm in STAGING_ONLY_ENVIRONMENTS
        and not idempotent_replay
        and (next_phase != "create_service" or not service_exists)
        and bool(project_name and environment_name)
        and (next_phase != "create_service" or bool(service_name))
        and (next_phase != "connect_source" or bool(repo and journal_service_id))
        and "target_resolution_failed" not in blockers
        and "create_service_required" not in blockers
        and "plan_repo_missing" not in blockers
    )

    return RailwayMutationPreview(
        would_mutate=would_mutate,
        operation=operation,
        project_name=project_name,
        environment_name=environment_name,
        service_name=service_name,
        resolved_project_id=resolved_project_id,
        resolved_environment_id=resolved_environment_id,
        service_already_exists=service_exists,
        idempotent_replay=idempotent_replay,
        kill_switch_active=kill_switch,
        execution_mode=policy.mode,
        policy=policy,
        blockers=blockers,
        blocker_messages=messages,
    )

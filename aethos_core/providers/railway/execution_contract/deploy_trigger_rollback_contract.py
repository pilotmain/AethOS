# SPDX-License-Identifier: Apache-2.0
"""FIX 113 — deploy trigger rollback contract (journal before trigger)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
    assess_deploy_trigger_readiness,
)


DEPLOY_TRIGGER_ROLLBACK_ACTION: str = "disable_deploys"

DEPLOY_TRIGGER_ROLLBACK_STEPS: tuple[str, ...] = (
    "verify_deploy_trigger_readiness",
    "record_disable_deploys_rollback_plan",
    "trigger_service_instance_redeploy",
    "record_trigger_deploy_receipt",
    "capture_deployment_metadata",
)


@dataclass(frozen=True)
class DeployTriggerRollbackContract:
    execution_id: str
    rollback_action: str
    rollback_plan_ready: bool
    ready_for_deploy_trigger: bool
    deploy_trigger_enabled: bool
    rollback_journal_present: bool
    steps: tuple[str, ...] = DEPLOY_TRIGGER_ROLLBACK_STEPS
    blockers: list[str] = field(default_factory=list)
    blocker_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "rollback_action": self.rollback_action,
            "rollback_plan_ready": self.rollback_plan_ready,
            "ready_for_deploy_trigger": self.ready_for_deploy_trigger,
            "deploy_trigger_enabled": self.deploy_trigger_enabled,
            "rollback_journal_present": self.rollback_journal_present,
            "steps": list(self.steps),
            "blockers": list(self.blockers),
            "blocker_messages": list(self.blocker_messages),
        }


def build_deploy_trigger_rollback_contract(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
    user_text: str = "",
) -> DeployTriggerRollbackContract:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")
    readiness = assess_deploy_trigger_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )

    rollback_journal_present = bool(journal.get("rollback_journal"))
    blockers = list(readiness.blockers)
    messages = list(readiness.messages)

    if not rollback_journal_present:
        blockers.append("rollback_journal_missing")
        messages.append("Rollback journal must exist before deploy trigger.")

    rollback_plan_ready = bool(
        rollback_journal_present
        and readiness.create_service_live_success
        and readiness.connect_source_live_success
        and readiness.configure_env_live_success
        and readiness.env_names_verified
        and readiness.staging_only
        and readiness.final_phrase_present
        and readiness.rollback_contract_visible
        and "rollback_journal_missing" not in blockers
    )

    if rollback_plan_ready and readiness.deploy_trigger_enabled:
        messages.append(
            f"Rollback plan ready: `{DEPLOY_TRIGGER_ROLLBACK_ACTION}` documented before deploy trigger."
        )

    return DeployTriggerRollbackContract(
        execution_id=execution_id,
        rollback_action=DEPLOY_TRIGGER_ROLLBACK_ACTION,
        rollback_plan_ready=rollback_plan_ready,
        ready_for_deploy_trigger=readiness.ready_for_deploy_trigger,
        deploy_trigger_enabled=readiness.deploy_trigger_enabled,
        rollback_journal_present=rollback_journal_present,
        blockers=blockers,
        blocker_messages=messages,
    )

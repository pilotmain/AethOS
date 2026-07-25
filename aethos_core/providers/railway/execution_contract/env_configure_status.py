# SPDX-License-Identifier: Apache-2.0
"""FIX 112B — configure_env status, verification, deploy-trigger readiness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
    DeployTriggerReadiness,
    assess_deploy_trigger_readiness,
)
from aethos_core.providers.railway.execution_contract.env_configure_rollback_contract import (
    build_env_configure_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.env_configure_verification import (
    EnvConfigureVerification,
    verify_env_configure_readonly,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    list_execution_receipts,
)
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    COMMIT_SKIP_DEPLOYS_ENFORCED,
)


@dataclass(frozen=True)
class RailwayEnvConfigureStatus:
    execution_id: str
    configure_env_enabled: bool
    rollback_plan_ready: bool
    rollback_contract_visible: bool
    ready_for_env_writes: bool
    env_names_verified: bool
    ready_for_deploy_trigger: bool
    groups_recorded: int
    group_receipt_count: int
    skip_deploys_enforced: bool
    readonly_verification: EnvConfigureVerification | None = None
    deploy_trigger_readiness: DeployTriggerReadiness | None = None
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "configure_env_enabled": self.configure_env_enabled,
            "rollback_plan_ready": self.rollback_plan_ready,
            "rollback_contract_visible": self.rollback_contract_visible,
            "ready_for_env_writes": self.ready_for_env_writes,
            "env_names_verified": self.env_names_verified,
            "ready_for_deploy_trigger": self.ready_for_deploy_trigger,
            "groups_recorded": self.groups_recorded,
            "group_receipt_count": self.group_receipt_count,
            "skip_deploys_enforced": self.skip_deploys_enforced,
            "readonly_verification": (
                self.readonly_verification.to_dict() if self.readonly_verification else None
            ),
            "deploy_trigger_readiness": (
                self.deploy_trigger_readiness.to_dict() if self.deploy_trigger_readiness else None
            ),
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def assess_railway_env_configure_status(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
    user_text: str = "",
) -> RailwayEnvConfigureStatus:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")
    contract = build_env_configure_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )
    enabled = bool(getattr(get_settings(), "railway_greenfield_configure_env_enabled", False))

    receipts = list_execution_receipts(execution_id=execution_id) if execution_id else []
    group_receipts = [
        r
        for r in receipts
        if str(r.get("phase") or "") == "configure_env" and str(r.get("receipt_group") or "")
    ]

    groups_state = journal.get("env_configure_groups") if isinstance(journal.get("env_configure_groups"), dict) else {}
    recorded = sum(1 for row in groups_state.values() if isinstance(row, dict) and row.get("recorded"))

    rollback_visible = bool(journal.get("env_configure_rollback_plan") or journal.get("rollback_journal"))

    verification: EnvConfigureVerification | None = None
    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    journal_names: list[str] = []
    configured = journal.get("env_vars_configured")
    if isinstance(configured, dict):
        for group in configured.get("groups", {}).values():
            if isinstance(group, dict):
                journal_names.extend(str(n) for n in group.get("env_names") or [])

    cached = journal.get("env_configure_verification")
    if isinstance(cached, dict) and cached.get("names_observed") is not None:
        verification = EnvConfigureVerification(
            ok=bool(cached.get("ok")),
            verified=bool(cached.get("verified")),
            minimum_secret_names_required=tuple(cached.get("minimum_secret_names_required") or []),
            names_observed=tuple(cached.get("names_observed") or []),
            missing_names=tuple(cached.get("missing_names") or []),
            minimum_secrets_present=bool(cached.get("minimum_secrets_present")),
            detail=str(cached.get("detail") or ""),
            errors=list(cached.get("errors") or []),
        )
    elif service_id and environment_id:
        verification = verify_env_configure_readonly(
            environment_id=environment_id,
            service_id=service_id,
            journal_env_names=journal_names,
        )

    deploy_readiness = assess_deploy_trigger_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )

    blockers = list(contract.blockers)
    messages = list(contract.blocker_messages)
    if not enabled:
        blockers.append("configure_env_disabled")
        messages.append("railway_greenfield_configure_env_enabled=false (default).")
    if verification and not verification.verified:
        blockers.append("env_names_not_verified")
        messages.append(verification.detail)

    return RailwayEnvConfigureStatus(
        execution_id=execution_id,
        configure_env_enabled=enabled,
        rollback_plan_ready=contract.rollback_plan_ready,
        rollback_contract_visible=rollback_visible,
        ready_for_env_writes=contract.ready_for_env_writes,
        env_names_verified=bool(verification and verification.verified),
        ready_for_deploy_trigger=deploy_readiness.ready_for_deploy_trigger,
        groups_recorded=recorded,
        group_receipt_count=len(group_receipts),
        skip_deploys_enforced=COMMIT_SKIP_DEPLOYS_ENFORCED,
        readonly_verification=verification,
        deploy_trigger_readiness=deploy_readiness,
        blockers=blockers,
        messages=messages,
    )

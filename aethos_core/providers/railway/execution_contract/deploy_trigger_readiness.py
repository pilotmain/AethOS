# SPDX-License-Identifier: Apache-2.0
"""FIX 112B / FIX 113 gate — deploy trigger readiness (names only, no deploy)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    resolve_env_configure_groups,
)
from aethos_core.providers.railway.execution_contract.env_configure_rollback_contract import (
    build_env_configure_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.env_configure_verification import (
    EnvConfigureVerification,
    verify_env_configure_readonly,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
    is_production_environment,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    forward_live_configure_env_group_recorded,
    forward_live_connect_source_mutation_recorded,
    forward_live_create_service_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_group_receipt,
    find_phase_receipt,
)
from aethos_core.providers.railway.greenfield_adapters.greenfield_mutation_scope import (
    STAGING_ONLY_ENVIRONMENTS,
)


@dataclass(frozen=True)
class DeployTriggerReadiness:
    execution_id: str
    ready_for_deploy_trigger: bool
    deploy_trigger_enabled: bool
    create_service_live_success: bool
    connect_source_live_success: bool
    configure_env_live_success: bool
    env_names_verified: bool
    staging_only: bool
    final_phrase_present: bool
    rollback_contract_visible: bool
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    env_verification: EnvConfigureVerification | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "ready_for_deploy_trigger": self.ready_for_deploy_trigger,
            "deploy_trigger_enabled": self.deploy_trigger_enabled,
            "create_service_live_success": self.create_service_live_success,
            "connect_source_live_success": self.connect_source_live_success,
            "configure_env_live_success": self.configure_env_live_success,
            "env_names_verified": self.env_names_verified,
            "staging_only": self.staging_only,
            "final_phrase_present": self.final_phrase_present,
            "rollback_contract_visible": self.rollback_contract_visible,
            "blockers": list(self.blockers),
            "messages": list(self.messages),
            "env_verification": self.env_verification.to_dict() if self.env_verification else None,
        }


def assess_deploy_trigger_readiness(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
    user_text: str = "",
) -> DeployTriggerReadiness:
    """
    FIX 113 prerequisites assessment (no deploy performed here).

    Deploy may trigger only when this returns ready_for_deploy_trigger=true.
    """
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")

    create_receipt = (
        find_phase_receipt(execution_id=execution_id, phase="create_service") if execution_id else None
    )
    connect_receipt = (
        find_phase_receipt(execution_id=execution_id, phase="connect_source") if execution_id else None
    )

    create_live = forward_live_create_service_mutation_recorded(create_receipt)
    if not create_live and str(journal.get("railway_service_id") or "").strip():
        create_live = True

    connect_live = forward_live_connect_source_mutation_recorded(connect_receipt)
    bound = journal.get("github_source_bound")
    if not connect_live and isinstance(bound, dict) and str(bound.get("repository") or "").strip():
        connect_live = True

    configure_live = True
    groups_state = journal.get("env_configure_groups")
    for group_id, _names in resolve_env_configure_groups(plan):
        group_receipt = (
            find_phase_group_receipt(
                execution_id=execution_id,
                phase="configure_env",
                receipt_group=group_id,
            )
            if execution_id
            else None
        )
        if forward_live_configure_env_group_recorded(group_receipt):
            continue
        if isinstance(groups_state, dict):
            row = groups_state.get(group_id)
            if isinstance(row, dict) and row.get("recorded") and row.get("mutation_performed"):
                continue
        configure_live = False
        break

    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")

    journal_names: list[str] = []
    env_configured = journal.get("env_vars_configured")
    if isinstance(env_configured, dict):
        for group in env_configured.get("groups", {}).values():
            if isinstance(group, dict):
                journal_names.extend(str(n) for n in group.get("env_names") or [])

    verification: EnvConfigureVerification | None = None
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
            plan=plan,
        )

    env_verified = bool(verification and verification.verified)

    environment = str(plan.get("environment") or "")
    env_norm = environment.strip().lower()
    staging_only = env_norm in STAGING_ONLY_ENVIRONMENTS and not is_production_environment(environment)

    policy = assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    final_phrase = NON_PRODUCTION_FINAL_PHRASE.lower() in (user_text or "").lower()
    if not bool(getattr(get_settings(), "railway_greenfield_require_final_phrase", True)):
        final_phrase = True

    deploy_enabled = bool(getattr(get_settings(), "railway_greenfield_trigger_deploy_enabled", False))

    rollback_contract = build_env_configure_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )
    rollback_visible = bool(
        journal.get("env_configure_rollback_plan")
        or journal.get("rollback_journal")
    )

    blockers: list[str] = []
    messages: list[str] = []
    if not create_live:
        blockers.append("create_service_live_required")
        messages.append("Live create_service mutation_success required.")
    if not connect_live:
        blockers.append("connect_source_live_required")
        messages.append("Live connect_source mutation_success required.")
    if not configure_live:
        blockers.append("configure_env_live_required")
        messages.append("Live configure_env group receipts required.")
    if not env_verified:
        blockers.append("env_names_not_verified")
        messages.append("Read-only env name verification must confirm minimum secrets.")
    if not staging_only:
        blockers.append("staging_only")
        messages.append("Deploy trigger is limited to staging environments in FIX 113.")
    if not final_phrase:
        blockers.append("final_phrase_required")
        messages.append("Governed final approval phrase required before deploy trigger.")
    if not deploy_enabled:
        blockers.append("deploy_trigger_disabled")
        messages.append("railway_greenfield_trigger_deploy_enabled=false (FIX 113).")
    if not rollback_visible:
        blockers.append("rollback_contract_not_visible")
        messages.append("Env configure rollback contract must be visible on journal.")

    ready = bool(
        execution_id
        and create_live
        and connect_live
        and configure_live
        and env_verified
        and staging_only
        and final_phrase
        and deploy_enabled
        and rollback_visible
        and not blockers
    )

    if ready:
        messages.append("All FIX 113 prerequisites satisfied — deploy trigger may run when enabled.")

    return DeployTriggerReadiness(
        execution_id=execution_id,
        ready_for_deploy_trigger=ready,
        deploy_trigger_enabled=deploy_enabled,
        create_service_live_success=create_live,
        connect_source_live_success=connect_live,
        configure_env_live_success=configure_live,
        env_names_verified=env_verified,
        staging_only=staging_only,
        final_phrase_present=final_phrase,
        rollback_contract_visible=rollback_visible,
        blockers=blockers,
        messages=messages,
        env_verification=verification,
    )

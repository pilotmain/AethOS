# SPDX-License-Identifier: Apache-2.0
"""FIX 114 — readiness gate for readonly runtime verification after deploy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
    assess_deploy_trigger_readiness,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    forward_live_trigger_deploy_recorded,
    phase_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
)


@dataclass(frozen=True)
class RuntimeVerificationReadiness:
    execution_id: str
    ready_for_runtime_verification: bool
    verify_runtime_enabled: bool
    trigger_deploy_live_success: bool
    deployment_id_present: bool
    env_names_verified: bool
    deploy_prerequisites_met: bool
    final_phrase_present: bool
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "ready_for_runtime_verification": self.ready_for_runtime_verification,
            "verify_runtime_enabled": self.verify_runtime_enabled,
            "trigger_deploy_live_success": self.trigger_deploy_live_success,
            "deployment_id_present": self.deployment_id_present,
            "env_names_verified": self.env_names_verified,
            "deploy_prerequisites_met": self.deploy_prerequisites_met,
            "final_phrase_present": self.final_phrase_present,
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def assess_runtime_verification_readiness(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
    user_text: str = "",
) -> RuntimeVerificationReadiness:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")

    deploy_readiness = assess_deploy_trigger_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )

    trigger_receipt = (
        find_phase_receipt(execution_id=execution_id, phase="trigger_deploy") if execution_id else None
    )
    trigger_live = forward_live_trigger_deploy_recorded(trigger_receipt) or phase_mutation_recorded(
        trigger_receipt
    )
    deployment_id = str(journal.get("railway_deployment_id") or "")
    if not deployment_id and isinstance(journal.get("deploy_trigger_metadata"), dict):
        deployment_id = str(journal["deploy_trigger_metadata"].get("deployment_id") or "")

    env_verified = bool(
        journal.get("env_configure_verification", {}).get("verified")
        if isinstance(journal.get("env_configure_verification"), dict)
        else False
    )
    if deploy_readiness.env_verification:
        env_verified = env_verified or deploy_readiness.env_verification.verified

    verify_enabled = bool(getattr(get_settings(), "railway_greenfield_verify_runtime_enabled", False))

    final_phrase = NON_PRODUCTION_FINAL_PHRASE.lower() in (user_text or "").lower()
    if not bool(getattr(get_settings(), "railway_greenfield_require_final_phrase", True)):
        final_phrase = True

    deploy_prereq = bool(
        deploy_readiness.create_service_live_success
        and deploy_readiness.connect_source_live_success
        and deploy_readiness.configure_env_live_success
        and deploy_readiness.env_names_verified
        and deploy_readiness.staging_only
        and deploy_readiness.rollback_contract_visible
    )

    blockers: list[str] = []
    messages: list[str] = []
    if not execution_id:
        blockers.append("execution_id_missing")
    if not deploy_prereq:
        blockers.append("deploy_pipeline_incomplete")
        messages.append("Prior live phases (create/connect/configure/env verify) must be complete.")
    if not trigger_live:
        blockers.append("trigger_deploy_live_required")
        messages.append("Live trigger_deploy receipt required before runtime verification.")
    if not deployment_id:
        blockers.append("deployment_id_missing")
        messages.append("railway_deployment_id must be present on journal from FIX 113.")
    if not env_verified:
        blockers.append("env_names_not_verified")
    if not final_phrase:
        blockers.append("final_phrase_required")
    if not verify_enabled:
        blockers.append("verify_runtime_disabled")
        messages.append("railway_greenfield_verify_runtime_enabled=false (FIX 114).")

    ready = bool(
        execution_id
        and deploy_prereq
        and trigger_live
        and deployment_id
        and env_verified
        and final_phrase
        and verify_enabled
        and not blockers
    )

    if ready:
        messages.append("Runtime verification may run (read-only; no deploy re-trigger).")

    return RuntimeVerificationReadiness(
        execution_id=execution_id,
        ready_for_runtime_verification=ready,
        verify_runtime_enabled=verify_enabled,
        trigger_deploy_live_success=trigger_live,
        deployment_id_present=bool(deployment_id),
        env_names_verified=env_verified,
        deploy_prerequisites_met=deploy_prereq,
        final_phrase_present=final_phrase,
        blockers=blockers,
        messages=messages,
    )

# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — production shadow rehearsal gates (policy-complete, no live mutations)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_enablement import (
    PRODUCTION_FINAL_PHRASE,
    is_production_environment,
    plan_has_execution_target,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    PRODUCTION_QUORUM_CONFIRMATION_PHRASE,
    assess_railway_production_policy,
    is_production_shadow_execution_enabled,
)

# Expected production policy outcomes during shadow — not rehearsal blockers.
_SHADOW_NON_BLOCKING_POLICY_CODES = frozenset(
    {
        "production_forward_live_locked",
        "production_shadow_mode_required",
        "production_autonomous_rollback_blocked",
        "production_slo_verification_required",
    }
)


@dataclass(frozen=True)
class ProductionShadowGateResult:
    ready: bool
    shadow_execution_enabled: bool
    production_target: bool
    policy_assessment: Any
    forward_live_permitted: bool
    operator_quorum_satisfied: bool
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "shadow_execution_enabled": self.shadow_execution_enabled,
            "production_target": self.production_target,
            "forward_live_permitted": self.forward_live_permitted,
            "operator_quorum_satisfied": self.operator_quorum_satisfied,
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def assess_production_shadow_gate(
    *,
    plan: dict[str, Any] | None,
    user_text: str = "",
    execution_id: str = "",
    journal: dict[str, Any] | None = None,
    require_quorum: bool = True,
) -> ProductionShadowGateResult:
    plan = plan or {}
    blockers: list[str] = []
    messages: list[str] = []

    if not is_production_shadow_execution_enabled():
        blockers.append("production_shadow_execution_disabled")
        messages.append(
            "Production shadow rehearsal is disabled. Set RAILWAY_PRODUCTION_SHADOW_EXECUTION=true."
        )

    if not plan_has_execution_target(plan):
        blockers.append("no_production_plan_loaded")
        messages.append(
            "Load a production deployment plan first, e.g. "
            "`create railway deployment plan for org/repo in pilotos / production`."
        )

    environment = str(plan.get("environment") or "")
    production_target = is_production_environment(environment)
    if not production_target:
        blockers.append("not_production_target")
        messages.append("Production shadow rehearsal requires a production environment target.")

    policy = assess_railway_production_policy(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
        journal=journal,
    )

    if policy.incident_mode_active:
        blockers.append("production_incident_mode_active")
    if policy.deployment_freeze_active:
        blockers.append("production_deployment_freeze_active")
    for code in policy.blockers:
        if code in _SHADOW_NON_BLOCKING_POLICY_CODES:
            continue
        if code not in blockers:
            blockers.append(code)
    for msg in policy.messages:
        if msg not in messages:
            messages.append(msg)

    if require_quorum and production_target and not policy.operator_quorum_satisfied:
        blockers.append("production_operator_quorum_unsatisfied")
        messages.append(
            "Record production final phrase and quorum confirmation on this execution "
            f"before shadow rehearsal. Quorum phrase: {PRODUCTION_QUORUM_CONFIRMATION_PHRASE}"
        )

    if PRODUCTION_FINAL_PHRASE not in (user_text or "") and require_quorum:
        if "production_final_phrase_missing" not in blockers:
            blockers.append("production_final_phrase_missing")
            messages.append(f"Shadow forward requires exact phrase: {PRODUCTION_FINAL_PHRASE}")

    if policy.forward_live_permitted:
        blockers.append("production_forward_live_must_remain_locked")
        messages.append("Production forward live must stay locked during shadow rehearsal.")

    ready = not blockers
    return ProductionShadowGateResult(
        ready=ready,
        shadow_execution_enabled=is_production_shadow_execution_enabled(),
        production_target=production_target,
        policy_assessment=policy,
        forward_live_permitted=policy.forward_live_permitted,
        operator_quorum_satisfied=policy.operator_quorum_satisfied,
        blockers=blockers,
        messages=messages,
    )


def assess_production_shadow_rollback_gate(
    *,
    plan: dict[str, Any] | None,
    user_text: str = "",
    execution_id: str = "",
    journal: dict[str, Any] | None = None,
) -> ProductionShadowGateResult:
    """Rollback shadow rehearsal — policy + forward shadow completion; never live rollback."""
    gate = assess_production_shadow_gate(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
        journal=journal,
        require_quorum=False,
    )
    blockers = list(gate.blockers)
    messages = list(gate.messages)

    shadow_journal = journal or {}
    if not shadow_journal.get("forward_shadow_completed"):
        blockers.append("forward_shadow_not_completed")
        messages.append("Run `simulate production railway deployment` before rollback shadow.")

    if gate.policy_assessment.rollback_permitted:
        blockers.append("production_rollback_must_remain_blocked")
        messages.append("Production rollback must remain blocked; shadow simulates escalation only.")

    if gate.policy_assessment.autonomous_rollback_blocked is False:
        blockers.append("autonomous_rollback_must_stay_blocked")

    ready = not blockers
    return ProductionShadowGateResult(
        ready=ready,
        shadow_execution_enabled=gate.shadow_execution_enabled,
        production_target=gate.production_target,
        policy_assessment=gate.policy_assessment,
        forward_live_permitted=gate.forward_live_permitted,
        operator_quorum_satisfied=gate.operator_quorum_satisfied,
        blockers=blockers,
        messages=messages,
    )

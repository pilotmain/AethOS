# SPDX-License-Identifier: Apache-2.0
"""Authoritative Railway greenfield execution readiness gate (no live mutations)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from aethos_core.providers.railway.deployment_plan.deployment_plan_lifecycle import (
    classify_deployment_plan_lifecycle_state,
)
from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate
from aethos_core.providers.railway.deployment_plan.plan_review import is_plan_review_confirmed
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    load_execution_lock,
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.execution_idempotency import derive_idempotency_key
from aethos_core.providers.railway.execution_contract.execution_journal import (
    load_journal_by_id,
    load_journal_by_idempotency_key,
)
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    lifecycle_state_for_approvals,
)

GateCheckStatus = Literal["pass", "fail", "unknown"]

_READINESS_GATE_RX = re.compile(
    r"\b(?:check|show)\s+railway\s+execution\s+(?:readiness|gate)\b"
    r"|\bis\s+railway\s+service\s+creation\s+ready\s+to\s+execute\??"
    r"|\bwhy\s+can'?t\s+railway\s+execution\s+start\??",
    re.I,
)

_CHECK_LABELS: dict[str, str] = {
    "deployment_plan": "deployment plan",
    "mutation_ready": "mutation ready",
    "review_confirmed": "review confirmed",
    "preflight_exists": "preflight exists",
    "preflight_approved": "preflight approved",
    "simulation_exists": "simulation exists",
    "simulation_ready_to_execute": "simulation ready",
    "env_readiness": "env readiness",
    "critical_env_secrets_configured": "critical env secrets",
    "execution_contract_exists": "execution contract",
    "execution_lock_available": "execution lock available",
    "execution_enabled": "execution enabled",
    "execution_policy": "execution policy",
    "dry_run_allowed": "dry run allowed",
    "phase_execution_allowed": "phase execution allowed",
    "real_mutation_allowed": "real mutation allowed",
}

_DRY_RUN_ENROLLMENT_CHECKS: tuple[str, ...] = (
    "deployment_plan",
    "mutation_ready",
    "review_confirmed",
    "preflight_exists",
    "preflight_approved",
    "simulation_exists",
    "simulation_ready_to_execute",
    "env_readiness",
    "critical_env_secrets_configured",
    "execution_lock_available",
    "execution_policy",
)


@dataclass(frozen=True)
class RailwayExecutionReadinessGate:
    ready: bool
    execution_enabled: bool
    checks: dict[str, GateCheckStatus]
    blocking_reasons: list[str]
    blocking_reason_messages: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    contract_blockers: list[str] = field(default_factory=list)
    lifecycle_state: str = "draft"
    env_state: dict[str, Any] = field(default_factory=dict)
    execution_id: str = ""
    execution_mode: str = "disabled"
    dry_run_allowed: bool = False
    real_mutation_allowed: bool = False
    phase_execution_allowed: bool = False
    enablement: RailwayExecutionEnablementPolicy | None = None

    def blocking_count(self) -> int:
        return len(self.blocking_reasons)

    def enrollment_contract_blockers(self) -> list[str]:
        """Blockers that prevent execute / dry-run enrollment."""
        if self.phase_execution_allowed:
            return list(self.contract_blockers)
        return list(self.contract_blockers)

    def can_enroll_execution(self) -> bool:
        if self.phase_execution_allowed and not self.enrollment_contract_blockers():
            return True
        if self.real_mutation_allowed and self.ready:
            return True
        return False

    def to_assessment_dict(self) -> dict[str, Any]:
        """Legacy assessment shape for execution_router renderers."""
        plan_pass = self.checks.get("deployment_plan") == "pass"
        review_pass = self.checks.get("review_confirmed") == "pass"
        preflight_exists = self.checks.get("preflight_exists") == "pass"
        preflight_approved = self.checks.get("preflight_approved") == "pass"
        simulation_exists = self.checks.get("simulation_exists") == "pass"
        simulation_ready = self.checks.get("simulation_ready_to_execute") == "pass"
        env_label = "ready"
        if self.checks.get("env_readiness") == "fail":
            env_label = "blocked"
        elif self.checks.get("env_readiness") == "unknown":
            env_label = "unknown"

        return {
            "review_confirmed": review_pass,
            "preflight_exists": preflight_exists,
            "preflight_approved": preflight_approved,
            "mutation_ready": self.checks.get("mutation_ready") == "pass",
            "simulation_complete": simulation_exists,
            "ready_to_execute": simulation_ready,
            "execution_enabled": self.execution_enabled,
            "execution_mode": self.execution_mode,
            "dry_run_allowed": self.dry_run_allowed,
            "real_mutation_allowed": self.real_mutation_allowed,
            "phase_execution_allowed": self.phase_execution_allowed,
            "execution_ready": self.ready,
            "env_readiness": env_label,
            "env_state": dict(self.env_state),
            "gate_matrix": self.display_gate_matrix(),
            "blocking_reasons": list(self.blocking_reason_messages),
            "next_steps": list(self.next_steps),
            "blockers": list(self.contract_blockers),
            "contract_blockers": list(self.enrollment_contract_blockers()),
            "lifecycle_state": self.lifecycle_state,
        }

    def display_gate_matrix(self) -> dict[str, str]:
        """Human display matrix for renderer."""
        plan_status = "ready" if self.checks.get("deployment_plan") == "pass" else "missing"
        if self.checks.get("deployment_plan") == "pass" and self.checks.get("mutation_ready") == "fail":
            plan_status = "incomplete"
        return {
            "deployment_plan": plan_status,
            "review_confirmed": "yes" if self.checks.get("review_confirmed") == "pass" else "no",
            "preflight_created": "yes" if self.checks.get("preflight_exists") == "pass" else "no",
            "preflight_approved": "yes" if self.checks.get("preflight_approved") == "pass" else "no",
            "simulation_complete": "yes" if self.checks.get("simulation_exists") == "pass" else "no",
            "simulation_ready_to_execute": "yes" if self.checks.get("simulation_ready_to_execute") == "pass" else "no",
            "env_readiness": (
                "ready"
                if self.checks.get("env_readiness") == "pass"
                else "blocked"
                if self.checks.get("env_readiness") == "fail"
                else "unknown"
            ),
            "execution_enabled": "yes" if self.execution_enabled else "no",
            "execution_mode": self.execution_mode,
            "dry_run_allowed": "yes" if self.dry_run_allowed else "no",
            "phase_execution_allowed": "yes" if self.phase_execution_allowed else "no",
            "real_mutation_allowed": "yes" if self.real_mutation_allowed else "no",
            "execution_policy": (
                "pass" if self.checks.get("execution_policy") == "pass" else "fail"
            ),
            "execution_lock_available": (
                "yes" if self.checks.get("execution_lock_available") == "pass" else "no"
            ),
            "execution_contract_exists": (
                "yes" if self.checks.get("execution_contract_exists") == "pass" else "no"
            ),
            "env_readiness_confidence": str(self.env_state.get("env_readiness_confidence") or "unknown"),
            "minimum_secret_set_complete": (
                "complete"
                if self.env_state.get("minimum_secret_set_complete")
                else "incomplete"
            ),
            "critical_env_secrets_detail": self._critical_env_secrets_label(),
        }

    def _critical_env_secrets_label(self) -> str:
        status = self.checks.get("critical_env_secrets_configured")
        if status == "pass":
            return "pass"
        configured = int(self.env_state.get("configured_securely_count") or 0)
        minimum = self.env_state.get("minimum_secret_set") or {}
        required = len(list(minimum.get("required") or []))
        if configured > 0 and required and configured < required:
            return "partial"
        return "fail" if status == "fail" else "unknown"


def is_railway_execution_readiness_gate_intent(text: str) -> bool:
    return bool(_READINESS_GATE_RX.search((text or "").strip()))


def _status(passed: bool, *, applicable: bool = True) -> GateCheckStatus:
    if not applicable:
        return "unknown"
    return "pass" if passed else "fail"


def _lock_available(*, plan: dict[str, Any], session_id: str, execution_id: str) -> bool:
    idempotency_key = derive_idempotency_key(plan=plan)
    lock = load_execution_lock(idempotency_key=idempotency_key)
    if not lock:
        return True
    from aethos_core.providers.railway.execution_contract.execution_context import _lock_is_stale

    if _lock_is_stale(lock):
        return True
    if execution_id and str(lock.get("execution_id")) == execution_id:
        return True
    if str(lock.get("owner_session_id") or "") == (session_id or "default").strip():
        return True
    return False


def _execution_contract_exists(*, plan: dict[str, Any], session_id: str) -> tuple[bool, str]:
    execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) or ""
    if execution_id and load_journal_by_id(execution_id):
        return True, execution_id
    journal = load_journal_by_idempotency_key(derive_idempotency_key(plan=plan))
    if journal:
        return True, str(journal.get("execution_id") or "")
    return False, execution_id


def evaluate_railway_execution_readiness(
    session_id: str,
    text: str | None = None,
    *,
    plan: dict[str, Any] | None = None,
    preflight: dict[str, Any] | None = None,
    simulation: dict[str, Any] | None = None,
) -> RailwayExecutionReadinessGate:
    """Single source of truth for Railway greenfield execution readiness."""
    session_id = (session_id or "default").strip()
    if plan is None and preflight is None and simulation is None:
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
            ensure_railway_deployment_lifecycle_for_lane,
        )

        lane = ensure_railway_deployment_lifecycle_for_lane(
            session_id=session_id,
            user_text=text or "",
            require_plan=False,
            require_preflight=False,
            require_simulation=False,
        )
        plan = lane.plan
        preflight = lane.preflight
        simulation = lane.simulation

    plan = plan or {}
    plan_state = classify_deployment_plan_lifecycle_state(plan if plan.get("repo") else None)
    plan_exists = plan_state != "no_plan"
    review_confirmed = bool(plan_exists and is_plan_review_confirmed(plan))
    mutation_gate = assess_mutation_readiness_gate(plan if plan_exists else {})
    mutation_ready = bool(mutation_gate.get("mutation_ready"))
    preflight_exists = bool(preflight and preflight.get("preflight_id"))
    preflight_approved = bool(preflight and preflight.get("preflight_approved"))
    simulation_exists = bool(simulation and simulation.get("simulation_id"))
    simulation_ready = bool(simulation and simulation.get("ready_to_execute"))

    env_state: dict[str, Any] = {}
    env_ready = False
    critical_secrets_ok = False
    if plan_exists:
        from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
            get_or_assess_env_value_readiness,
        )

        env_state = get_or_assess_env_value_readiness(plan=plan, session_id=session_id)
        mode = str(env_state.get("ready_mode") or "")
        critical_missing = list(
            env_state.get("critical_blockers")
            or env_state.get("critical_missing")
            or env_state.get("missing")
            or []
        )
        minimum_complete = bool(env_state.get("minimum_secret_set_complete"))
        env_execution_mode = str(env_state.get("execution_mode") or "disabled")
        if env_execution_mode == "dry_run":
            env_ready = bool(env_state.get("ready_for_dry_run")) or (
                minimum_complete and not critical_missing
            )
            critical_secrets_ok = minimum_complete
        else:
            env_ready = mode in {"ready", "pass_with_defaults"} and not critical_missing
            critical_secrets_ok = not critical_missing

    contract_exists, execution_id = (
        _execution_contract_exists(plan=plan, session_id=session_id) if plan_exists else (False, "")
    )
    lock_available = _lock_available(plan=plan, session_id=session_id, execution_id=execution_id) if plan_exists else False

    enablement = assess_railway_execution_enablement_policy(plan=plan if plan_exists else {}, user_text=text or "")
    execution_mode = enablement.mode
    real_execution_enabled = enablement.allows_real_mutation()
    policy_passes = enablement.allows_execute_enrollment()
    dry_run_allowed = bool(
        plan_exists and enablement.target_loaded and execution_mode == "dry_run" and policy_passes
    )

    checks: dict[str, GateCheckStatus] = {
        "deployment_plan": _status(plan_exists),
        "mutation_ready": _status(mutation_ready, applicable=plan_exists),
        "review_confirmed": _status(review_confirmed, applicable=plan_exists),
        "preflight_exists": _status(preflight_exists, applicable=plan_exists),
        "preflight_approved": _status(preflight_approved, applicable=plan_exists and preflight_exists),
        "simulation_exists": _status(simulation_exists, applicable=plan_exists),
        "simulation_ready_to_execute": _status(
            simulation_ready,
            applicable=plan_exists and simulation_exists,
        ),
        "env_readiness": _status(env_ready, applicable=plan_exists),
        "critical_env_secrets_configured": _status(critical_secrets_ok, applicable=plan_exists),
        "execution_contract_exists": _status(contract_exists, applicable=plan_exists),
        "execution_lock_available": _status(lock_available, applicable=plan_exists),
        "execution_enabled": _status(real_execution_enabled),
        "execution_policy": _status(policy_passes, applicable=plan_exists),
        "dry_run_allowed": _status(dry_run_allowed, applicable=plan_exists),
        "real_mutation_allowed": _status(real_execution_enabled, applicable=plan_exists),
    }

    phase_execution_allowed = bool(
        execution_mode == "dry_run"
        and all(checks.get(key) == "pass" for key in _DRY_RUN_ENROLLMENT_CHECKS)
    )
    checks["phase_execution_allowed"] = _status(phase_execution_allowed, applicable=plan_exists)

    blocking_reasons: list[str] = []
    messages: list[str] = []
    next_steps: list[str] = []
    contract_blockers: list[str] = []

    if not plan_exists:
        blocking_reasons.append("plan_missing")
        messages.append("No deployment plan is available in this session.")
        contract_blockers.append("deployment plan")
        next_steps.append("create railway deployment plan for <repo> in <project> / <environment>")
    else:
        if not review_confirmed:
            blocking_reasons.append("review_not_confirmed")
            messages.append("Deployment plan review has not been confirmed.")
            contract_blockers.append("deployment plan review confirmation")
            next_steps.append("review railway deployment plan")
            next_steps.append("confirm railway deployment plan")
        if not mutation_ready:
            blocking_reasons.append("mutation_not_ready")
            missing = ", ".join(mutation_gate.get("missing_labels") or mutation_gate.get("missing") or [])
            messages.append(f"Deployment plan is not mutation-ready ({missing or 'incomplete fields'}).")
            contract_blockers.extend(list(mutation_gate.get("missing_labels") or mutation_gate.get("missing") or []))
            next_steps.append("complete the railway deployment plan")
        if not preflight_exists:
            blocking_reasons.append("preflight_not_created")
            messages.append("Service creation preflight has not been created.")
            contract_blockers.append("service creation preflight")
            next_steps.append("create railway service creation preflight")
        elif not preflight_approved:
            blocking_reasons.append("preflight_not_approved")
            messages.append("Preflight has not been approved.")
            contract_blockers.append("preflight approval")
            next_steps.append("approve railway service creation preflight")
        if not critical_secrets_ok:
            blocking_reasons.append("critical_env_values_missing")
            missing = list(env_state.get("critical_missing") or env_state.get("missing") or [])
            if missing:
                messages.append(f"Required critical env values are missing: {', '.join(missing)}.")
            else:
                messages.append("Required critical env values are missing.")
            next_steps.append("configure missing env values through Credential Center")
            next_steps.append("refresh railway env readiness")
        elif not env_ready:
            blocking_reasons.append("env_readiness_blocked")
            messages.append("Env value readiness is not satisfied for this deployment target.")
            next_steps.append("refresh railway env readiness")
        if not simulation_exists:
            blocking_reasons.append("simulation_not_complete")
            messages.append("Service creation simulation has not been completed.")
            contract_blockers.append("service creation simulation")
            next_steps.append("simulate railway service creation")
        elif not simulation_ready:
            blocking_reasons.append("simulation_not_ready")
            sim_messages = list((simulation or {}).get("blocking_reason_messages") or [])
            sim_codes = list((simulation or {}).get("blocking_reasons") or [])
            detail = "; ".join(sim_messages) if sim_messages else ", ".join(sim_codes)
            if detail:
                messages.append(f"Simulation is not ready to execute: {detail}.")
            else:
                messages.append("Simulation is not ready to execute.")
            contract_blockers.append("simulation ready_to_execute")
            next_steps.append("simulate railway service creation")
        if not contract_exists:
            blocking_reasons.append("execution_contract_missing")
            messages.append("Execution contract journal has not been created for this target.")
        if not lock_available:
            blocking_reasons.append("execution_lock_unavailable")
            messages.append("Execution lock is held by another in-flight execution for this target.")
            contract_blockers.append("execution lock unavailable")

    if enablement.mode == "disabled":
        blocking_reasons.append("execution_policy_disabled")
        messages.append("Railway greenfield execution mode is disabled.")
        contract_blockers.append("Railway greenfield execution mode is disabled")
    if enablement.is_production and not enablement.production_allowed:
        blocking_reasons.append("production_not_allowed")
        messages.append("Production greenfield execution is not allowed by runtime policy.")
        contract_blockers.append("Production greenfield execution is not allowed by runtime policy")
    if enablement.mode != "disabled" and not enablement.allowlist_passed:
        for code in enablement.blocking_reasons:
            if code in {"project_not_allowlisted", "environment_not_allowlisted", "service_not_allowlisted"}:
                if code not in blocking_reasons:
                    blocking_reasons.append(code)
        for msg in enablement.blocking_reason_messages:
            if msg not in messages and "production" not in msg.lower():
                messages.append(msg)
                contract_blockers.append(msg)
    if enablement.mode == "enabled" and enablement.final_phrase_required and not enablement.final_phrase_valid:
        blocking_reasons.append("final_phrase_required")
        if not enablement.final_phrase_provided:
            messages.append("Final governed execution approval phrase is required but was not provided.")
            contract_blockers.append("final approval phrase")
        else:
            messages.append("Final governed execution approval phrase does not match the required exact text.")
            contract_blockers.append("final approval phrase (invalid)")

    if not real_execution_enabled and enablement.mode != "dry_run":
        blocking_reasons.append("execution_disabled")
        messages.append(
            "Railway greenfield service creation execution is disabled in this runtime."
        )
        if enablement.mode == "enabled" and not enablement.greenfield_execution_enabled:
            contract_blockers.append("execution_enabled (greenfield execution flag disabled)")
        elif enablement.mode != "disabled":
            contract_blockers.append("execution_enabled (disabled by platform policy)")

    if plan_exists and not policy_passes and enablement.mode != "disabled":
        blocking_reasons.append("execution_policy_failed")
        if not any("execution policy" in b.lower() for b in contract_blockers):
            for msg in enablement.blocking_reason_messages:
                if msg not in messages:
                    messages.append(msg)

    required_pass_real = (
        "deployment_plan",
        "mutation_ready",
        "review_confirmed",
        "preflight_exists",
        "preflight_approved",
        "simulation_exists",
        "simulation_ready_to_execute",
        "env_readiness",
        "critical_env_secrets_configured",
        "execution_contract_exists",
        "execution_lock_available",
        "execution_policy",
        "execution_enabled",
    )
    ready = (
        phase_execution_allowed
        if execution_mode == "dry_run"
        else all(checks.get(key) == "pass" for key in required_pass_real)
    )

    lifecycle_state = lifecycle_state_for_approvals(
        review_confirmed=review_confirmed,
        preflight_exists=preflight_exists,
        preflight_approved=preflight_approved,
        simulation_complete=simulation_exists,
    )

    deduped_steps: list[str] = []
    for step in next_steps:
        if step not in deduped_steps:
            deduped_steps.append(step)

    return RailwayExecutionReadinessGate(
        ready=ready,
        execution_enabled=real_execution_enabled,
        execution_mode=execution_mode,
        dry_run_allowed=dry_run_allowed,
        real_mutation_allowed=real_execution_enabled,
        phase_execution_allowed=phase_execution_allowed,
        checks=checks,
        blocking_reasons=blocking_reasons,
        blocking_reason_messages=messages,
        next_steps=deduped_steps,
        contract_blockers=contract_blockers,
        lifecycle_state=lifecycle_state,
        env_state=env_state,
        execution_id=execution_id,
        enablement=enablement,
    )

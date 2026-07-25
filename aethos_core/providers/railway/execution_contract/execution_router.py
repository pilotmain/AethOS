# SPDX-License-Identifier: Apache-2.0
"""Route Railway execution contract prompts (contract-only, no live mutations)."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_dry_run_executor import (
    parse_simulated_failure_phase,
    run_dry_run_phase_execution,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_dispatch import (
    run_single_real_mutation_phase,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    assess_railway_execution_enablement_policy,
    is_railway_execution_enablement_intent,
    load_railway_execution_enablement_config,
)
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    execution_runtime_allows_real_mutation,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    acquire_execution_lock,
    bind_session_execution,
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.execution_idempotency import (
    derive_idempotency_key,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    get_or_create_execution_journal,
    load_journal_by_id,
    save_execution_journal,
)
from aethos_core.providers.railway.execution_contract.execution_readiness_gate import (
    RailwayExecutionReadinessGate,
    evaluate_railway_execution_readiness,
    is_railway_execution_readiness_gate_intent,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    list_execution_receipts,
    record_simulated_phase_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import (
    attach_rollback_journal,
)
from aethos_core.providers.railway.execution_contract.execution_renderer import (
    render_execution_contract_overview,
    render_execution_journal,
    render_execution_phases,
    render_execution_readiness_gate,
    render_railway_execution_enablement,
    render_execution_receipts,
    render_execution_request_result,
    render_execution_timeline,
    render_rollback_contract,
    render_rollback_receipts,
    render_rollback_timeline,
    render_mutation_audit,
    render_mutation_preview,
    render_connect_source_rollback_contract,
    render_dry_run_connect_source_rollback_result,
    render_live_connect_source_rollback_result,
    render_source_binding_audit,
    render_source_binding_status,
    render_env_configure_rollback_contract,
    render_env_configure_status,
    render_env_configure_audit,
    render_env_configure_verification,
    render_deploy_trigger_readiness,
    render_deploy_trigger_rollback_contract,
    render_live_trigger_deploy_result,
    render_runtime_verification_readiness,
    render_runtime_verification_status,
    render_readonly_runtime_verification_result,
    render_rollback_readiness,
    render_live_rollback_result,
    render_railway_production_policy,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    assess_railway_production_policy,
    is_railway_production_policy_intent,
)
from aethos_core.providers.railway.execution_contract.connect_source_rollback_contract import (
    build_connect_source_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.env_configure_rollback_contract import (
    build_env_configure_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.env_configure_audit import (
    build_railway_env_configure_audit_report,
)
from aethos_core.providers.railway.execution_contract.env_configure_verification import (
    verify_env_configure_readonly,
)
from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
    assess_deploy_trigger_readiness,
)
from aethos_core.providers.railway.execution_contract.env_configure_status import (
    assess_railway_env_configure_status,
)
from aethos_core.providers.railway.execution_contract.execution_dry_run_rollback_executor import (
    run_dry_run_connect_source_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_real_rollback_disconnect_executor import (
    run_real_disconnect_connect_source_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch import (
    run_live_rollback_orchestration,
)
from aethos_core.providers.railway.execution_contract.execution_real_rollback_env_configure import (
    run_real_revert_env_configure_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_rollback_readiness import (
    assess_railway_rollback_readiness,
    is_railway_rollback_readiness_intent,
)
from aethos_core.providers.railway.execution_contract.rollback_audit_renderer import (
    build_rollback_isolation_audit,
    render_rollback_isolation_audit,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_trigger_deploy import (
    run_real_mutation_trigger_deploy,
)
from aethos_core.providers.railway.execution_contract.execution_readonly_runtime_verification_executor import (
    run_readonly_runtime_verification,
)
from aethos_core.providers.railway.execution_contract.runtime_verification_readiness import (
    assess_runtime_verification_readiness,
)
from aethos_core.providers.railway.execution_contract.deploy_trigger_rollback_contract import (
    build_deploy_trigger_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.mutation_audit import (
    build_railway_mutation_audit_report,
)
from aethos_core.providers.railway.execution_contract.mutation_preview import (
    assess_railway_mutation_preview,
)
from aethos_core.providers.railway.execution_contract.source_binding_audit import (
    build_railway_source_binding_audit_report,
)
from aethos_core.providers.railway.execution_contract.source_binding_status import (
    assess_railway_source_binding_status,
)
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    transition_journal_state,
)

_CONTRACT_RX = re.compile(r"\bshow\s+railway\s+execution\s+contract\b", re.I)
_PHASES_RX = re.compile(r"\bshow\s+railway\s+execution\s+phases\b", re.I)
_ROLLBACK_RX = re.compile(r"\bshow\s+railway\s+rollback\s+contract\b", re.I)
_JOURNAL_RX = re.compile(r"\bshow\s+railway\s+execution\s+journal\b", re.I)
_RECEIPTS_RX = re.compile(r"\bshow\s+railway\s+execution\s+receipts\b", re.I)
_TIMELINE_RX = re.compile(r"\bshow\s+railway\s+execution\s+timeline\b", re.I)
_ROLLBACK_TIMELINE_RX = re.compile(r"\bshow\s+railway\s+rollback\s+timeline\b", re.I)
_ROLLBACK_RECEIPTS_RX = re.compile(r"\bshow\s+railway\s+rollback\s+receipts\b", re.I)
_EXECUTE_RX = re.compile(r"\bexecute\s+railway\s+service\s+creation\b", re.I)
_SIMULATE_EXECUTE_RX = re.compile(r"\bsimulate\s+railway\s+service\s+creation\b", re.I)
_MUTATION_AUDIT_RX = re.compile(r"\bshow\s+railway\s+(?:live\s+)?mutation\s+audit\b", re.I)
_MUTATION_PREVIEW_RX = re.compile(
    r"\b(?:what\s+would\s+railway\s+mutate|show\s+railway\s+mutation\s+preview)\b",
    re.I,
)
_SOURCE_BINDING_STATUS_RX = re.compile(r"\bshow\s+railway\s+source\s+binding\s+status\b", re.I)
_SOURCE_BINDING_AUDIT_RX = re.compile(r"\bshow\s+railway\s+source\s+binding\s+audit\b", re.I)
_SOURCE_BINDING_ROLLBACK_CONTRACT_RX = re.compile(
    r"\bshow\s+railway\s+source\s+binding\s+rollback\s+contract\b",
    re.I,
)
_SIMULATE_SOURCE_BINDING_ROLLBACK_RX = re.compile(
    r"\bsimulate\s+railway\s+source\s+binding\s+rollback\b",
    re.I,
)
_EXECUTE_SOURCE_BINDING_ROLLBACK_RX = re.compile(
    r"\bexecute\s+railway\s+source\s+binding\s+rollback\b",
    re.I,
)
_ENV_CONFIGURE_STATUS_RX = re.compile(r"\bshow\s+railway\s+env\s+configure\s+status\b", re.I)
_ENV_CONFIGURE_AUDIT_RX = re.compile(r"\bshow\s+railway\s+env\s+configure\s+audit\b", re.I)
_ENV_CONFIGURE_ROLLBACK_CONTRACT_RX = re.compile(
    r"\bshow\s+railway\s+env\s+configure\s+rollback\s+contract\b",
    re.I,
)
_ENV_CONFIGURE_VERIFICATION_RX = re.compile(
    r"\bshow\s+railway\s+env\s+configure\s+verification\b",
    re.I,
)
_DEPLOY_TRIGGER_READINESS_RX = re.compile(
    r"\bshow\s+railway\s+deploy\s+trigger\s+readiness\b",
    re.I,
)
_DEPLOY_TRIGGER_ROLLBACK_CONTRACT_RX = re.compile(
    r"\bshow\s+railway\s+deploy\s+trigger\s+rollback\s+contract\b",
    re.I,
)
_EXECUTE_DEPLOY_TRIGGER_RX = re.compile(
    r"\bexecute\s+railway\s+deploy\s+trigger\b",
    re.I,
)
_RUNTIME_VERIFICATION_READINESS_RX = re.compile(
    r"\bshow\s+railway\s+runtime\s+verification\s+readiness\b",
    re.I,
)
_RUNTIME_VERIFICATION_STATUS_RX = re.compile(
    r"\bshow\s+railway\s+runtime\s+verification\b",
    re.I,
)
_EXECUTE_RUNTIME_VERIFICATION_RX = re.compile(
    r"\bexecute\s+railway\s+runtime\s+verification\b",
    re.I,
)
_ROLLBACK_READINESS_RX = re.compile(
    r"\b(?:check|show)\s+railway\s+rollback\s+readiness\b",
    re.I,
)
_ROLLBACK_WHY_RX = re.compile(
    r"\bwhy\s+can'?t\s+railway\s+rollback\s+start\??",
    re.I,
)
_EXECUTE_ROLLBACK_RX = re.compile(
    r"\bexecute\s+railway\s+rollback\b",
    re.I,
)
_EXECUTE_ENV_ROLLBACK_RX = re.compile(
    r"\bexecute\s+railway\s+env\s+rollback\b",
    re.I,
)
_ROLLBACK_AUDIT_RX = re.compile(
    r"\bshow\s+railway\s+rollback\s+audit\b",
    re.I,
)


def is_railway_execution_contract_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _CONTRACT_RX.search(raw)
        or _PHASES_RX.search(raw)
        or _ROLLBACK_RX.search(raw)
        or _JOURNAL_RX.search(raw)
        or _RECEIPTS_RX.search(raw)
        or _EXECUTE_RX.search(raw)
        or _SIMULATE_EXECUTE_RX.search(raw)
        or _TIMELINE_RX.search(raw)
        or _ROLLBACK_TIMELINE_RX.search(raw)
        or _ROLLBACK_RECEIPTS_RX.search(raw)
        or is_railway_execution_readiness_gate_intent(raw)
        or is_railway_execution_enablement_intent(raw)
        or _MUTATION_AUDIT_RX.search(raw)
        or _MUTATION_PREVIEW_RX.search(raw)
        or _SOURCE_BINDING_STATUS_RX.search(raw)
        or _SOURCE_BINDING_AUDIT_RX.search(raw)
        or _SOURCE_BINDING_ROLLBACK_CONTRACT_RX.search(raw)
        or _SIMULATE_SOURCE_BINDING_ROLLBACK_RX.search(raw)
        or _EXECUTE_SOURCE_BINDING_ROLLBACK_RX.search(raw)
        or _ENV_CONFIGURE_STATUS_RX.search(raw)
        or _ENV_CONFIGURE_AUDIT_RX.search(raw)
        or _ENV_CONFIGURE_ROLLBACK_CONTRACT_RX.search(raw)
        or _ENV_CONFIGURE_VERIFICATION_RX.search(raw)
        or _DEPLOY_TRIGGER_READINESS_RX.search(raw)
        or _DEPLOY_TRIGGER_ROLLBACK_CONTRACT_RX.search(raw)
        or _EXECUTE_DEPLOY_TRIGGER_RX.search(raw)
        or _RUNTIME_VERIFICATION_READINESS_RX.search(raw)
        or _RUNTIME_VERIFICATION_STATUS_RX.search(raw)
        or _EXECUTE_RUNTIME_VERIFICATION_RX.search(raw)
        or is_railway_rollback_readiness_intent(raw)
        or is_railway_production_policy_intent(raw)
        or _EXECUTE_ROLLBACK_RX.search(raw)
        or _EXECUTE_ENV_ROLLBACK_RX.search(raw)
        or _ROLLBACK_AUDIT_RX.search(raw)
    )


def assess_execution_approvals(
    *,
    plan: dict[str, Any] | None,
    preflight: dict[str, Any] | None,
    simulation: dict[str, Any] | None,
    session_id: str = "default",
    text: str | None = None,
) -> dict[str, Any]:
    gate = evaluate_railway_execution_readiness(
        session_id,
        text,
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )
    return gate.to_assessment_dict()


def request_execution_contract(
    *,
    plan: dict[str, Any],
    session_id: str,
    approval: dict[str, Any],
) -> dict[str, Any]:
    """Enroll execution journal, lock, rollback plan, and simulated receipts (no mutation)."""
    lifecycle_state = str(approval.get("lifecycle_state") or "draft")
    journal, created = get_or_create_execution_journal(
        plan=plan,
        session_id=session_id,
        initial_state=lifecycle_state,
        approval=approval,
    )
    journal["approval"] = dict(approval)
    journal = save_execution_journal(journal)

    idempotency_key = derive_idempotency_key(plan=plan)
    lock_result: dict[str, Any] = {"ok": True, "reused": False}
    if created or str(journal.get("state")) in {
        "simulation_complete",
        "execution_requested",
        "execution_locked",
    }:
        lock_result = acquire_execution_lock(
            idempotency_key=idempotency_key,
            execution_id=str(journal["execution_id"]),
            session_id=session_id,
            project=str(plan.get("project") or ""),
            environment=str(plan.get("environment") or ""),
            service_name=str(plan.get("service_name") or ""),
        )
    lock_acquired = bool(lock_result.get("ok"))
    if not lock_acquired:
        return {
            "ok": False,
            "journal": journal,
            "journal_created": created,
            "lock_acquired": False,
            "lock_reason": str(lock_result.get("detail") or lock_result.get("reason") or ""),
            "approval_blockers": [],
        }

    bind_session_execution(session_id=session_id, execution_id=str(journal["execution_id"]))

    if not journal.get("rollback_journal"):
        journal = attach_rollback_journal(journal)

    enablement_cfg = load_railway_execution_enablement_config()
    user_text = str(approval.get("user_text") or "")
    policy = assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    dry_run_result = None
    real_mutation_result = None
    receipts = list_execution_receipts(execution_id=str(journal["execution_id"]))
    if enablement_cfg.mode == "enabled":
        if policy.allows_real_mutation():
            real_mutation_result = run_single_real_mutation_phase(
                journal=journal,
                plan=plan,
                policy=policy,
                user_text=user_text,
            )
            journal = real_mutation_result.journal
    elif enablement_cfg.mode == "dry_run":
        dry_run_result = run_dry_run_phase_execution(
            journal=journal,
            plan=plan,
            failure_phase=str(approval.get("simulated_failure_phase") or "") or None,
            user_text=user_text,
        )
        journal = dry_run_result.journal
    elif not receipts:
        record_simulated_phase_receipts(execution_id=str(journal["execution_id"]))

    current_state = str(journal.get("state") or lifecycle_state)
    try:
        if current_state == "simulation_complete":
            journal = transition_journal_state(journal, to_state="execution_requested")
            journal = save_execution_journal(journal)
        if str(journal.get("state")) == "execution_requested":
            journal = transition_journal_state(journal, to_state="execution_locked")
            journal = save_execution_journal(journal)
    except IllegalExecutionTransitionError:
        pass

    detail = (
        "Execution contract enrolled. Live Railway mutations remain disabled; "
        "receipts recorded as simulated."
    )
    mutation_performed = False
    if enablement_cfg.mode == "dry_run" and dry_run_result is not None:
        detail = dry_run_result.detail
    elif enablement_cfg.mode == "enabled":
        if real_mutation_result is not None:
            detail = real_mutation_result.detail
            mutation_performed = bool(real_mutation_result.mutation_performed)
        elif policy.allows_real_mutation():
            detail = "Enabled mode: real mutation policy satisfied but executor did not run."
        else:
            detail = (
                "Enabled mode: execution enrolled but real mutation blocked by policy "
                f"({', '.join(policy.blocking_reasons) or 'policy'})."
            )
    return {
        "ok": True,
        "journal": journal,
        "journal_created": created,
        "lock_acquired": lock_acquired,
        "lock_reused": bool(lock_result.get("reused")),
        "detail": detail,
        "dry_run_result": dry_run_result,
        "real_mutation_result": real_mutation_result,
        "mutation_performed": mutation_performed,
        "approval_blockers": [],
    }


def route_railway_execution_contract(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_railway_execution_contract_intent(raw):
        return None

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        ensure_railway_deployment_lifecycle_for_lane,
    )

    gate_first = bool(
        _EXECUTE_RX.search(raw)
        or _SIMULATE_EXECUTE_RX.search(raw)
        or _SIMULATE_SOURCE_BINDING_ROLLBACK_RX.search(raw)
        or _EXECUTE_SOURCE_BINDING_ROLLBACK_RX.search(raw)
        or _EXECUTE_DEPLOY_TRIGGER_RX.search(raw)
        or _EXECUTE_RUNTIME_VERIFICATION_RX.search(raw)
        or _EXECUTE_ROLLBACK_RX.search(raw)
        or _EXECUTE_ENV_ROLLBACK_RX.search(raw)
        or is_railway_execution_readiness_gate_intent(raw)
    )
    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=not gate_first,
        require_preflight=not gate_first,
        require_simulation=not gate_first,
    )

    if (
        _MUTATION_PREVIEW_RX.search(raw)
        or _MUTATION_AUDIT_RX.search(raw)
        or _SOURCE_BINDING_STATUS_RX.search(raw)
        or _SOURCE_BINDING_AUDIT_RX.search(raw)
        or _SOURCE_BINDING_ROLLBACK_CONTRACT_RX.search(raw)
        or _SIMULATE_SOURCE_BINDING_ROLLBACK_RX.search(raw)
        or _EXECUTE_SOURCE_BINDING_ROLLBACK_RX.search(raw)
        or _ENV_CONFIGURE_STATUS_RX.search(raw)
        or _ENV_CONFIGURE_AUDIT_RX.search(raw)
        or _ENV_CONFIGURE_ROLLBACK_CONTRACT_RX.search(raw)
        or _ENV_CONFIGURE_VERIFICATION_RX.search(raw)
        or _DEPLOY_TRIGGER_READINESS_RX.search(raw)
        or _DEPLOY_TRIGGER_ROLLBACK_CONTRACT_RX.search(raw)
        or _EXECUTE_DEPLOY_TRIGGER_RX.search(raw)
        or _RUNTIME_VERIFICATION_READINESS_RX.search(raw)
        or _RUNTIME_VERIFICATION_STATUS_RX.search(raw)
        or _EXECUTE_RUNTIME_VERIFICATION_RX.search(raw)
        or is_railway_rollback_readiness_intent(raw)
        or _EXECUTE_ROLLBACK_RX.search(raw)
        or _EXECUTE_ENV_ROLLBACK_RX.search(raw)
        or _ROLLBACK_AUDIT_RX.search(raw)
    ):
        plan = lane.plan or {}
        execution_id = (
            resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""
        )
        journal = load_journal_by_id(execution_id) if execution_id else None
        if not journal and plan.get("repo"):
            journal, _created = get_or_create_execution_journal(
                plan=plan,
                session_id=session_id,
                initial_state="simulation_complete",
                approval={},
            )
            if not journal.get("rollback_journal"):
                journal = attach_rollback_journal(journal)

        if _SOURCE_BINDING_ROLLBACK_CONTRACT_RX.search(raw):
            contract = build_connect_source_rollback_contract(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
            )
            body = render_connect_source_rollback_contract(contract)
            return body, "railway_source_binding_rollback_contract", _meta(
                session_id,
                stage="source_binding_rollback_contract",
                eligible=str(contract.eligible_for_dry_run_rollback).lower(),
            )

        if _ROLLBACK_AUDIT_RX.search(raw):
            audit_execution_id = execution_id or str((journal or {}).get("execution_id") or "")
            audit = build_rollback_isolation_audit(execution_id=audit_execution_id)
            body = render_rollback_isolation_audit(audit)
            return body, "railway_rollback_audit", _meta(
                session_id,
                stage="rollback_audit",
                audit_ok=str(audit.ok).lower(),
            )

        if _ROLLBACK_READINESS_RX.search(raw) or _ROLLBACK_WHY_RX.search(raw):
            readiness = assess_railway_rollback_readiness(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
                user_text=raw,
            )
            body = render_rollback_readiness(readiness)
            return body, "railway_rollback_readiness", _meta(
                session_id,
                stage="rollback_readiness",
                ready=str(readiness.ready_for_live_rollback).lower(),
            )

        if _EXECUTE_ROLLBACK_RX.search(raw):
            if not journal:
                body = "No execution journal found. Enroll execution before live rollback."
                return body, "railway_execution_rollback_blocked", _meta(
                    session_id,
                    stage="rollback_blocked",
                )
            rollback_result = run_live_rollback_orchestration(
                journal=journal,
                plan=plan,
                user_text=raw,
                session_id=session_id,
            )
            body = render_live_rollback_result(rollback_result)
            return body, "railway_execution_rollback", _meta(
                session_id,
                stage="rollback_executed",
                execution_id=str(rollback_result.journal.get("execution_id") or ""),
                mutation_performed=str(rollback_result.mutation_performed).lower(),
                rollback_completed=str(rollback_result.rollback_completed).lower(),
            )

        if _EXECUTE_ENV_ROLLBACK_RX.search(raw):
            if not journal:
                body = "No execution journal found. Enroll execution before env rollback."
                return body, "railway_env_rollback_blocked", _meta(
                    session_id,
                    stage="env_rollback_blocked",
                )
            env_result = run_real_revert_env_configure_rollback(
                journal=journal,
                plan=plan,
                user_text=raw,
            )
            body = render_live_rollback_result(env_result)
            return body, "railway_execution_rollback", _meta(
                session_id,
                stage="env_rollback_executed",
                mutation_performed=str(env_result.mutation_performed).lower(),
            )

        if _EXECUTE_SOURCE_BINDING_ROLLBACK_RX.search(raw):
            if not journal:
                body = "No execution journal found. Enroll execution before live source rollback."
                return body, "railway_source_binding_rollback_blocked", _meta(
                    session_id,
                    stage="rollback_blocked",
                )
            live_result = run_real_disconnect_connect_source_rollback(
                journal=journal,
                plan=plan,
                user_text=raw,
            )
            body = render_live_connect_source_rollback_result(live_result)
            return body, "railway_source_binding_rollback_executed", _meta(
                session_id,
                stage="source_binding_rollback_executed",
                execution_id=str(live_result.journal.get("execution_id") or ""),
                idempotent_replay=str(live_result.idempotent_replay).lower(),
                mutation_performed=str(live_result.mutation_performed).lower(),
                policy_blocked=str(live_result.policy_blocked).lower(),
            )

        if _SIMULATE_SOURCE_BINDING_ROLLBACK_RX.search(raw):
            if not journal:
                body = "No execution journal found. Enroll execution before simulating rollback."
                return body, "railway_source_binding_rollback_blocked", _meta(
                    session_id,
                    stage="rollback_blocked",
                )
            rollback_result = run_dry_run_connect_source_rollback(journal=journal, plan=plan)
            body = render_dry_run_connect_source_rollback_result(rollback_result)
            return body, "railway_source_binding_rollback_simulated", _meta(
                session_id,
                stage="source_binding_rollback_simulated",
                execution_id=str(rollback_result.journal.get("execution_id") or ""),
                idempotent_replay=str(rollback_result.idempotent_replay).lower(),
                mutation_performed="false",
            )

        if _ENV_CONFIGURE_ROLLBACK_CONTRACT_RX.search(raw):
            contract = build_env_configure_rollback_contract(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
            )
            body = render_env_configure_rollback_contract(contract)
            return body, "railway_env_configure_rollback_contract", _meta(
                session_id,
                stage="env_configure_rollback_contract",
                rollback_plan_ready=str(contract.rollback_plan_ready).lower(),
            )

        if _ENV_CONFIGURE_STATUS_RX.search(raw):
            status = assess_railway_env_configure_status(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
            )
            body = render_env_configure_status(status)
            return body, "railway_env_configure_status", _meta(
                session_id,
                stage="env_configure_status",
                rollback_plan_ready=str(status.rollback_plan_ready).lower(),
                env_names_verified=str(status.env_names_verified).lower(),
                ready_for_deploy_trigger=str(status.ready_for_deploy_trigger).lower(),
            )

        if _ENV_CONFIGURE_AUDIT_RX.search(raw):
            audit = build_railway_env_configure_audit_report(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
                user_text=raw,
            )
            body = render_env_configure_audit(audit)
            return body, "railway_env_configure_audit", _meta(
                session_id,
                stage="env_configure_audit",
                audit_ok=str(audit.ok).lower(),
            )

        if _ENV_CONFIGURE_VERIFICATION_RX.search(raw):
            service_id = str((journal or {}).get("railway_service_id") or "")
            environment_id = str((journal or {}).get("railway_environment_id") or "")
            journal_names: list[str] = []
            if journal and isinstance(journal.get("env_vars_configured"), dict):
                for group in journal["env_vars_configured"].get("groups", {}).values():
                    if isinstance(group, dict):
                        journal_names.extend(str(n) for n in group.get("env_names") or [])
            if not service_id or not environment_id:
                body = "No Railway service/environment on journal for env verification."
                return body, "railway_env_configure_verification_blocked", _meta(
                    session_id,
                    stage="verification_blocked",
                )
            verification = verify_env_configure_readonly(
                environment_id=environment_id,
                service_id=service_id,
                journal_env_names=journal_names,
            )
            body = render_env_configure_verification(verification)
            return body, "railway_env_configure_verification", _meta(
                session_id,
                stage="env_configure_verification",
                verified=str(verification.verified).lower(),
            )

        if _DEPLOY_TRIGGER_ROLLBACK_CONTRACT_RX.search(raw):
            contract = build_deploy_trigger_rollback_contract(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
                user_text=raw,
            )
            body = render_deploy_trigger_rollback_contract(contract)
            return body, "railway_deploy_trigger_rollback_contract", _meta(
                session_id,
                stage="deploy_trigger_rollback_contract",
                rollback_plan_ready=str(contract.rollback_plan_ready).lower(),
            )

        if _EXECUTE_DEPLOY_TRIGGER_RX.search(raw):
            if not journal:
                body = "No execution journal found. Enroll execution before deploy trigger."
                return body, "railway_deploy_trigger_blocked", _meta(
                    session_id,
                    stage="deploy_trigger_blocked",
                )
            deploy_result = run_real_mutation_trigger_deploy(
                journal=journal,
                plan=plan,
                user_text=raw,
            )
            body = render_live_trigger_deploy_result(deploy_result)
            return body, "railway_deploy_trigger_executed", _meta(
                session_id,
                stage="deploy_trigger_executed",
                execution_id=str(deploy_result.journal.get("execution_id") or ""),
                mutation_performed=str(deploy_result.mutation_performed).lower(),
                policy_blocked=str(deploy_result.policy_blocked).lower(),
            )

        if _DEPLOY_TRIGGER_READINESS_RX.search(raw):
            readiness = assess_deploy_trigger_readiness(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
                user_text=raw,
            )
            body = render_deploy_trigger_readiness(readiness)
            return body, "railway_deploy_trigger_readiness", _meta(
                session_id,
                stage="deploy_trigger_readiness",
                ready=str(readiness.ready_for_deploy_trigger).lower(),
            )

        if _EXECUTE_RUNTIME_VERIFICATION_RX.search(raw):
            if not journal:
                body = "No execution journal found. Enroll execution before runtime verification."
                return body, "railway_runtime_verification_blocked", _meta(
                    session_id,
                    stage="runtime_verification_blocked",
                )
            verify_result = run_readonly_runtime_verification(
                journal=journal,
                plan=plan,
                user_text=raw,
            )
            body = render_readonly_runtime_verification_result(verify_result)
            return body, "railway_runtime_verification_executed", _meta(
                session_id,
                stage="runtime_verification_executed",
                execution_id=str(verify_result.journal.get("execution_id") or ""),
                mutation_performed=str(verify_result.mutation_performed).lower(),
                policy_blocked=str(verify_result.policy_blocked).lower(),
            )

        if _RUNTIME_VERIFICATION_READINESS_RX.search(raw):
            readiness = assess_runtime_verification_readiness(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
                user_text=raw,
            )
            body = render_runtime_verification_readiness(readiness)
            return body, "railway_runtime_verification_readiness", _meta(
                session_id,
                stage="runtime_verification_readiness",
                ready=str(readiness.ready_for_runtime_verification).lower(),
            )

        if _RUNTIME_VERIFICATION_STATUS_RX.search(raw):
            body = render_runtime_verification_status(journal=journal or {})
            return body, "railway_runtime_verification_status", _meta(
                session_id,
                stage="runtime_verification_status",
                performed=str(bool((journal or {}).get("runtime_verification_performed"))).lower(),
            )

        if _SOURCE_BINDING_STATUS_RX.search(raw):
            status = assess_railway_source_binding_status(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
            )
            body = render_source_binding_status(status)
            return body, "railway_source_binding_status", _meta(
                session_id,
                stage="source_binding_status",
                ready_for_env_writes=str(status.ready_for_env_writes).lower(),
            )

        if _SOURCE_BINDING_AUDIT_RX.search(raw):
            audit_report = build_railway_source_binding_audit_report(
                plan=plan,
                journal=journal,
                execution_id=execution_id,
            )
            body = render_source_binding_audit(audit_report)
            return body, "railway_source_binding_audit", _meta(
                session_id,
                stage="source_binding_audit",
                audit_ok=str(audit_report.ok).lower(),
            )

        if _MUTATION_PREVIEW_RX.search(raw):
            preview = assess_railway_mutation_preview(
                plan=plan,
                user_text=raw,
                execution_id=execution_id,
                journal=journal,
            )
            body = render_mutation_preview(preview)
            return body, "railway_mutation_preview", _meta(
                session_id,
                stage="mutation_preview",
                would_mutate=str(preview.would_mutate).lower(),
                kill_switch=str(preview.kill_switch_active).lower(),
            )
        audit = build_railway_mutation_audit_report(
            plan=plan,
            user_text=raw,
            execution_id=execution_id,
            journal=journal,
        )
        body = render_mutation_audit(audit)
        return body, "railway_mutation_audit", _meta(
            session_id,
            stage="mutation_audit",
            audit_ok=str(audit.ok).lower(),
            kill_switch=str(audit.kill_switch_active).lower(),
        )

    if is_railway_execution_enablement_intent(raw):
        plan = lane.plan or {}
        policy = assess_railway_execution_enablement_policy(plan=plan, user_text=raw)
        body = render_railway_execution_enablement(policy)
        return body, "railway_execution_enablement", _meta(
            session_id,
            stage="enablement",
            enablement=policy,
        )

    if is_railway_production_policy_intent(raw):
        plan = lane.plan or {}
        prod_execution_id = (
            resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""
        )
        prod_journal = load_journal_by_id(prod_execution_id) if prod_execution_id else None
        prod = assess_railway_production_policy(
            plan=plan,
            user_text=raw,
            execution_id=prod_execution_id,
            journal=prod_journal,
        )
        body = render_railway_production_policy(prod)
        return body, "railway_production_policy", _meta(
            session_id,
            stage="production_policy",
            forward_live_permitted=str(prod.forward_live_permitted).lower(),
        )

    if _CONTRACT_RX.search(raw):
        body = render_execution_contract_overview()
        return body, "railway_execution_contract_show", _meta(session_id, stage="contract")

    if _PHASES_RX.search(raw):
        body = render_execution_phases()
        return body, "railway_execution_contract_phases", _meta(session_id, stage="phases")

    if _ROLLBACK_RX.search(raw):
        body = render_rollback_contract()
        return body, "railway_execution_contract_rollback", _meta(session_id, stage="rollback")

    from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
        get_creation_preflight,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        get_deployment_plan_context,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
        get_simulation,
    )

    plan = lane.plan or get_deployment_plan_context(session_id=session_id)
    preflight = lane.preflight or get_creation_preflight(session_id=session_id)
    simulation = lane.simulation or get_simulation(session_id=session_id)
    gate = evaluate_railway_execution_readiness(
        session_id,
        raw,
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )

    if is_railway_execution_readiness_gate_intent(raw):
        body = render_execution_readiness_gate(gate)
        return body, "railway_execution_readiness_gate", _meta(
            session_id,
            stage="readiness_gate",
            gate=gate,
        )

    plan = lane.plan or {}
    approval = gate.to_assessment_dict()

    if _JOURNAL_RX.search(raw):
        execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else None
        journal = load_journal_by_id(execution_id) if execution_id else None
        if not journal and plan.get("repo"):
            journal, _created = get_or_create_execution_journal(
                plan=plan,
                session_id=session_id,
                initial_state=str(approval.get("lifecycle_state") or "draft"),
                approval=approval,
            )
        body = render_execution_journal(journal, readiness_gate=gate)
        return body, "railway_execution_contract_journal", _meta(
            session_id,
            stage="journal",
            execution_id=str((journal or {}).get("execution_id") or ""),
            gate=gate,
        )

    if _ROLLBACK_TIMELINE_RX.search(raw):
        execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""
        journal = load_journal_by_id(execution_id) if execution_id else None
        receipts = list_execution_receipts(execution_id=execution_id) if execution_id else []
        body = render_rollback_timeline(journal, receipts=receipts)
        return body, "railway_execution_rollback_timeline", _meta(
            session_id,
            stage="rollback_timeline",
            execution_id=execution_id,
            gate=gate,
        )

    if _ROLLBACK_RECEIPTS_RX.search(raw):
        execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""
        receipts = list_execution_receipts(execution_id=execution_id) if execution_id else []
        body = render_rollback_receipts(receipts, execution_id=execution_id)
        return body, "railway_execution_rollback_receipts", _meta(
            session_id,
            stage="rollback_receipts",
            execution_id=execution_id,
            gate=gate,
        )

    if _TIMELINE_RX.search(raw):
        execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""
        journal = load_journal_by_id(execution_id) if execution_id else None
        receipts = list_execution_receipts(execution_id=execution_id) if execution_id else []
        body = render_execution_timeline(journal, receipts=receipts)
        return body, "railway_execution_timeline", _meta(
            session_id,
            stage="timeline",
            execution_id=execution_id,
            gate=gate,
        )

    if _RECEIPTS_RX.search(raw):
        execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""
        receipts = list_execution_receipts(execution_id=execution_id) if execution_id else []
        body = render_execution_receipts(receipts, execution_id=execution_id)
        return body, "railway_execution_contract_receipts", _meta(
            session_id,
            stage="receipts",
            execution_id=execution_id,
            gate=gate,
        )

    if _EXECUTE_RX.search(raw) or _SIMULATE_EXECUTE_RX.search(raw):
        if not gate.can_enroll_execution():
            body = render_execution_readiness_gate(gate)
            return body, "railway_execution_contract_not_ready", _meta(
                session_id,
                stage="approval_blocked",
                gate=gate,
            )

        approval = dict(approval)
        approval["user_text"] = raw
        failure_phase = parse_simulated_failure_phase(raw)
        if failure_phase:
            approval["simulated_failure_phase"] = failure_phase
        result = request_execution_contract(plan=plan, session_id=session_id, approval=approval)
        body = render_execution_request_result(result)
        journal = result.get("journal") or {}
        dry_run_result = result.get("dry_run_result")
        real_mutation_result = result.get("real_mutation_result")
        simulated_count = (
            str(dry_run_result.simulated_phase_count) if dry_run_result is not None else "0"
        )
        meta_extra: dict[str, str] = {
            "simulated_phase_count": simulated_count,
        }
        if real_mutation_result is not None:
            meta_extra["mutation_performed"] = str(
                bool(getattr(real_mutation_result, "mutation_performed", False))
            ).lower()
            meta_extra["real_mutation_service_id"] = str(
                getattr(real_mutation_result, "service_id", "") or ""
            )
        elif result.get("mutation_performed"):
            meta_extra["mutation_performed"] = "true"
        return body, "railway_execution_contract_requested", _meta(
            session_id,
            stage="execution_requested",
            execution_id=str(journal.get("execution_id") or ""),
            lock_acquired=str(result.get("lock_acquired", False)).lower(),
            gate=gate,
            **meta_extra,
        )

    return None


def _meta(
    session_id: str,
    *,
    stage: str,
    gate: RailwayExecutionReadinessGate | None = None,
    enablement: Any | None = None,
    **extra: str,
) -> dict[str, str]:
    meta = {
        "route_id": "railway_execution_contract",
        "matched_module": "providers.railway.execution_contract.execution_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "execution_enabled": str(execution_runtime_allows_real_mutation()).lower(),
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "execution_contract_stage": stage,
    }
    if gate is not None:
        meta["execution_gate_ready"] = str(gate.ready).lower()
        meta["blocking_count"] = str(gate.blocking_count())
        meta["execution_mode"] = gate.execution_mode
        meta["phase_execution_allowed"] = str(gate.phase_execution_allowed).lower()
        meta["real_mutation_allowed"] = str(gate.real_mutation_allowed).lower()
        if gate.enablement is not None:
            en = gate.enablement
            meta["policy_allowed"] = str(en.allowed).lower()
            meta["production_allowed"] = str(en.production_allowed).lower()
            meta["final_phrase_required"] = str(en.final_phrase_required).lower()
    if enablement is not None:
        meta["execution_mode"] = enablement.mode
        meta["policy_allowed"] = str(enablement.allowed).lower()
        meta["production_allowed"] = str(enablement.production_allowed).lower()
        meta["final_phrase_required"] = str(enablement.final_phrase_required).lower()
    meta.update(extra)
    return meta

# SPDX-License-Identifier: Apache-2.0
"""Railway agentic execution pilot — multi-step goal completion."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.execution_brain.execution_brain import build_execution_context, compose_blocked_plan_reply
from aethos_core.execution_brain.execution_goal import ExecutionGoal
from aethos_core.execution_brain.execution_memory import update_execution_memory
from aethos_core.execution_brain.execution_result import ExecutionPlanResult, ExecutionStepResult
from aethos_core.provider_e2e_readiness.blocker_mapping import map_railway_blockers


def run_railway_execution_brain(goal: ExecutionGoal, *, session_id: str = "default") -> ExecutionPlanResult:
    ctx = build_execution_context(goal, session_id=session_id)
    settings = get_settings()
    plan = ExecutionPlanResult(
        goal_summary=f"Deploy AethOS to Railway"
        + (" with env configuration and verification" if goal.requires_env or goal.requires_verify else ""),
        provider="railway",
    )

    checks = _run_readiness_checks(goal.user_text, session_id=session_id)
    ctx.checks = checks
    plan.checks_snapshot = _redact_checks(checks)

    token_step = _step_validate_token(checks)
    plan.steps.append(token_step)
    if token_step.status != "completed":
        return _finalize_blocked(
            plan, checks, settings, session_id=session_id, failed_step=token_step, user_text=goal.user_text
        )

    inventory_step = _step_discover_inventory(checks)
    plan.steps.append(inventory_step)
    if inventory_step.status != "completed":
        return _finalize_blocked(
            plan, checks, settings, session_id=session_id, failed_step=inventory_step, user_text=goal.user_text
        )

    from aethos_core.providers.railway.railway_inventory_target_picker import pick_railway_targets

    picked = pick_railway_targets(checks, goal.user_text, default_hint=goal.target_hint)
    if len(picked.targets) > 1:
        return _finalize_multi_target_plan(
            plan,
            checks,
            goal=goal,
            targets=[(row.project, row.environment, row.service) for row in picked.targets],
            session_id=session_id,
        )

    target = _resolve_target(checks, hint=goal.target_hint, user_text=goal.user_text)
    ctx.discovered_target = target
    target_step = _step_resolve_target(checks, target)
    plan.steps.append(target_step)
    if target_step.status != "completed":
        return _finalize_blocked(
            plan, checks, settings, session_id=session_id, failed_step=target_step, user_text=goal.user_text
        )

    ctx.target_label = " / ".join(target) if target else ""
    env_step = _step_env_readiness(checks, settings)
    plan.steps.append(env_step)
    if env_step.status == "blocked":
        return _finalize_blocked(
            plan, checks, settings, session_id=session_id, failed_step=env_step, user_text=goal.user_text
        )

    mutation_step = _step_mutation_gate(settings)
    plan.steps.append(mutation_step)

    preflight = _step_create_preflight(goal.user_text, session_id=session_id, checks=checks)
    plan.steps.append(preflight)
    if preflight.status == "awaiting_approval":
        plan.awaiting_approval = True
        plan.job_id = str(preflight.evidence.get("job_id") or "")
        plan.next_executable_step = "Approve preflight in Mission Control → Jobs, then execute orchestration."
        update_execution_memory(
            session_id=session_id,
            goal=goal.user_text,
            provider="railway",
            step_completed="railway.create_deploy_preflight",
            job_id=plan.job_id,
        )
        verify_step = ExecutionStepResult(
            step_id="railway.verify_deployment",
            label="Verify deployment",
            status="skipped",
            detail="Runs after governed orchestration completes.",
        )
        plan.steps.append(verify_step)
        plan.completion_ready = True
        return plan

    if preflight.status == "blocked":
        return _finalize_blocked(
            plan, checks, settings, session_id=session_id, failed_step=preflight, user_text=goal.user_text
        )

    plan.completion_ready = True
    return plan


def _run_readiness_checks(user_text: str, *, session_id: str) -> dict[str, Any]:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )

    return safe_run_deployment_readiness_checks(user_text=user_text, session_id=session_id)


def _step_validate_token(checks: dict[str, Any]) -> ExecutionStepResult:
    if checks.get("railway_credential_ok") and checks.get("railway_api_connection_ok"):
        return ExecutionStepResult(
            step_id="railway.validate_token",
            label="Validate Railway connection",
            status="completed",
            detail="Railway token validated.",
        )
    blockers = map_railway_blockers(checks, settings=get_settings(), include_mutation_gates=False)
    code = blockers[0].code if blockers else "RAILWAY_API_CONNECTION_FAILED"
    return ExecutionStepResult(
        step_id="railway.validate_token",
        label="Validate Railway connection",
        status="blocked",
        detail=blockers[0].meaning if blockers else "Railway connection failed.",
        blocker_code=code,
    )


def _step_discover_inventory(checks: dict[str, Any]) -> ExecutionStepResult:
    inv = checks.get("inventory") or {}
    if inv.get("ok"):
        return ExecutionStepResult(
            step_id="railway.discover_projects",
            label="Discover Railway projects",
            status="completed",
            detail=(
                f"{inv.get('project_count', 0)} project(s), "
                f"{inv.get('service_count', 0)} service(s) visible."
            ),
            evidence={"inventory": {"project_count": inv.get("project_count"), "service_count": inv.get("service_count")}},
        )
    return ExecutionStepResult(
        step_id="railway.discover_projects",
        label="Discover Railway projects",
        status="blocked",
        detail=str(inv.get("error") or "Railway project/service discovery failed."),
        blocker_code="RAILWAY_INVENTORY_UNAVAILABLE",
        evidence={
            "inventory_probe": inv.get("inventory_probe"),
            "inventory_probe_status": inv.get("inventory_probe_status"),
            "project_count": inv.get("project_count"),
            "service_count": inv.get("service_count"),
        },
    )


def _resolve_target(
    checks: dict[str, Any],
    *,
    hint: str,
    user_text: str = "",
) -> tuple[str, str, str] | None:
    from aethos_core.providers.railway.railway_inventory_target_picker import pick_single_railway_target

    return pick_single_railway_target(checks, user_text or hint, default_hint=hint)


def _step_resolve_target(
    checks: dict[str, Any],
    target: tuple[str, str, str] | None,
) -> ExecutionStepResult:
    if target is not None:
        return ExecutionStepResult(
            step_id="railway.discover_services",
            label="Discover target service",
            status="completed",
            detail=f"Target: {' / '.join(target)}",
            evidence={"target": target},
        )
    inv = checks.get("inventory") or {}
    return ExecutionStepResult(
        step_id="railway.discover_services",
        label="Discover target service",
        status="blocked",
        detail=f"Could not auto-select among {inv.get('service_count', 0)} service(s).",
        blocker_code="RAILWAY_TARGET_SERVICE_MISSING",
    )


def _step_env_readiness(checks: dict[str, Any], settings: Any) -> ExecutionStepResult:
    creation = checks.get("service_creation") or {}
    env_writes = bool(creation.get("env_var_writes_enabled"))
    if not settings.provider_env_var_mutations_enabled:
        return ExecutionStepResult(
            step_id="railway.check_env_readiness",
            label="Check env readiness",
            status="completed",
            detail="Env var writes disabled — keys will be reported at preflight.",
        )
    return ExecutionStepResult(
        step_id="railway.check_env_readiness",
        label="Check env readiness",
        status="completed",
        detail="Env readiness will be assessed during governed orchestration (values never shown).",
    )


def _step_mutation_gate(settings: Any) -> ExecutionStepResult:
    if settings.mutation_execution_enabled:
        return ExecutionStepResult(
            step_id="railway.mutation_gate",
            label="Check mutation readiness",
            status="completed",
            detail="Mutation execution gate is enabled.",
        )
    return ExecutionStepResult(
        step_id="railway.mutation_gate",
        label="Check mutation readiness",
        status="completed",
        detail=(
            "MUTATION_EXECUTION_ENABLED is false — I can still create a governed preflight, "
            "but execution requires runtime approval and enabling the mutation gate."
        ),
    )


def _step_create_preflight(
    user_text: str,
    *,
    session_id: str,
    checks: dict[str, Any],
) -> ExecutionStepResult:
    if not get_settings().provider_e2e_orchestration_enabled:
        return ExecutionStepResult(
            step_id="railway.create_deploy_preflight",
            label="Create deploy preflight",
            status="blocked",
            detail="Provider E2E orchestration is disabled.",
            blocker_code="E2E_ORCHESTRATION_DISABLED",
        )

    if not checks.get("railway_credential_ok") or not checks.get("railway_api_connection_ok"):
        from aethos_core.provider_e2e_readiness.blocker_mapping import (
            is_auth_rejection_detail,
            is_rate_limited_detail,
        )

        conn_detail = str(checks.get("railway_api_connection_detail") or "")
        status_code = checks.get("railway_api_connection_status_code")
        if not checks.get("railway_credential_ok"):
            blocker_code = "RAILWAY_TOKEN_MISSING"
            detail = "A Railway token must be configured before preflight."
        elif checks.get("railway_api_connection_rate_limited") or is_rate_limited_detail(conn_detail, status_code=status_code):
            blocker_code = "RAILWAY_RATE_LIMITED"
            detail = "Railway API is rate-limiting requests (transient) — token is valid. Retry shortly."
        elif is_auth_rejection_detail(conn_detail, status_code=status_code):
            blocker_code = "RAILWAY_TOKEN_INVALID"
            detail = "Connection must pass before preflight."
        else:
            blocker_code = "RAILWAY_API_CONNECTION_FAILED"
            detail = conn_detail or "Connection must pass before preflight."
        return ExecutionStepResult(
            step_id="railway.create_deploy_preflight",
            label="Create deploy preflight",
            status="blocked",
            detail=detail,
            blocker_code=blocker_code,
        )

    from aethos_core.provider_e2e_execution.railway_e2e_execution import route_railway_e2e_execution

    routed = route_railway_e2e_execution(user_text, session_id=session_id)
    if routed is None:
        return ExecutionStepResult(
            step_id="railway.create_deploy_preflight",
            label="Create deploy preflight",
            status="blocked",
            detail="E2E route did not match.",
            blocker_code="E2E_ROUTE_FAILED",
        )

    body, intent, meta = routed
    if intent == "railway_e2e_orchestration_preflight":
        return ExecutionStepResult(
            step_id="railway.create_deploy_preflight",
            label="Create deploy preflight",
            status="awaiting_approval",
            detail="Governed orchestration preflight created.",
            evidence={"job_id": meta.get("job_id", ""), "intent": intent, "preflight_body": body[:240]},
        )

    return ExecutionStepResult(
        step_id="railway.create_deploy_preflight",
        label="Create deploy preflight",
        status="blocked",
        detail="Preflight could not be created — configuration still incomplete.",
        blocker_code="RAILWAY_TARGET_SERVICE_MISSING",
    )


def _finalize_multi_target_plan(
    plan: ExecutionPlanResult,
    checks: dict[str, Any],
    *,
    goal: ExecutionGoal,
    targets: list[tuple[str, str, str]],
    session_id: str,
) -> ExecutionPlanResult:
    from aethos_core.provider_e2e_execution.railway_e2e_execution import _route_multi_target_railway_e2e

    routed = _route_multi_target_railway_e2e(
        goal.user_text,
        checks=checks,
        settings=get_settings(),
        targets=targets,
        session_id=session_id,
    )
    if routed is None:
        return plan
    body, intent, meta = routed
    job_ids = [part.strip() for part in str(meta.get("proposed_job_ids") or meta.get("job_id") or "").split(",") if part.strip()]

    plan.steps.append(
        ExecutionStepResult(
            step_id="railway.discover_services",
            label="Discover target services",
            status="completed",
            detail=f"Resolved {len(targets)} Railway target(s).",
        )
    )
    plan.steps.append(
        ExecutionStepResult(
            step_id="railway.create_deploy_preflight",
            label="Create deploy prefights",
            status="awaiting_approval",
            detail="Governed redeploy prefights created for each selected service.",
            evidence={"preflight_body": body[:400], "intent": intent, "target_count": str(len(targets))},
        )
    )
    plan.awaiting_approval = True
    plan.job_id = job_ids[0] if job_ids else ""
    plan.recovery_summary = body
    plan.completion_ready = True
    plan.next_executable_step = "Approve each preflight in Mission Control → Jobs, then execute redeploy."
    update_execution_memory(
        session_id=session_id,
        goal=goal.user_text,
        provider="railway",
        step_completed="railway.create_deploy_preflight",
        job_id=plan.job_id,
    )
    return plan


def _finalize_blocked(
    plan: ExecutionPlanResult,
    checks: dict[str, Any],
    settings: Any,
    *,
    session_id: str,
    failed_step: ExecutionStepResult,
    user_text: str = "",
) -> ExecutionPlanResult:
    blockers = map_railway_blockers(
        checks,
        settings=settings,
        target_resolved=False if failed_step.blocker_code == "RAILWAY_TARGET_SERVICE_MISSING" else None,
        include_mutation_gates=failed_step.blocker_code == "MUTATION_EXECUTION_DISABLED",
    )
    if not blockers and failed_step.blocker_code:
        from aethos_core.provider_e2e_readiness.blocker_mapping import ReadinessBlocker

        blockers = [
            ReadinessBlocker(
                code=failed_step.blocker_code,
                meaning=failed_step.detail,
                required_action="Resolve the reported issue and retry.",
                safe_next_command="validate Railway connection",
            )
        ]
    plan.blockers = [b.code for b in blockers]
    if failed_step.blocker_code == "RAILWAY_TARGET_SERVICE_MISSING":
        from aethos_core.providers.railway.railway_inventory_target_picker import pick_railway_targets
        from aethos_core.task_frame.railway_deploy_selection import store_railway_deploy_selection_task

        picked = pick_railway_targets(checks, user_text or plan.goal_summary)
        if picked.candidates:
            store_railway_deploy_selection_task(
                session_id=session_id,
                user_text=user_text or plan.goal_summary,
                checks=checks,
                candidates=picked.candidates,
            )
    plan.recovery_summary = compose_blocked_plan_reply(plan=plan, blockers=blockers, provider="railway")
    update_execution_memory(
        session_id=session_id,
        goal=plan.goal_summary,
        provider="railway",
        failure_code=plan.blockers[0] if plan.blockers else failed_step.blocker_code,
    )
    return plan


def _redact_checks(checks: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.provider_e2e_execution.composer import redact_checks_snapshot

    return redact_checks_snapshot(checks)

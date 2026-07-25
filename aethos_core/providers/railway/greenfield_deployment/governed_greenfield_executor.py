# SPDX-License-Identifier: Apache-2.0
"""Governed Railway greenfield execution after Mission Control preflight approval."""

from __future__ import annotations

import time
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_journal import get_or_create_execution_journal
from aethos_core.providers.railway.execution_contract.execution_real_mutation_dispatch import (
    run_single_real_mutation_phase,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.credential_truth import resolve_railway_credential
from aethos_core.security.secret_redaction import redact_text


def is_governed_railway_greenfield_orchestration(params: dict[str, Any]) -> bool:
    return (
        params.get("greenfield") is True
        and str(params.get("flow") or "") == "railway_greenfield_deployment"
        and str(params.get("provider") or "").strip().lower() == "railway"
    )


def build_governed_greenfield_execution_policy(
    *,
    plan: dict[str, Any],
    user_text: str = "",
    mc_preflight_approved: bool = False,
) -> RailwayExecutionEnablementPolicy:
    """Execution policy for MC-approved greenfield — preflight approval waives final phrase."""
    base = assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)
    if not mc_preflight_approved:
        return base

    filtered_reasons = [
        reason
        for reason in base.blocking_reasons
        if reason not in {"final_phrase_missing", "final_phrase_invalid"}
    ]
    filtered_messages = [
        message
        for message in base.blocking_reason_messages
        if "Final governed execution approval phrase" not in message
        and "phrase does not match" not in message
    ]
    allowed = base.target_loaded and base.mode != "disabled" and base.allowlist_passed
    if base.mode == "enabled" and not base.greenfield_execution_enabled:
        allowed = False
    if filtered_reasons and base.mode == "enabled":
        allowed = False

    return RailwayExecutionEnablementPolicy(
        mode=base.mode,
        greenfield_execution_enabled=base.greenfield_execution_enabled,
        allowed=allowed,
        dry_run_only=base.dry_run_only,
        production_allowed=base.production_allowed,
        final_phrase_required=base.final_phrase_required,
        final_phrase_provided=base.final_phrase_provided or True,
        final_phrase_valid=True if base.final_phrase_required else base.final_phrase_valid,
        target_project=base.target_project,
        target_environment=base.target_environment,
        target_service=base.target_service,
        is_production=base.is_production,
        allowlist_passed=base.allowlist_passed,
        target_loaded=base.target_loaded,
        next_step=base.next_step,
        blocking_reasons=filtered_reasons,
        blocking_reason_messages=filtered_messages,
    )


def run_governed_railway_greenfield_orchestration(
    *,
    job_id: str,
    params: dict[str, Any],
) -> tuple[str, str, bool, dict[str, Any]]:
    """
    Run governed greenfield phases (create → connect → env → deploy → verify).

    Returns (summary, full_result, executed, artifact).
    """
    from aethos_core.runtime.jobs import job_store

    plan, user_text, session_id, preflight_id, preflight_job_id = _load_execution_context(params)
    if not plan.get("repo"):
        detail = "Greenfield target plan missing repository — cannot execute governed phases."
        return detail, detail, False, {"execution_status": "blocked", "failure_state": "missing_target_plan"}

    credential = resolve_railway_credential()
    if not credential.ok:
        detail = credential.detail or "Railway API token not available."
        return detail, detail, False, {
            "execution_status": "blocked",
            "failure_state": "missing_provider_token",
            "credential_resolution": {
                "source": credential.source,
                "detail": credential.detail,
                "env_present": credential.env_present,
            },
        }

    env_report = dict(params.get("required_env_var_report") or {})
    from aethos_core.providers.railway.env_value_readiness.deployment_env_guidance import (
        assess_deployment_env_for_plan,
        compose_deployment_env_block_report,
    )

    env_assessment = assess_deployment_env_for_plan(plan=plan, env_report=env_report)
    if env_assessment.missing_names:
        summary, full = compose_deployment_env_block_report(env_assessment)
        return summary, full, False, {
            "execution_status": "blocked",
            "failure_state": "missing_secure_store_env",
            "deployment_env_assessment": env_assessment.to_dict(),
            "missing_env_names": list(env_assessment.missing_names),
        }

    policy = build_governed_greenfield_execution_policy(
        plan=plan,
        user_text=user_text,
        mc_preflight_approved=bool(params.get("provider_e2e_approved")),
    )
    if not policy.allows_real_mutation():
        detail = (
            "; ".join(policy.blocking_reason_messages[:4])
            or "Railway greenfield execution policy blocked real mutation."
        )
        return detail, detail, False, {
            "execution_status": "blocked",
            "failure_state": "execution_policy_blocked",
            "execution_enablement": {
                "mode": policy.mode,
                "blockers": list(policy.blocking_reasons),
                "messages": list(policy.blocking_reason_messages),
            },
        }

    job_store.emit_progress(job_id, "Running governed Railway greenfield phases…")
    journal, _created = get_or_create_execution_journal(
        plan=plan,
        session_id=session_id,
        initial_state="execution_locked",
        approval={
            "mode": "mission_control_preflight",
            "preflight_id": preflight_id,
            "job_id": preflight_job_id,
            "orchestration_job_id": job_id,
        },
    )
    if not journal.get("rollback_journal"):
        journal = attach_rollback_journal(journal)

    journal, execution_status, blocker = _run_governed_phase_loop(
        job_id=job_id,
        journal=journal,
        plan=plan,
        policy=policy,
        user_text=user_text,
    )

    artifact: dict[str, Any] = {
        "execution_status": execution_status,
        "greenfield_execution": True,
        "journal": _safe_journal(journal),
        "credential_source": credential.source,
    }
    if blocker:
        detail = str(blocker.get("detail") or "Governed greenfield execution failed.")
        artifact["failure_state"] = str(blocker.get("code") or "greenfield_execution_failed")
        artifact["required_action"] = str(blocker.get("required_action") or "")
        full = _compose_failure_report(plan=plan, journal=journal, blocker=blocker, credential=credential)
        return detail, redact_text(full), False, artifact

    service = str(journal.get("service_name") or plan.get("service_name") or "")
    url = str(journal.get("deployment_url") or "")
    summary = f"Governed Railway greenfield deployment completed for `{service}`."
    if url:
        summary += f" Deployment URL: {url}"
    full = _compose_success_report(plan=plan, journal=journal, credential=credential)
    artifact["mutating"] = True
    artifact["executed"] = True
    return summary, redact_text(full), True, artifact


def _load_execution_context(params: dict[str, Any]) -> tuple[dict[str, Any], str, str, str, str]:
    from aethos_core.runtime.jobs import job_store

    plan = dict(params.get("target_plan") or {})
    parent_id = str(params.get("parent_greenfield_job_id") or "")
    if parent_id and not plan.get("repo"):
        parent = job_store.get(parent_id)
        if parent:
            parent_params = dict(parent.params or {})
            plan = dict(parent_params.get("target_plan") or plan)
            params.setdefault("required_env_var_report", parent_params.get("required_env_var_report"))
            params.setdefault("git_remote_resolution_report", parent_params.get("git_remote_resolution_report"))

    user_text = str(params.get("user_request") or "")
    session_id = str(params.get("session_id") or "default")
    preflight_id = str(params.get("preflight_id") or "")
    preflight_job_id = parent_id or str(params.get("parent_greenfield_job_id") or "")
    return plan, user_text, session_id, preflight_id, preflight_job_id


def _run_governed_phase_loop(
    *,
    job_id: str,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy,
    user_text: str,
    max_steps: int = 36,
) -> tuple[dict[str, Any], str, dict[str, str] | None]:
    from aethos_core.runtime.jobs import job_store

    current = dict(journal)
    last_idempotent_detail = ""
    for step in range(max_steps):
        result = run_single_real_mutation_phase(
            journal=current,
            plan=plan,
            policy=policy,
            user_text=user_text,
        )
        current = dict(result.journal or current)
        if result.mutation_performed or result.detail:
            job_store.emit_progress(
                job_id,
                f"Greenfield phase — {result.detail or 'step complete'}",
            )

        verification = (
            current.get("runtime_verification")
            if isinstance(current.get("runtime_verification"), dict)
            else {}
        )
        if verification.get("verified") or (
            current.get("runtime_verification_performed") and verification.get("ok")
        ):
            return current, "completed", None

        if result.policy_blocked or result.errors:
            code = str((result.errors or ["GREENFIELD_PHASE_BLOCKED"])[0])
            detail = str(result.detail or "")
            if any(token in detail.lower() for token in ("building", "deploying", "initializing", "pending")):
                time.sleep(8)
                continue
            return current, "failed", {
                "code": code,
                "detail": detail or "Governed greenfield phase blocked.",
                "required_action": "Resolve the blocker in Mission Control and retry.",
                "safe_next_command": user_text,
            }

        if result.idempotent_replay and not result.mutation_performed:
            signature = str(result.detail or "")
            if signature and signature == last_idempotent_detail:
                return current, "failed", {
                    "code": "GREENFIELD_IDEMPOTENT_STALL",
                    "detail": "Governed greenfield execution stalled on repeated idempotent phase replay.",
                    "required_action": "Clear the stale execution journal or retry with a fresh session.",
                    "safe_next_command": user_text,
                }
            last_idempotent_detail = signature

        if result.idempotent_replay and current.get("runtime_verification_performed"):
            return current, "completed", None

        if step == max_steps - 1:
            break

    return current, "failed", {
        "code": "GREENFIELD_EXECUTION_STEP_LIMIT",
        "detail": "Governed greenfield execution exceeded the phase step limit.",
        "required_action": "Check Mission Control execution journal and retry.",
        "safe_next_command": user_text,
    }


def _compose_success_report(
    *,
    plan: dict[str, Any],
    journal: dict[str, Any],
    credential,
) -> str:
    lines = [
        "# Railway greenfield execution completed",
        "",
        f"- Service: `{journal.get('service_name') or plan.get('service_name')}`",
        f"- Project: `{journal.get('project') or plan.get('project')}`",
        f"- Environment: `{journal.get('environment') or plan.get('environment')}`",
        f"- Repository: `{plan.get('repo')}` @ `{plan.get('branch')}`",
        f"- Credential: {credential.source}",
    ]
    if journal.get("deployment_url"):
        lines.append(f"- Deployment URL: {journal.get('deployment_url')}")
    if journal.get("railway_service_id"):
        lines.append(f"- Railway service id: `{journal.get('railway_service_id')}`")
    return "\n".join(lines)


def _compose_failure_report(
    *,
    plan: dict[str, Any],
    journal: dict[str, Any],
    blocker: dict[str, str],
    credential,
) -> str:
    lines = [
        "# Railway greenfield execution failed",
        "",
        f"- Blocker: `{blocker.get('code')}`",
        f"- Detail: {blocker.get('detail')}",
        f"- Target: `{plan.get('service_name')}` in `{plan.get('project')}` / `{plan.get('environment')}`",
        f"- Credential: {credential.source}",
    ]
    if blocker.get("required_action"):
        lines.extend(["", f"**Required action:** {blocker['required_action']}"])
    if journal.get("state"):
        lines.append(f"- Journal state: `{journal.get('state')}`")
    return "\n".join(lines)


def _safe_journal(journal: dict[str, Any]) -> dict[str, Any]:
    return {
        k: journal.get(k)
        for k in (
            "execution_id",
            "project",
            "environment",
            "service_name",
            "railway_service_id",
            "railway_deployment_id",
            "deployment_url",
            "runtime_verification_performed",
            "state",
        )
    }

# SPDX-License-Identifier: Apache-2.0
"""Solo Vercel greenfield — block when build-critical env is missing; explain like an operator."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.greenfield_deployment.greenfield_flow import VercelGreenfieldFlowResult
from aethos_core.providers.vercel.greenfield_deployment.greenfield_preflight import approve_vercel_greenfield_preflight
from aethos_core.solo_execution.solo_execution_mode import is_solo_execution_mode_enabled, validate_solo_greenfield_eligibility


def maybe_run_solo_vercel_greenfield_execution(
    *,
    user_text: str,
    session_id: str,
    plan: dict[str, Any],
    env_report: dict[str, Any],
    git_remote: dict[str, Any],
    local_source: dict[str, Any],
    inspection: dict[str, Any],
    preflight_job_id: str,
    preflight_id: str,
    local_report: str,
    git_report: str,
    env_report_text: str,
    target_report: str,
) -> VercelGreenfieldFlowResult | None:
    if not is_solo_execution_mode_enabled():
        return None

    from aethos_core.config import get_settings

    settings = get_settings()
    allowed = {p.strip().lower() for p in (settings.aethos_solo_allowed_providers or "").split(",") if p.strip()}
    scope = str(settings.aethos_solo_execution_provider or "").strip().lower()
    if scope and scope != "vercel" and "vercel" not in allowed:
        return None

    eligibility = validate_solo_greenfield_eligibility(
        plan={**plan, "environment": plan.get("environment") or "production", "framework": plan.get("framework") or inspection.get("framework") or "nextjs"},
        env_report=env_report,
        git_remote=git_remote,
        provider="vercel",
        user_text=user_text,
    )
    if not eligibility.ok:
        return VercelGreenfieldFlowResult(
            ok=False,
            blocked=True,
            blocker_code=eligibility.blocker_code or "SOLO_EXECUTION_BLOCKED",
            blocker_detail=eligibility.detail,
            reply=_blocked_reply(eligibility, plan=plan, env_report=env_report, inspection=inspection),
            intent="vercel_greenfield_deployment_blocked",
        )

    try:
        _, meta = approve_vercel_greenfield_preflight(preflight_job_id, session_id=session_id)
    except Exception as exc:
        return VercelGreenfieldFlowResult(
            ok=False,
            blocked=True,
            blocker_code="SOLO_VERCEL_APPROVAL_FAILED",
            blocker_detail=str(exc),
            reply=f"Vercel solo execution blocked during approval: {exc}",
            intent="vercel_greenfield_deployment_blocked",
        )

    orch_id = str(meta.get("orchestration_job_id") or "")
    sections = [
        "Vercel greenfield deployment — solo execution started",
        "",
        local_report,
        "",
        git_report,
        "",
        env_report_text,
        "",
        target_report,
        "",
        f"Preflight `{preflight_id}` approved.",
        f"Orchestration job `{orch_id}` queued (env → deploy → verify).",
        "",
        "If build-critical env vars are missing, deploy will stop with a completion plan instead of a broken build.",
        "",
        "Track progress in Mission Control → Jobs.",
    ]
    return VercelGreenfieldFlowResult(
        ok=True,
        blocked=False,
        reply="\n".join(sections),
        intent="vercel_greenfield_deployment_solo_started",
        preflight_job_id=preflight_job_id,
        artifacts={"orchestration_job_id": orch_id, "plan": plan},
    )


def _blocked_reply(eligibility, *, plan: dict[str, Any], env_report: dict[str, Any], inspection: dict[str, Any]) -> str:
    from aethos_core.provider_e2e_orchestration.e2e_completion_advisor import (
        build_e2e_completion_advisory,
        compose_completion_advisory_report,
    )
    from aethos_core.provider_e2e_orchestration.job_model import ProviderE2EJobModel

    model = ProviderE2EJobModel(
        provider="vercel",
        project_name=str(plan.get("project_name") or plan.get("project") or ""),
        env_var_names=list(env_report.get("required_env_var_names") or []),
    )
    params = {
        "target_plan": plan,
        "inspection": inspection,
        "env_var_names": list(env_report.get("required_env_var_names") or []),
        "framework": plan.get("framework") or inspection.get("framework") or "nextjs",
    }
    env_exec = {
        "applied_names": [],
        "failed_names": list(eligibility.missing_env_names or []),
        "all_required_names": list(env_report.get("required_env_var_names") or []),
        "all_detected_env_var_names": list(env_report.get("all_detected_env_var_names") or []),
    }
    advisory = build_e2e_completion_advisory(
        model=model,
        params=params,
        env_report=env_exec,
        poll_report={},
        redeploy_report={},
        execution_status="env_failed",
    )
    lines = [
        "Vercel greenfield deployment blocked — I won't ship a broken build.",
        "",
        f"**Reason:** `{eligibility.blocker_code}`",
    ]
    if eligibility.detail:
        lines.append(f"- {eligibility.detail}")
    lines.extend(["", compose_completion_advisory_report(advisory)])
    return "\n".join(lines)

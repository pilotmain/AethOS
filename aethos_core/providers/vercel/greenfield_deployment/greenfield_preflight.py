# SPDX-License-Identifier: Apache-2.0
"""Vercel greenfield preflight job."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.runtime.authority import authority

VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE = "vercel_greenfield_deployment_preflight"


def create_vercel_greenfield_preflight_job(
    *,
    user_text: str,
    session_id: str,
    plan: dict[str, Any],
    env_report: dict[str, Any],
    local_source: dict[str, Any],
    git_remote: dict[str, Any],
    credential_id: str = "",
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.vercel_greenfield_execution_enabled:
        return {"ok": False, "error": "vercel_greenfield_execution_disabled"}

    preflight_id = f"vgf-{uuid.uuid4().hex[:12]}"
    job_params = {
        "provider": "vercel",
        "flow": "vercel_greenfield_deployment",
        "session_id": session_id,
        "user_request": user_text,
        "preflight_id": preflight_id,
        "target_plan": plan,
        "required_env_var_names": list(env_report.get("required_env_var_names") or []),
        "credential_id": credential_id,
        "referenced_github_repo": str(git_remote.get("repository") or plan.get("repo") or ""),
        "local_workspace": local_source,
        "git_remote": git_remote,
        "inspection": {
            "required_env_var_names": list(env_report.get("required_env_var_names") or []),
            "framework": str(plan.get("framework") or "nextjs"),
            "runtime": str(plan.get("runtime") or "unknown"),
        },
        "orchestration_steps": [
            f"Link GitHub repo `{plan.get('repo')}` to Vercel project `{plan.get('project_name')}`",
            f"Configure {env_report.get('count', 0)} env var(s) via secure references",
            "Trigger production deploy and collect evidence",
        ],
        "approval_required": True,
        "mutation_performed": False,
    }

    job = authority.create_job(
        title=f"Vercel greenfield: {plan.get('project_name')} from {plan.get('repo')}",
        job_type=VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
        params=job_params,
        source="chat",
        session_id=session_id,
        auto_run=False,
    )

    from aethos_core.jobs.session_approval_target import record_session_approval_target

    record_session_approval_target(
        session_id=session_id,
        job_id=job.id,
        job_type=VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
        provider="vercel",
        action_type="link_repo_env_deploy_verify",
        preflight_id=preflight_id,
    )

    return {
        "ok": True,
        "job_id": job.id,
        "preflight_id": preflight_id,
        "job_type": VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
        "created_at": datetime.now(UTC).isoformat(),
    }


def compose_vercel_greenfield_preflight_reply(*, job_id: str, plan: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Vercel greenfield deployment preflight is ready.",
            "",
            f"Target project: `{plan.get('project_name')}`",
            f"Repository: `{plan.get('repo')}` @ `{plan.get('branch')}`",
            "",
            f"Approve in Mission Control to proceed (job `{job_id}`).",
        ]
    )


def build_orchestration_params_from_vercel_greenfield_preflight(
    preflight_params: dict[str, Any],
    *,
    greenfield_job_id: str,
) -> dict[str, Any]:
    from aethos_core.provider_e2e_orchestration.job_model import enrich_job_params_for_orchestration

    plan = dict(preflight_params.get("target_plan") or {})
    env_names = list(preflight_params.get("required_env_var_names") or [])
    return enrich_job_params_for_orchestration(
        {
            "provider": "vercel",
            "session_id": preflight_params.get("session_id"),
            "user_request": preflight_params.get("user_request"),
            "preflight_id": preflight_params.get("preflight_id"),
            "parent_greenfield_job_id": greenfield_job_id,
            "flow": "vercel_greenfield_deployment",
            "action_type": "link_repo_env_deploy_verify",
            "greenfield": True,
            "project_name": plan.get("project_name") or plan.get("project"),
            "project_id": plan.get("project_id") or "",
            "credential_id": preflight_params.get("credential_id") or "",
            "referenced_github_repo": preflight_params.get("referenced_github_repo") or plan.get("repo"),
            "github_repo_id": plan.get("github_repo_id"),
            "branch": plan.get("branch") or "main",
            "target": {"project_name": plan.get("project_name") or plan.get("project"), "project_id": plan.get("project_id") or ""},
            "env_var_names": env_names,
            "framework": plan.get("framework") or "other",
            "target_plan": plan,
            "inspection": preflight_params.get("inspection") if isinstance(preflight_params.get("inspection"), dict) else {},
            "orchestration_steps": list(preflight_params.get("orchestration_steps") or []),
            "deploy_action": "redeploy",
        }
    )


def approve_vercel_greenfield_preflight(
    job_id: str,
    *,
    session_id: str | None = None,
    remembered: dict[str, Any] | None = None,
    spawn_orchestration: bool = True,
) -> tuple[Any, dict[str, Any]]:
    from aethos_core.jobs.session_approval_target import mark_session_approval_mutation_performed
    from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
    from aethos_core.provider_e2e_orchestration.approval_flow import approve_provider_e2e_orchestration
    from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_gate import (
        GreenfieldApprovalError,
        validate_greenfield_approval_gate,
    )
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    gate = validate_greenfield_approval_gate(job, session_id=session_id, remembered=remembered)
    if not gate.ok:
        raise GreenfieldApprovalError(gate)

    params = dict(job.params or {})
    approval_id = f"vgf-approval-{job_id}-{int(datetime.now(UTC).timestamp())}"
    job.params["greenfield_preflight_approved"] = True
    job.params["approval_id"] = approval_id
    job.params["execution_status"] = "approved"
    job.params["greenfield_preflight_approved_at_iso"] = datetime.now(UTC).isoformat()

    if session_id:
        mark_session_approval_mutation_performed(session_id=session_id, job_id=job_id)

    if not spawn_orchestration:
        return job, {"approval_id": approval_id, "preflight_id": params.get("preflight_id"), "spawn_orchestration": False}

    orch_params = build_orchestration_params_from_vercel_greenfield_preflight(params, greenfield_job_id=job_id)
    orch_job = authority.create_job(
        title=f"Vercel greenfield execution: {orch_params.get('project_name')}",
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        params=orch_params,
        source="greenfield_preflight",
        session_id=str(getattr(job, "session_id", "") or session_id or "default"),
        auto_run=False,
    )
    job.params["orchestration_job_id"] = orch_job.id
    orch_job, orch_meta = approve_provider_e2e_orchestration(orch_job.id)
    return job, {
        "approval_id": approval_id,
        "preflight_id": params.get("preflight_id"),
        "orchestration_job_id": orch_job.id,
        "orchestration_gate": orch_meta.get("gate"),
        "spawn_orchestration": True,
    }

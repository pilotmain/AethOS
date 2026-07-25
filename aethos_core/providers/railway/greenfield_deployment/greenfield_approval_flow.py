# SPDX-License-Identifier: Apache-2.0
"""Approve Railway greenfield preflight jobs — spawn governed orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
from aethos_core.provider_e2e_orchestration.approval_flow import approve_provider_e2e_orchestration
from aethos_core.provider_e2e_orchestration.job_model import enrich_job_params_for_orchestration
from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_gate import (
    GreenfieldApprovalError,
    validate_greenfield_approval_gate,
)


def build_orchestration_params_from_greenfield_preflight(
    preflight_params: dict[str, Any],
    *,
    greenfield_job_id: str,
) -> dict[str, Any]:
    plan = dict(preflight_params.get("target_plan") or {})
    env_report = dict(preflight_params.get("required_env_var_report") or {})
    health_path = str(plan.get("health_check_path") or "")
    if health_path.lower() == "unknown":
        health_path = ""

    return enrich_job_params_for_orchestration(
        {
            "provider": "railway",
            "session_id": preflight_params.get("session_id"),
            "user_request": preflight_params.get("user_request"),
            "preflight_id": preflight_params.get("preflight_id"),
            "parent_greenfield_job_id": greenfield_job_id,
            "flow": "railway_greenfield_deployment",
            "action_type": "create_project_service_env_deploy_verify",
            "greenfield": True,
            "target_plan": dict(preflight_params.get("target_plan") or {}),
            "required_env_var_report": dict(preflight_params.get("required_env_var_report") or {}),
            "git_remote_resolution_report": dict(preflight_params.get("git_remote_resolution_report") or {}),
            "project_name": plan.get("project"),
            "service_name": plan.get("service_name"),
            "environment": plan.get("environment"),
            "target": {
                "project_name": plan.get("project"),
                "environment_name": plan.get("environment"),
                "service_name": plan.get("service_name"),
            },
            "env_var_names": list(env_report.get("required_env_var_names") or []),
            "health_check_url": health_path,
            "orchestration_steps": list(preflight_params.get("orchestration_steps") or []),
            "deploy_action": "none",
        }
    )


def approve_railway_greenfield_preflight(
    job_id: str,
    *,
    session_id: str | None = None,
    remembered: dict[str, Any] | None = None,
    spawn_orchestration: bool = True,
) -> tuple[Any, dict[str, Any]]:
    """Validate gates, stamp greenfield approval, optionally spawn + approve orchestration."""
    from aethos_core.jobs.session_approval_target import mark_session_approval_mutation_performed
    from aethos_core.runtime.authority import authority
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    gate = validate_greenfield_approval_gate(job, session_id=session_id, remembered=remembered)
    if not gate.ok:
        raise GreenfieldApprovalError(gate)

    params = dict(job.params or {})
    approval_id = f"rgf-approval-{job_id}-{int(datetime.now(UTC).timestamp())}"
    job.params["greenfield_preflight_approved"] = True
    job.params["approval_id"] = approval_id
    job.params["execution_status"] = "approved"
    job.params["greenfield_preflight_approved_at_iso"] = datetime.now(UTC).isoformat()
    job.params["solo_execution_approved"] = not spawn_orchestration

    if session_id:
        mark_session_approval_mutation_performed(session_id=session_id, job_id=job_id)

    if not spawn_orchestration:
        return job, {
            "approval_id": approval_id,
            "preflight_id": params.get("preflight_id"),
            "spawn_orchestration": False,
        }

    orch_params = build_orchestration_params_from_greenfield_preflight(params, greenfield_job_id=job_id)
    orch_job = authority.create_job(
        title=f"Railway greenfield execution: {orch_params.get('service_name')}",
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

# SPDX-License-Identifier: Apache-2.0
"""Phase 5 — governed Railway greenfield preflight job (approval required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.provider_e2e_execution.composer import redact_checks_snapshot
from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import normalize_plan_for_artifact
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    assess_railway_execution_enablement_policy,
)
from aethos_core.runtime.authority import authority

RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE = "railway_greenfield_deployment_preflight"


def create_railway_greenfield_preflight_job(
    *,
    user_text: str,
    session_id: str,
    plan: dict[str, Any],
    env_report: dict[str, Any],
    local_source: dict[str, Any],
    git_remote: dict[str, Any],
    railway_checks: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create Mission Control preflight job — no Railway mutations."""
    settings = get_settings()
    normalized_plan = normalize_plan_for_artifact({**plan, **env_report})
    enablement = assess_railway_execution_enablement_policy(plan=normalized_plan, user_text=user_text)

    steps = [
        "Validate Railway credential (complete)",
        f"Create Railway project `{plan.get('project')}` if needed (approval required)",
        f"Create service `{plan.get('service_name')}` from `{plan.get('repo')}` @ `{plan.get('branch')}`",
        "Attach GitHub source binding to service",
        f"Configure {env_report.get('count', 0)} env var(s) via secure references (names only in audit)",
        "Trigger governed deploy (approval required)",
        "Poll deployment status and collect log evidence",
        f"Verify health endpoint `{plan.get('health_check_path')}` and produce final report",
    ]

    rollback = [
        "Disconnect GitHub source binding if creation succeeded but deploy failed",
        "Revert env var writes via governed rollback contract",
        "Archive failed service or mark for manual cleanup in Mission Control",
    ]

    preflight_id = f"rgf-{uuid.uuid4().hex[:12]}"
    job_params = {
        "provider": "railway",
        "flow": "railway_greenfield_deployment",
        "session_id": session_id,
        "user_request": user_text,
        "preflight_id": preflight_id,
        "target_plan": normalized_plan,
        "local_workspace_deployment_source_report": _safe_local_source(local_source),
        "git_remote_resolution_report": _safe_git_remote(git_remote),
        "required_env_var_report": {
            "required_env_var_names": list(env_report.get("required_env_var_names") or []),
            "secure_references": list(env_report.get("secure_references") or []),
            "count": env_report.get("count", 0),
        },
        "orchestration_steps": steps,
        "rollback_plan": rollback,
        "blast_radius": {
            "creates_new_project": True,
            "creates_new_service": True,
            "env_var_names": list(env_report.get("required_env_var_names") or []),
            "risk_tier": plan.get("risk_tier"),
        },
        "execution_enablement": {
            "mode": enablement.mode,
            "allowed": enablement.allowed,
            "blockers": list(enablement.blocking_reason_messages or [])[:8],
        },
        "checks_snapshot": redact_checks_snapshot(railway_checks or {}),
        "mutation_execution_enabled": settings.mutation_execution_enabled,
        "provider_env_var_mutations_enabled": settings.provider_env_var_mutations_enabled,
        "approval_required": True,
        "mutation_performed": False,
    }

    job = authority.create_job(
        title=f"Railway greenfield: {plan.get('service_name')} from {plan.get('repo')}",
        job_type=RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
        params=job_params,
        source="chat",
        session_id=session_id,
        auto_run=False,
    )

    from aethos_core.jobs.session_approval_target import record_session_approval_target

    record_session_approval_target(
        session_id=session_id,
        job_id=job.id,
        job_type=RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
        provider="railway",
        action_type="create_project_service_env_deploy_verify",
        preflight_id=preflight_id,
    )

    return {
        "ok": True,
        "preflight_id": preflight_id,
        "job_id": job.id,
        "job_type": RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
        "approval_path": mutation_approval_surface(),
        "steps": steps,
        "rollback_plan": rollback,
        "enablement": enablement,
        "plan": normalized_plan,
        "created_at": datetime.now(UTC).isoformat(),
    }


def compose_greenfield_preflight_reply(
    *,
    preflight: dict[str, Any],
    local_report: str,
    git_report: str,
    target_report: str,
    env_report_text: str,
) -> str:
    plan = dict(preflight.get("plan") or {})
    enablement = preflight.get("enablement")
    blockers = list(getattr(enablement, "blocking_reason_messages", None) or [])
    execution_ready = False
    if enablement is not None and hasattr(enablement, "allows_real_mutation"):
        execution_ready = bool(enablement.allows_real_mutation())
    elif isinstance(enablement, dict):
        execution_ready = bool(enablement.get("allowed"))
    lines = [
        "**Railway greenfield deployment flow**",
        "",
        "Detected a **new project / local workspace** deployment — not an existing-service redeploy.",
        "",
        local_report,
        "",
        git_report,
        "",
        target_report,
        "",
        env_report_text,
        "",
        "### Governed preflight",
        f"- Preflight ID: `{preflight.get('preflight_id')}`",
        f"- Mission Control job: `{preflight.get('job_id')}`",
    ]
    if execution_ready:
        lines.append("- Approval: **required** before any Railway mutation")
    else:
        lines.extend(
            [
                "- Mode: **planning only** — deploy plan and preflight recorded; no Railway mutations yet.",
                "- To actually deploy: enable **Railway greenfield execution** in operator settings "
                "(`railway_greenfield_execution_enabled` and related flags), then approve in "
                "**Mission Control → Approvals**.",
            ]
        )
    lines.append("")
    lines.append("**Planned steps:**")
    for idx, step in enumerate(list(preflight.get("steps") or []), start=1):
        lines.append(f"{idx}. {step}")
    if blockers:
        lines.extend(["", "**Execution enablement notes (preflight still created):**"])
        for msg in blockers[:6]:
            lines.append(f"- {msg}")
    lines.extend(
        [
            "",
            f"Review job `{preflight.get('job_id')}` in **{preflight.get('approval_path')}**.",
            "No secret values are shown."
            + (
                " No Railway mutation has been executed."
                if execution_ready
                else " This turn completed in planning mode — no deploy is waiting for approval."
            ),
        ]
    )
    return "\n".join(lines)


def _safe_local_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        k: source.get(k)
        for k in (
            "workspace_root",
            "workspace_name",
            "workspace_id",
            "repo_name",
            "branch",
            "registered_in_catalog",
            "build_files",
            "start_command_candidates",
        )
    }


def _safe_git_remote(remote: dict[str, Any]) -> dict[str, Any]:
    return {
        k: remote.get(k)
        for k in ("provider", "owner", "repo", "repository", "branch", "remote_url", "remote_name")
    }

# SPDX-License-Identifier: Apache-2.0
"""Vercel greenfield deployment orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
    format_git_remote_resolution_report,
    resolve_git_remote_from_workspace,
)
from aethos_core.providers.railway.greenfield_deployment.local_repo_inspection import (
    build_required_env_var_report,
    format_required_env_var_report,
    inspect_local_repo_for_deployment,
)
from aethos_core.providers.railway.greenfield_deployment.local_workspace_source import (
    discover_local_workspace_deployment_source,
    format_local_workspace_deployment_source_report,
)
from aethos_core.providers.railway.greenfield_deployment.target_plan import parse_plan_fields_from_text
from aethos_core.providers.vercel.greenfield_deployment.greenfield_preflight import (
    compose_vercel_greenfield_preflight_reply,
    create_vercel_greenfield_preflight_job,
)
from aethos_core.providers.vercel.greenfield_deployment.remote_repo_inspection import (
    inspect_remote_github_repo_for_deployment,
)
from aethos_core.providers.vercel.greenfield_deployment.remote_repo_source import (
    format_remote_repo_source_report,
    resolve_remote_github_repo_from_text,
)
from aethos_core.providers.vercel.greenfield_deployment.target_plan import (
    build_vercel_greenfield_target_plan,
    format_vercel_greenfield_target_plan,
)
from aethos_core.runtime.vercel_readonly_jobs import resolve_vercel_api_token_for_chat


@dataclass
class VercelGreenfieldFlowResult:
    ok: bool
    blocked: bool
    blocker_code: str = ""
    blocker_detail: str = ""
    reply: str = ""
    intent: str = "vercel_greenfield_deployment_flow"
    preflight_job_id: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)


def run_vercel_greenfield_deployment_flow(
    user_text: str,
    *,
    session_id: str = "default",
    workspace_hint: str = "",
) -> VercelGreenfieldFlowResult:
    token, credential_id = resolve_vercel_api_token_for_chat()
    if not token:
        detail = "Vercel credentials unavailable. Add an API token in Mission Control → Advanced settings → Credentials."
        return VercelGreenfieldFlowResult(
            ok=False,
            blocked=True,
            blocker_code="VERCEL_TOKEN_MISSING",
            blocker_detail=detail,
            reply=f"Vercel greenfield deployment blocked: {detail}",
            intent="vercel_greenfield_deployment_blocked",
        )

    parsed = parse_plan_fields_from_text(user_text, default_repo="")
    from aethos_core.deployment_targets.resolver import resolve_workspace_hint_for_session

    workspace_hint = resolve_workspace_hint_for_session(workspace_hint or None, session_id=session_id)
    remote_repo = resolve_remote_github_repo_from_text(
        user_text,
        session_id=session_id,
        workspace_hint=workspace_hint,
    )
    remote_ok = bool(remote_repo.get("ok"))
    deployment_target = remote_repo.get("deployment_target") if isinstance(remote_repo.get("deployment_target"), dict) else {}

    local_source: dict[str, Any] = {"ok": False}
    local_report = ""
    git_remote: dict[str, Any] = {}
    git_report = ""
    inspection: dict[str, Any] = {"runtime": "unknown", "required_env_var_names": []}

    if remote_ok:
        git_remote = dict(remote_repo)
        git_report = format_remote_repo_source_report(remote_repo)
        local_source = {
            "ok": True,
            "source": "remote_github",
            "workspace_name": str(remote_repo.get("project_name") or ""),
            "project_name": str(remote_repo.get("project_name") or ""),
            "branch": str(remote_repo.get("branch") or "main"),
        }
        local_report = git_report
        inspection = inspect_remote_github_repo_for_deployment(
            repository=str(remote_repo.get("repository") or ""),
            branch=str(remote_repo.get("branch") or "main"),
        )
    else:
        hint = workspace_hint or str(parsed.get("service_name") or parsed.get("repo") or deployment_target.get("alias") or "aethos").split("/")[-1]
        local_source = discover_local_workspace_deployment_source(hint=hint, user_text=user_text)
        local_report = format_local_workspace_deployment_source_report(local_source)
        if not local_source.get("ok"):
            return VercelGreenfieldFlowResult(
                ok=False,
                blocked=True,
                blocker_code=str(local_source.get("blocker_code") or remote_repo.get("blocker_code") or "LOCAL_WORKSPACE_NOT_CONFIGURED"),
                blocker_detail=str(local_source.get("detail") or remote_repo.get("detail") or ""),
                reply="\n\n".join(
                    part
                    for part in (
                        local_report,
                        format_remote_repo_source_report(remote_repo) if remote_repo.get("blocker_code") else "",
                    )
                    if part
                ),
                intent="vercel_greenfield_deployment_blocked",
                artifacts={"local_source": local_source, "remote_repo": remote_repo},
            )

        workspace_root = str(local_source.get("workspace_root") or "")
        git_remote = resolve_git_remote_from_workspace(workspace_root)
        git_report = format_git_remote_resolution_report(git_remote)
        if not git_remote.get("ok"):
            return VercelGreenfieldFlowResult(
                ok=False,
                blocked=True,
                blocker_code=str(git_remote.get("blocker_code") or "GIT_REMOTE_MISSING"),
                blocker_detail=str(git_remote.get("detail") or ""),
                reply="\n\n".join([local_report, "", git_report]),
                intent="vercel_greenfield_deployment_blocked",
            )
        inspection = inspect_local_repo_for_deployment(workspace_root)

    repo_full = str(git_remote.get("repository") or "unknown/unknown")
    branch = str(git_remote.get("branch") or local_source.get("branch") or "main")
    project_name = str(
        git_remote.get("project_name")
        or local_source.get("project_name")
        or repo_full.split("/")[-1]
        or "app"
    )
    plan = build_vercel_greenfield_target_plan(
        repo_full_name=repo_full,
        branch=branch,
        project_name=project_name,
        framework=str(inspection.get("framework") or inspection.get("runtime") or "other"),
        deployment_target=deployment_target if deployment_target.get("ok") else None,
    )
    plan["github_repo_id"] = git_remote.get("github_repo_id")

    from aethos_core.config import get_settings
    from aethos_core.providers.vercel.api_client import ensure_project_for_greenfield

    settings = get_settings()
    team_id = str(settings.vercel_team_id or "").strip() or None
    project_resolution = ensure_project_for_greenfield(
        token,
        project_name=project_name,
        git_repo=repo_full,
        framework=str(plan.get("framework") or "other"),
        team_id=team_id,
        create_if_missing=bool(settings.vercel_greenfield_create_project_enabled),
    )
    if not project_resolution.get("ok"):
        detail = str(project_resolution.get("detail") or project_resolution.get("error") or "Project resolution failed.")
        return VercelGreenfieldFlowResult(
            ok=False,
            blocked=True,
            blocker_code=str(project_resolution.get("error") or "VERCEL_PROJECT_RESOLUTION_FAILED"),
            blocker_detail=detail,
            reply=f"Vercel greenfield deployment blocked: {detail}",
            intent="vercel_greenfield_deployment_blocked",
        )
    project = dict(project_resolution.get("project") or {})
    plan["project_id"] = project.get("id") or project.get("name")
    plan["project_created"] = bool(project_resolution.get("created"))

    env_report = build_required_env_var_report(inspection, git_remote=git_remote, plan=plan)

    preflight = create_vercel_greenfield_preflight_job(
        user_text=user_text,
        session_id=session_id,
        plan=plan,
        env_report=env_report,
        local_source=local_source,
        git_remote=git_remote,
        credential_id=credential_id,
    )
    if not preflight.get("ok"):
        detail = str(preflight.get("error") or "Preflight creation failed.")
        return VercelGreenfieldFlowResult(
            ok=False,
            blocked=True,
            blocker_code="VERCEL_GREENFIELD_PREFLIGHT_FAILED",
            blocker_detail=detail,
            reply=f"Vercel greenfield deployment blocked: {detail}",
            intent="vercel_greenfield_deployment_blocked",
        )

    job_id = str(preflight.get("job_id") or "")

    solo_result = _maybe_run_solo_vercel(
        user_text,
        session_id,
        plan,
        env_report,
        git_remote,
        local_source,
        inspection,
        job_id,
        preflight,
        local_report,
        git_report,
        format_required_env_var_report(env_report),
        format_vercel_greenfield_target_plan(plan),
    )
    if solo_result is not None:
        return solo_result

    sections = [
        "Vercel greenfield deployment readiness",
        "",
    ]
    if plan.get("project_created"):
        sections.append(f"Created net-new Vercel project `{project_name}`.")
        sections.append("")
    sections.extend(
        [
            local_report,
            "",
            git_report if git_report else "",
            "",
            format_required_env_var_report(env_report),
            "",
            format_vercel_greenfield_target_plan(plan),
            "",
            compose_vercel_greenfield_preflight_reply(job_id=job_id, plan=plan),
        ]
    )
    return VercelGreenfieldFlowResult(
        ok=True,
        blocked=False,
        reply="\n".join([line for line in sections if line is not None]),
        intent="vercel_greenfield_deployment_preflight_created",
        preflight_job_id=job_id,
        artifacts={"plan": plan, "env_report": env_report},
    )


def _maybe_run_solo_vercel(
    user_text: str,
    session_id: str,
    plan: dict[str, Any],
    env_report: dict[str, Any],
    git_remote: dict[str, Any],
    local_source: dict[str, Any],
    inspection: dict[str, Any],
    job_id: str,
    preflight: dict[str, Any],
    local_report: str,
    git_report: str,
    env_report_text: str,
    target_report: str,
) -> VercelGreenfieldFlowResult | None:
    try:
        from aethos_core.solo_execution.solo_vercel_greenfield_executor import maybe_run_solo_vercel_greenfield_execution

        return maybe_run_solo_vercel_greenfield_execution(
            user_text=user_text,
            session_id=session_id,
            plan=plan,
            env_report=env_report,
            git_remote=git_remote,
            local_source=local_source,
            inspection=inspection,
            preflight_job_id=job_id,
            preflight_id=str(preflight.get("preflight_id") or ""),
            local_report=local_report,
            git_report=git_report,
            env_report_text=env_report_text,
            target_report=target_report,
        )
    except ImportError:
        return None

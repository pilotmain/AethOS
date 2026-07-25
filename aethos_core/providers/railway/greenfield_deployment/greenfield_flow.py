# SPDX-License-Identifier: Apache-2.0
"""Railway greenfield deployment from local workspace — orchestrated phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
    format_git_remote_resolution_report,
    resolve_git_remote_from_workspace,
)
from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
    compose_greenfield_preflight_reply,
    create_railway_greenfield_preflight_job,
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
from aethos_core.providers.railway.greenfield_deployment.target_plan import (
    build_railway_greenfield_target_plan,
    format_railway_greenfield_target_plan,
)


@dataclass
class RailwayGreenfieldFlowResult:
    ok: bool
    blocked: bool
    blocker_code: str = ""
    blocker_detail: str = ""
    safe_next_command: str = ""
    reply: str = ""
    intent: str = "railway_greenfield_deployment_flow"
    preflight_job_id: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)


def run_railway_greenfield_deployment_flow(
    user_text: str,
    *,
    session_id: str = "default",
    workspace_hint: str = "aethos",
) -> RailwayGreenfieldFlowResult:
    """Phases 1–5 readonly; creates governed preflight when ready."""
    try:
        return _run_railway_greenfield_deployment_flow_impl(
            user_text,
            session_id=session_id,
            workspace_hint=workspace_hint,
        )
    except Exception as exc:
        from aethos_core.security.secret_redaction import redact_text

        detail = redact_text(str(exc))
        return RailwayGreenfieldFlowResult(
            ok=False,
            blocked=True,
            blocker_code="RAILWAY_GREENFIELD_FLOW_ERROR",
            blocker_detail=detail,
            safe_next_command="Open Mission Control → Code workspaces and register the AethOS repo path.",
            reply=_compose_blocker_reply(
                title="Railway greenfield deployment blocked",
                code="RAILWAY_GREENFIELD_FLOW_ERROR",
                detail=detail,
                next_command="Open Mission Control → Code workspaces and register the AethOS repo path.",
            ),
            intent="railway_greenfield_deployment_blocked",
        )


def _run_railway_greenfield_deployment_flow_impl(
    user_text: str,
    *,
    session_id: str = "default",
    workspace_hint: str = "aethos",
) -> RailwayGreenfieldFlowResult:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )

    checks = safe_run_deployment_readiness_checks(user_text=user_text, session_id=session_id)
    artifacts: dict[str, Any] = {"railway_checks": _safe_checks(checks)}

    from aethos_core.deployment_targets.resolver import (
        resolve_deployment_target,
        resolve_workspace_hint_for_session,
    )

    workspace_hint = resolve_workspace_hint_for_session(
        workspace_hint if workspace_hint != "aethos" else None,
        session_id=session_id,
    )
    deployment_target = resolve_deployment_target(
        user_text,
        session_id=session_id,
        workspace_hint=workspace_hint,
    )
    artifacts["deployment_target"] = deployment_target

    local_hint = workspace_hint
    if deployment_target.get("ok"):
        if deployment_target.get("local_path"):
            local_hint = str(deployment_target["local_path"])
        elif deployment_target.get("alias"):
            local_hint = str(deployment_target["alias"])

    if not checks.get("railway_credential_ok") or not checks.get("railway_api_connection_ok"):
        from aethos_core.provider_e2e_readiness.blocker_mapping import (
            is_auth_rejection_detail,
            is_rate_limited_detail,
        )

        detail = str(
            checks.get("railway_api_connection_detail")
            or checks.get("railway_credential_detail")
            or "Railway credential not ready."
        )
        status_code = checks.get("railway_api_connection_status_code")

        if not checks.get("railway_credential_ok"):
            # No resolvable token at all.
            code = "RAILWAY_TOKEN_MISSING"
            title = "Railway credential not ready"
        elif checks.get("railway_api_connection_rate_limited") or is_rate_limited_detail(detail, status_code=status_code):
            # Token is present and valid — Railway is just throttling us. Transient, retryable.
            code = "RAILWAY_RATE_LIMITED"
            title = "Railway API rate limit (transient — token is valid)"
            detail = (
                "Railway is temporarily rate-limiting API requests. Your token is valid and already "
                "configured in Mission Control — this is not a credential problem. Retry once the "
                f"rate-limit window clears. Probe detail: {detail}"
            )
        elif is_auth_rejection_detail(detail, status_code=status_code):
            code = "RAILWAY_TOKEN_INVALID"
            title = "Railway credential not ready"
        else:
            code = "RAILWAY_API_CONNECTION_FAILED"
            title = "Railway API connection failed"

        return RailwayGreenfieldFlowResult(
            ok=False,
            blocked=True,
            blocker_code=code,
            blocker_detail=detail,
            safe_next_command="show railway credential diagnostics",
            reply=_compose_blocker_reply(
                title=title,
                code=code,
                detail=detail,
                next_command="show railway credential diagnostics",
            ),
            intent="railway_greenfield_deployment_blocked",
            artifacts=artifacts,
        )

    from aethos_core.production.deployment_mode import is_hosted_deployment
    from aethos_core.providers.vercel.greenfield_deployment.remote_repo_inspection import (
        inspect_remote_github_repo_for_deployment,
    )
    from aethos_core.providers.vercel.greenfield_deployment.remote_repo_source import (
        format_remote_repo_source_report,
        resolve_remote_github_repo_from_text,
    )

    remote_repo = resolve_remote_github_repo_from_text(
        user_text,
        session_id=session_id,
        workspace_hint=workspace_hint,
    )
    remote_ok = bool(remote_repo.get("ok"))
    hosted = is_hosted_deployment()

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
    elif hosted:
        blocker_code = str(remote_repo.get("blocker_code") or "REMOTE_REPO_MISSING")
        detail = str(remote_repo.get("detail") or "Could not resolve GitHub repository for hosted deploy.")
        safe_next = str(
            remote_repo.get("safe_next_command")
            or "Connect GitHub and register the repo, then retry: deploy killit to railway"
        )
        return RailwayGreenfieldFlowResult(
            ok=False,
            blocked=True,
            blocker_code=blocker_code,
            blocker_detail=detail,
            safe_next_command=safe_next,
            reply=_compose_blocker_reply(
                title="Hosted Railway deploy requires a connected GitHub repo",
                code=blocker_code,
                detail=detail,
                next_command=safe_next,
            ),
            intent="railway_greenfield_deployment_blocked",
            artifacts={**artifacts, "remote_repo": remote_repo},
        )
    else:
        local_source = discover_local_workspace_deployment_source(hint=local_hint, user_text=user_text)
        local_report = format_local_workspace_deployment_source_report(local_source)
        if not local_source.get("ok"):
            return RailwayGreenfieldFlowResult(
                ok=False,
                blocked=True,
                blocker_code=str(local_source.get("blocker_code") or "LOCAL_WORKSPACE_NOT_CONFIGURED"),
                blocker_detail=str(local_source.get("detail") or ""),
                safe_next_command=str(local_source.get("safe_next_command") or ""),
                reply=local_report,
                intent="railway_greenfield_deployment_blocked",
                artifacts=artifacts,
            )

        git_remote = resolve_git_remote_from_workspace(str(local_source.get("workspace_root") or ""))
        git_report = format_git_remote_resolution_report(git_remote)
        if not git_remote.get("ok"):
            return RailwayGreenfieldFlowResult(
                ok=False,
                blocked=True,
                blocker_code=str(git_remote.get("blocker_code") or "GIT_REMOTE_MISSING"),
                blocker_detail=str(git_remote.get("detail") or ""),
                safe_next_command=str(git_remote.get("safe_next_command") or ""),
                reply="\n\n".join([local_report, "", git_report]),
                intent="railway_greenfield_deployment_blocked",
                artifacts=artifacts,
            )

    artifacts["local_workspace_deployment_source_report"] = local_source
    artifacts["git_remote_resolution_report"] = git_remote
    if remote_ok:
        artifacts["remote_github_repo"] = remote_repo

    from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
        detect_greenfield_deploy_component,
        inspect_component_repo,
    )

    component = detect_greenfield_deploy_component(user_text)
    if local_source.get("workspace_root"):
        inspection = inspect_component_repo(str(local_source.get("workspace_root") or ""), component=component)
    elif not inspection.get("ok"):
        inspection = inspect_remote_github_repo_for_deployment(
            repository=str(git_remote.get("repository") or ""),
            branch=str(git_remote.get("branch") or "main"),
        )

    plan = build_railway_greenfield_target_plan(
        user_text=user_text,
        git_remote=git_remote,
        local_source=local_source,
        local_inspection=inspection,
        deployment_target=deployment_target if deployment_target.get("ok") else None,
    )
    artifacts["railway_greenfield_target_plan"] = plan

    env_report = build_required_env_var_report(inspection, git_remote=git_remote, plan=plan)
    artifacts["required_env_var_report"] = env_report
    target_report = format_railway_greenfield_target_plan(plan)
    env_report_text = format_required_env_var_report(env_report)

    preflight = create_railway_greenfield_preflight_job(
        user_text=user_text,
        session_id=session_id,
        plan=plan,
        env_report=env_report,
        local_source=local_source,
        git_remote=git_remote,
        railway_checks=checks,
    )
    artifacts["railway_greenfield_preflight_job"] = {
        "preflight_id": preflight.get("preflight_id"),
        "job_id": preflight.get("job_id"),
        "job_type": preflight.get("job_type"),
    }

    from aethos_core.solo_execution.solo_greenfield_executor import maybe_run_solo_greenfield_execution

    solo_result = maybe_run_solo_greenfield_execution(
        user_text=user_text,
        session_id=session_id,
        plan=plan,
        env_report=env_report,
        git_remote=git_remote,
        local_source=local_source,
        inspection=inspection,
        preflight_job_id=str(preflight.get("job_id") or ""),
        preflight_id=str(preflight.get("preflight_id") or ""),
        local_report=local_report,
        git_report=git_report,
        target_report=target_report,
        env_report_text=env_report_text,
    )
    if solo_result is not None:
        solo_result.artifacts.update(artifacts)
        return solo_result

    reply = compose_greenfield_preflight_reply(
        preflight=preflight,
        local_report=local_report,
        git_report=git_report,
        target_report=target_report,
        env_report_text=env_report_text,
    )

    return RailwayGreenfieldFlowResult(
        ok=True,
        blocked=False,
        reply=reply,
        intent="railway_greenfield_deployment_preflight",
        preflight_job_id=str(preflight.get("job_id") or ""),
        artifacts=artifacts,
    )


def _compose_blocker_reply(*, title: str, code: str, detail: str, next_command: str) -> str:
    return "\n".join(
        [
            f"**{title}**",
            "",
            f"- Blocker: `{code}`",
            f"- Detail: {detail}",
            "",
            "**Required action:** resolve the blocker before greenfield deployment can proceed.",
            "",
            f"**Safe next command:** `{next_command}`",
            "",
            "No Railway project or service has been created. No mutation has been performed.",
        ]
    )


def _safe_checks(checks: dict[str, Any]) -> dict[str, Any]:
    return {
        k: checks.get(k)
        for k in (
            "railway_credential_ok",
            "railway_api_connection_ok",
            "railway_api_connection_rate_limited",
            "railway_api_connection_status_code",
            "railway_api_connection_soft_passed",
            "railway_api_connection_soft_pass_reason",
            "railway_credential_source",
            "railway_credential_source_label",
            "railway_validation_probe",
        )
        if k in checks
    }

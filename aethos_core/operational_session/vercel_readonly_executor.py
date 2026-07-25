# SPDX-License-Identifier: Apache-2.0
"""Vercel readonly tool execution for the operational conversation kernel."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal
from aethos_core.operational_session.response_formatter import format_log_block
from aethos_core.operational_session.session_subject import SessionSubject, inventory_session_subject


@dataclass
class VercelReadonlyResult:
    ok: bool
    reply: str
    operation: str
    tool_id: str = ""
    summary: str = ""
    subject: SessionSubject | None = None
    log_limit: int | None = None
    deployment_id: str = ""


def execute_vercel_readonly(
    goal: ReadonlyGoal,
    subject: SessionSubject,
    *,
    session_id: str = "default",
) -> VercelReadonlyResult:
    if goal.operation == "validate_connection":
        return _validate_connection(subject, session_id=session_id)

    project = (subject.vercel_project or subject.project or subject.alias or "").strip()

    if goal.operation == "list_inventory" and subject.provider == "vercel" and not project:
        return _list_projects(subject, session_id=session_id, user_text=goal.user_text)

    if not project:
        return VercelReadonlyResult(
            ok=False,
            reply="Which **Vercel project** should I inspect? Name it explicitly (e.g. `killit`).",
            operation=goal.operation,
        )

    if goal.operation == "fetch_logs":
        return _fetch_logs(goal, subject, project_name=project, session_id=session_id)
    if goal.operation == "list_inventory":
        return _list_projects(subject, session_id=session_id, user_text=goal.user_text)
    if goal.operation == "list_deployments":
        return _list_deployments(goal, subject, project_name=project, session_id=session_id)
    if goal.operation in {"deployment_status", "health_check"}:
        return _deployment_summary(goal, subject, project_name=project, session_id=session_id, health=goal.operation == "health_check")
    return VercelReadonlyResult(
        ok=False,
        reply=f"I couldn't map that Vercel request for `{project}` to a readonly tool yet.",
        operation=goal.operation,
    )


def _validate_connection(subject: SessionSubject, *, session_id: str) -> VercelReadonlyResult:
    from aethos_core.provider_e2e_readiness.vercel_readiness_checks import run_vercel_readiness_checks

    checks = run_vercel_readiness_checks(session_id=session_id)
    cred_ok = bool(checks.get("vercel_credential_ok"))
    api_ok = bool(checks.get("vercel_api_connection_ok"))
    lines = ["**Vercel connection (readonly)**", ""]
    if cred_ok:
        lines.append("- Credential: **loaded**")
    else:
        lines.append(f"- Credential: **missing** — {checks.get('vercel_credential_detail') or 'not configured'}")
    if api_ok:
        detail = checks.get("vercel_api_connection_detail") or "ok"
        count = checks.get("vercel_project_count", 0)
        lines.append(f"- API connection: **ok** — {detail}")
        lines.append(f"- Projects visible: **{count}**")
    else:
        lines.append(f"- API connection: **failed** — {checks.get('vercel_api_connection_detail') or 'unknown'}")
    lines.extend(["", "No mutation has been performed."])
    updated = SessionSubject(provider="vercel", subject_source="session")
    return VercelReadonlyResult(
        ok=cred_ok and api_ok,
        reply="\n".join(lines),
        operation="validate_connection",
        tool_id="vercel.validate_token",
        summary="connection ok" if (cred_ok and api_ok) else "connection failed",
        subject=updated,
    )


def _resolve_token() -> tuple[str, str] | None:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter
    from aethos_core.runtime.vercel_readonly_jobs import resolve_vercel_auth_for_chat

    auth = resolve_vercel_auth_for_chat()
    if auth.get("auth_method") != "api_token" or not auth.get("credential_id"):
        return None
    token = VercelAuthAdapter().get_api_token(str(auth["credential_id"]))
    if not token:
        return None
    return token, str(auth["credential_id"])


def _fetch_logs(
    goal: ReadonlyGoal,
    subject: SessionSubject,
    *,
    project_name: str,
    session_id: str,
) -> VercelReadonlyResult:
    auth = _resolve_token()
    if auth is None:
        return VercelReadonlyResult(
            ok=False,
            reply=(
                "Vercel API token is not available.\n\n"
                "Add **VERCEL_API_TOKEN** in Mission Control → Advanced settings → Credentials → Vercel."
            ),
            operation="fetch_logs",
            tool_id="vercel.fetch_logs",
        )
    token, _cred = auth
    from aethos_core.providers.vercel.operations.logs_api import fetch_deployment_logs

    payload = fetch_deployment_logs(token, project_name=project_name)
    dep_id = str(payload.get("deployment_id") or "")
    deployment = payload.get("deployment") if isinstance(payload.get("deployment"), dict) else {}

    events = list(payload.get("events") or [])
    logs = []
    for row in events[: goal.log_limit]:
        if not isinstance(row, dict):
            continue
        logs.append(
            {
                "timestamp": str(row.get("created") or "—"),
                "level": str(row.get("type") or "INFO"),
                "message": str(row.get("text") or "").strip(),
                "source": "vercel_api",
            }
        )
    if not logs:
        for line in list(payload.get("log_lines") or [])[: goal.log_limit]:
            logs.append(
                {
                    "timestamp": "—",
                    "level": "INFO",
                    "message": str(line),
                    "source": "vercel_api",
                }
            )

    if logs:
        return _fetch_logs_success_block(
            goal, subject, project_name=project_name, payload=payload, logs=logs
        )

    if not logs:
        state = str(deployment.get("state") or "unknown")
        if dep_id or state != "unknown":
            tried = payload.get("deployments_tried")
            tried_note = f" (checked {tried} deployment(s))" if tried else ""
            state_note = (
                "Production may be healthy while an older deployment failed — runtime logs are often "
                "not exposed via API even for **ready** deployments."
                if state in {"ready", "success"}
                else "Build output for **error** deployments is usually only in the Vercel dashboard."
            )
            reply = (
                f"**Vercel logs for {project_name}**{tried_note}\n\n"
                f"Primary deployment `{dep_id or '—'}` · state **{state}**\n\n"
                f"The Vercel API did not return runtime log lines. {state_note}\n\n"
                f"Next: `deployment status for {project_name} on vercel` or inspect the deployment in Vercel.\n\n"
                "No mutation has been performed."
            )
            updated = SessionSubject(
                provider="vercel",
                vercel_project=project_name,
                project=project_name,
                subject_source="session",
            )
            return VercelReadonlyResult(
                ok=True,
                reply=reply,
                operation="fetch_logs",
                tool_id="vercel.fetch_logs",
                summary=f"deployment {state}, no runtime log lines",
                subject=updated,
                log_limit=goal.log_limit,
                deployment_id=dep_id,
            )
    err = str(payload.get("error") or "Log fetch failed.")
    if "not found" in err.lower():
        reply = (
            f"No Vercel project named **{project_name}** appears in your inventory.\n\n"
            "Run `show vercel projects` to list projects, then retry with an exact name.\n\n"
            "No mutation has been performed."
        )
    else:
        reply = (
            f"**Vercel logs for {project_name}**\n\n"
            f"{err}\n\n"
            f"Try `deployment status for {project_name} on vercel`.\n\n"
            "No mutation has been performed."
        )
    return VercelReadonlyResult(
        ok=False,
        reply=reply,
        operation="fetch_logs",
        tool_id="vercel.fetch_logs",
        subject=SessionSubject(provider="vercel", vercel_project=project_name, project=project_name, subject_source="session"),
    )


def _fetch_logs_success_block(
    goal: ReadonlyGoal,
    subject: SessionSubject,
    *,
    project_name: str,
    payload: dict,
    logs: list[dict],
) -> VercelReadonlyResult:
    reply = format_log_block(
        provider="Vercel",
        target_label=f"**{project_name}**",
        logs=logs,
        limit=goal.log_limit,
        deployment_state=str((payload.get("deployment") or {}).get("state") or "unknown"),
        sources=["vercel_api"],
    )
    dep_id = str(payload.get("deployment_id") or "")
    updated = SessionSubject(
        provider="vercel",
        vercel_project=project_name,
        project=project_name,
        alias=subject.alias,
        subject_source="session",
    )
    return VercelReadonlyResult(
        ok=True,
        reply=reply,
        operation="fetch_logs",
        tool_id="vercel.fetch_logs",
        summary=f"{len(logs)} log line(s)",
        subject=updated,
        log_limit=goal.log_limit,
        deployment_id=dep_id,
    )


def _list_projects(
    subject: SessionSubject,
    *,
    session_id: str,
    user_text: str = "",
) -> VercelReadonlyResult:
    auth = _resolve_token()
    if auth is None:
        return VercelReadonlyResult(
            ok=False,
            reply="Vercel API token is not available for project inventory.",
            operation="list_inventory",
            tool_id="vercel.discover_projects",
        )
    token, _cred = auth
    from aethos_core.providers.vercel.diagnostics.project_diagnostics_api import fetch_projects_list

    payload = fetch_projects_list(token)
    projects = list(payload.get("projects") or [])
    wants_per_project_health = bool(
        re.search(r"\b(health|status)\b.*\b(each|every|all)\b", user_text, re.I)
        or re.search(r"\bfor each\b", user_text, re.I)
    )
    lines = ["**Vercel projects (readonly):**", ""]
    if not projects:
        lines.append("- No projects returned from Vercel API.")
    elif wants_per_project_health:
        from aethos_core.providers.vercel.operations.deployments_api import fetch_deployments

        for row in projects[:15]:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "—")
            dep = fetch_deployments(token, project_name=name, limit=3)
            deployments = list(dep.get("deployments") or [])
            latest = deployments[0] if deployments else {}
            state = latest.get("state") or row.get("latest_production_state") or "unknown"
            url = latest.get("url") or "—"
            lines.append(f"- **{name}** · deployment **{state}** · {url}")
    else:
        for row in projects[:15]:
            if isinstance(row, dict):
                lines.append(
                    f"- **{row.get('name') or '—'}** · production `{row.get('latest_production_state') or 'unknown'}`"
                )
    lines.extend(["", "No mutation has been performed."])
    updated = inventory_session_subject(provider="vercel", project_count=len(projects))
    return VercelReadonlyResult(
        ok=True,
        reply="\n".join(lines),
        operation="list_inventory",
        tool_id="vercel.discover_projects",
        summary=f"{len(projects)} project(s)",
        subject=updated,
    )


def _list_deployments(
    goal: ReadonlyGoal,
    subject: SessionSubject,
    *,
    project_name: str,
    session_id: str,
) -> VercelReadonlyResult:
    auth = _resolve_token()
    if auth is None:
        return VercelReadonlyResult(
            ok=False,
            reply="Vercel credentials are not configured.",
            operation="list_deployments",
            tool_id="vercel.verify_deployment",
        )
    token, _cred = auth
    from aethos_core.providers.vercel.operations.deployments_api import fetch_deployments

    payload = fetch_deployments(token, project_name=project_name, limit=10)
    deployments = list(payload.get("deployments") or [])
    lines = [f"**Vercel deployments for {project_name}:**", ""]
    if not deployments:
        lines.append("- No deployments returned.")
    else:
        for row in deployments[: goal.log_limit or 5]:
            lines.append(
                f"- `{row.get('created_at') or '—'}` **{row.get('state') or 'unknown'}** · "
                f"`{row.get('branch') or '—'}` · {row.get('url') or '—'}"
            )
    lines.extend(["", "No mutation has been performed."])
    updated = SessionSubject(provider="vercel", vercel_project=project_name, project=project_name, subject_source="session")
    return VercelReadonlyResult(
        ok=True,
        reply="\n".join(lines),
        operation="list_deployments",
        tool_id="vercel.verify_deployment",
        summary=f"{len(deployments)} deployment(s)",
        subject=updated,
    )


def _deployment_summary(
    goal: ReadonlyGoal,
    subject: SessionSubject,
    *,
    project_name: str,
    session_id: str,
    health: bool = False,
) -> VercelReadonlyResult:
    auth = _resolve_token()
    if auth is None:
        return VercelReadonlyResult(
            ok=False,
            reply="Vercel credentials are not configured for readonly inspection.",
            operation=goal.operation,
        )
    token, _cred = auth
    from aethos_core.providers.vercel.operations.deployments_api import fetch_deployments

    payload = fetch_deployments(token, project_name=project_name, limit=3)
    deployments = list(payload.get("deployments") or [])
    lines = [f"**Vercel {'health' if health else 'deployment status'} for {project_name}:**", ""]
    if not deployments:
        lines.append("- No deployments returned from Vercel API.")
    else:
        for row in deployments[:3]:
            lines.append(
                f"- state: **{row.get('state') or 'unknown'}** · branch: `{row.get('branch') or '—'}` · "
                f"url: {row.get('url') or '—'}"
            )
    lines.extend(["", "No mutation has been performed."])
    updated = SessionSubject(provider="vercel", vercel_project=project_name, project=project_name, subject_source="session")
    return VercelReadonlyResult(
        ok=True,
        reply="\n".join(lines),
        operation=goal.operation,
        tool_id="vercel.verify_deployment",
        summary="deployment status",
        subject=updated,
    )

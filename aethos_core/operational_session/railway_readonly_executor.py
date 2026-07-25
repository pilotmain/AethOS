# SPDX-License-Identifier: Apache-2.0
"""Railway readonly tool execution for the operational conversation kernel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal
from aethos_core.operational_session.response_formatter import format_health_block, format_inventory_block, format_log_block
from aethos_core.operational_session.session_subject import SessionSubject, inventory_session_subject


@dataclass
class ReadonlyExecutionResult:
    ok: bool
    reply: str
    operation: str
    tool_id: str = ""
    summary: str = ""
    subject: SessionSubject | None = None
    log_limit: int | None = None


def execute_railway_readonly(
    goal: ReadonlyGoal,
    subject: SessionSubject,
    *,
    session_id: str = "default",
) -> ReadonlyExecutionResult:
    if goal.operation == "validate_connection":
        return _validate_connection(session_id=session_id)
    if goal.operation == "list_inventory":
        return _list_inventory(session_id=session_id)
    if goal.operation == "list_services":
        return _list_inventory(session_id=session_id, services_only=True)
    if goal.operation == "fetch_logs":
        return _fetch_logs(goal, subject, session_id=session_id)
    if goal.operation == "health_check":
        return _health_check(subject, session_id=session_id)
    if goal.operation == "deployment_status":
        return _deployment_status(subject, session_id=session_id)
    return ReadonlyExecutionResult(
        ok=False,
        reply="I couldn't map that Railway request to a readonly tool yet.",
        operation=goal.operation,
    )


def _validate_connection(*, session_id: str) -> ReadonlyExecutionResult:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )

    checks = safe_run_deployment_readiness_checks(session_id=session_id)
    token_ok = bool(checks.get("railway_credential_ok"))
    api_ok = bool(checks.get("railway_api_connection_ok"))
    inventory = checks.get("inventory") if isinstance(checks.get("inventory"), dict) else {}
    inv_ok = bool(inventory.get("ok"))
    lines = ["**Railway connection (readonly)**", ""]
    if token_ok:
        lines.append("- Credential: **loaded**")
    else:
        lines.append(f"- Credential: **missing** — {checks.get('railway_credential_detail') or 'not configured'}")
    if api_ok:
        lines.append(f"- API connection: **ok** — {checks.get('railway_api_connection_detail') or 'ok'}")
    else:
        lines.append(f"- API connection: **failed** — {checks.get('railway_api_connection_detail') or 'unknown'}")
    if inv_ok:
        count = int(inventory.get("service_count") or 0)
        lines.append(f"- Inventory: **ok** — {count} service(s) visible")
    else:
        lines.append(f"- Inventory: **failed** — {inventory.get('error') or 'unknown'}")
    lines.extend(["", "No mutation has been performed."])
    subject = SessionSubject(provider="railway", subject_source="session")
    return ReadonlyExecutionResult(
        ok=token_ok and api_ok and inv_ok,
        reply="\n".join(lines),
        operation="validate_connection",
        tool_id="railway.validate_token",
        summary="connection ok" if (token_ok and api_ok and inv_ok) else "connection failed",
        subject=subject,
    )


def _list_inventory(*, session_id: str, services_only: bool = False) -> ReadonlyExecutionResult:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )
    from aethos_core.providers.railway.inventory.railway_projects_chat import (
        build_railway_inventory_summary_from_cache,
        compose_railway_inventory_blocker,
        format_railway_projects_inventory_reply,
        should_use_cached_railway_inventory,
    )

    checks = safe_run_deployment_readiness_checks(user_text="show railway projects", session_id=session_id)
    inventory = dict(checks.get("inventory") or {})
    if not inventory.get("ok") and should_use_cached_railway_inventory(error=str(inventory.get("error") or "")):
        cached = build_railway_inventory_summary_from_cache()
        if cached:
            inventory = cached
    if not inventory.get("ok"):
        reply = compose_railway_inventory_blocker(inventory=inventory, checks=checks)
        return ReadonlyExecutionResult(ok=False, reply=reply, operation="list_inventory", tool_id="railway.discover_projects")

    body = format_railway_projects_inventory_reply(inventory)
    if services_only:
        body = body.replace("**Railway projects and services**", "**Railway services**")
    reply = format_inventory_block(provider="railway", body=body)
    subject = inventory_session_subject(
        provider="railway",
        project_count=int(inventory.get("project_count") or 0),
        environment_count=int(inventory.get("environment_count") or 0),
        service_count=int(inventory.get("service_count") or 0),
    )
    return ReadonlyExecutionResult(
        ok=True,
        reply=reply,
        operation="list_inventory",
        tool_id="railway.discover_projects",
        summary=f"{inventory.get('project_count', 0)} projects",
        subject=subject,
    )


def _resolve_health_rows(subject: SessionSubject, *, session_id: str) -> list[dict[str, Any]]:
    from aethos_core.operational_session.railway_service_hints import filter_railway_health_rows
    from aethos_core.operational_planner.adapters.railway_wide_health import collect_railway_service_health_rows

    rows, _error = collect_railway_service_health_rows()
    services = list(subject.services)
    if subject.service:
        services = [subject.service]
    if not services:
        services = ["aethos-api", "aethos-ui"]
    return filter_railway_health_rows(rows, services, text=" ".join(services))


def _fetch_logs(goal: ReadonlyGoal, subject: SessionSubject, *, session_id: str) -> ReadonlyExecutionResult:
    from aethos_core.providers.railway.operations.logs_multisource import fetch_railway_service_logs_fast

    rows = _resolve_health_rows(subject, session_id=session_id)
    if not rows:
        named = (subject.service or (subject.services[0] if subject.services else "")).strip()
        if named:
            reply = (
                f"No Railway service named **{named}** appears in your inventory.\n\n"
                "Run `show railway projects` to list projects and services, then retry with an exact name."
            )
        else:
            reply = "I couldn't resolve Railway services for log fetch. Try naming the service (e.g. `aethos-api`)."
        return ReadonlyExecutionResult(
            ok=False,
            reply=reply,
            operation="fetch_logs",
            tool_id="railway.fetch_logs",
        )

    sections: list[str] = []
    for row in rows:
        service_name = str(row.get("service") or "")
        payload = fetch_railway_service_logs_fast(
            service_name=service_name,
            service_id=str(row.get("service_id") or "") or None,
            limit=goal.log_limit,
        )
        logs = list(payload.get("logs") or [])
        path = f"{row.get('project') or '—'} / {row.get('environment') or '—'} / {service_name}"
        sections.append(
            format_log_block(
                provider="Railway",
                target_label=f"**{path}**",
                logs=logs,
                limit=goal.log_limit,
                health=str(row.get("health") or "unknown"),
                deployment_state=str(row.get("deployment_state") or "unknown"),
                sources=list(payload.get("sources_checked") or []),
            ).replace("No mutation has been performed.", "").strip()
        )

    reply = "\n\n".join(sections).strip() + "\n\nNo mutation has been performed."
    updated = SessionSubject(
        provider="railway",
        project=str(rows[0].get("project") or subject.project or ""),
        environment=str(rows[0].get("environment") or subject.environment or "staging"),
        services=[str(row.get("service") or "") for row in rows if row.get("service")],
        service=str(rows[0].get("service") or "") if len(rows) == 1 else "",
        subject_source="session",
    )
    return ReadonlyExecutionResult(
        ok=True,
        reply=reply,
        operation="fetch_logs",
        tool_id="railway.fetch_logs",
        summary=f"{len(rows)} service(s), limit {goal.log_limit}",
        subject=updated,
        log_limit=goal.log_limit,
    )


def _health_check(subject: SessionSubject, *, session_id: str) -> ReadonlyExecutionResult:
    rows = _resolve_health_rows(subject, session_id=session_id)
    if not rows:
        return ReadonlyExecutionResult(
            ok=False,
            reply="No Railway services matched for health check.",
            operation="health_check",
            tool_id="railway.verify_deployment",
        )
    reply = format_health_block(provider="railway", rows=rows)
    updated = SessionSubject(
        provider="railway",
        project=str(rows[0].get("project") or ""),
        environment=str(rows[0].get("environment") or "staging"),
        services=[str(row.get("service") or "") for row in rows if row.get("service")],
        service=str(rows[0].get("service") or "") if len(rows) == 1 else "",
        subject_source="session",
    )
    return ReadonlyExecutionResult(
        ok=True,
        reply=reply,
        operation="health_check",
        tool_id="railway.verify_deployment",
        summary=f"{len(rows)} service(s) checked",
        subject=updated,
    )


def _deployment_status(subject: SessionSubject, *, session_id: str) -> ReadonlyExecutionResult:
    rows = _resolve_health_rows(subject, session_id=session_id)
    if not rows:
        return ReadonlyExecutionResult(
            ok=False,
            reply="No Railway deployment targets resolved.",
            operation="deployment_status",
            tool_id="railway.verify_deployment",
        )
    lines = ["**Railway deployment status:**", ""]
    for row in rows:
        path = f"{row.get('project') or '—'} / {row.get('environment') or '—'} / {row.get('service') or '—'}"
        lines.append(
            f"- **{path}** — status: `{row.get('status') or 'unknown'}` · "
            f"deployment: `{row.get('deployment_state') or 'unknown'}` · "
            f"health: **{row.get('health') or 'unknown'}**"
        )
    lines.extend(["", "No mutation has been performed."])
    updated = SessionSubject(
        provider="railway",
        project=str(rows[0].get("project") or ""),
        environment=str(rows[0].get("environment") or "staging"),
        services=[str(row.get("service") or "") for row in rows if row.get("service")],
        subject_source="session",
    )
    return ReadonlyExecutionResult(
        ok=True,
        reply="\n".join(lines),
        operation="deployment_status",
        tool_id="railway.verify_deployment",
        summary="deployment status",
        subject=updated,
    )

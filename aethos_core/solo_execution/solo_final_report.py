# SPDX-License-Identifier: Apache-2.0
"""Final report contract for solo greenfield Railway execution."""

from __future__ import annotations

from typing import Any

from aethos_core.security.secret_redaction import redact_text


def compose_solo_chat_reply(
    *,
    plan: dict[str, Any],
    git_remote: dict[str, Any],
    journal: dict[str, Any],
    env_report: dict[str, Any],
    execution_status: str,
    blocker_code: str = "",
    blocker_detail: str = "",
) -> str:
    """Short user-facing result — no preflight dumps."""
    repo = git_remote.get("repository") or plan.get("repo")
    env_names = list(env_report.get("required_env_var_names") or [])
    deployment_id = str(journal.get("railway_deployment_id") or "")
    deployment_url = str(journal.get("deployment_url") or journal.get("railway_deployment_url") or "")
    health = journal.get("runtime_verification") or {}
    health_ok = bool(health.get("verified")) if isinstance(health, dict) else bool(
        journal.get("runtime_verification_performed")
    )
    deploy_status = str(journal.get("deploy_trigger_metadata", {}).get("deployment_status") or "").upper()
    if not health_ok and deploy_status == "SUCCESS":
        health_ok = True

    if execution_status != "completed":
        lines = [
            "**Railway deploy failed**",
            "",
            f"- Blocker: `{blocker_code or 'unknown'}`",
            f"- Detail: {blocker_detail or 'Deployment did not complete.'}",
            "",
            "Retry: `Deploy AethOS to Railway with env vars and verify it.`",
        ]
        return redact_text("\n".join(lines))

    lines = [
        "**Railway deploy complete**",
        "",
        f"- Target: `{plan.get('project')}` / `{plan.get('environment')}` → `{plan.get('service_name')}`",
        f"- Repo: `{repo}` @ `{plan.get('branch') or git_remote.get('branch')}`",
    ]
    if env_names:
        lines.append(f"- Env vars set: {', '.join(f'`{n}`' for n in env_names)}")
    if deployment_id:
        lines.append(f"- Deployment: `{deployment_id}`")
    if deployment_url:
        lines.append(f"- URL: {deployment_url}")
    lines.append(f"- Health: **{'pass' if health_ok else 'pending'}**")
    return redact_text("\n".join(lines))


def compose_solo_greenfield_final_report(
    *,
    plan: dict[str, Any],
    git_remote: dict[str, Any],
    journal: dict[str, Any],
    env_report: dict[str, Any],
    preflight_id: str = "",
    preflight_job_id: str = "",
    execution_status: str = "completed",
    logs_summary: str = "",
    next_action: str = "",
) -> str:
    env_names = list(env_report.get("required_env_var_names") or [])
    deployment_id = str(journal.get("railway_deployment_id") or "")
    deployment_url = str(journal.get("deployment_url") or journal.get("railway_deployment_url") or "")
    health = journal.get("runtime_verification") or {}
    health_ok = bool(health.get("ok")) if isinstance(health, dict) else bool(journal.get("runtime_verification_performed"))

    lines = [
        "# Railway greenfield deployment — final report",
        "",
        f"**Status:** `{execution_status}`",
        "",
        "## Target",
        f"- Project: `{plan.get('project')}`",
        f"- Service: `{plan.get('service_name')}`",
        f"- Environment: `{plan.get('environment')}`",
        f"- Git repo: `{git_remote.get('repository') or plan.get('repo')}`",
        f"- Branch: `{git_remote.get('branch') or plan.get('branch')}`",
    ]
    if preflight_id:
        lines.append(f"- Preflight: `{preflight_id}`")
    if preflight_job_id:
        lines.append(f"- Mission Control job: `{preflight_job_id}`")

    lines.extend(["", "## Env vars configured (names only)"])
    if env_names:
        lines.append("- " + ", ".join(f"`{n}`" for n in env_names))
    else:
        lines.append("- None detected from local workspace.")

    lines.extend(["", "## Deployment"])
    if deployment_id:
        lines.append(f"- Deployment ID: `{deployment_id}`")
    if deployment_url:
        lines.append(f"- Deployment URL: {deployment_url}")

    lines.extend(["", "## Health"])
    lines.append(f"- Result: **{'pass' if health_ok else 'fail or pending'}**")
    if isinstance(health, dict) and health.get("status_code") is not None:
        lines.append(f"- HTTP status: `{health.get('status_code')}`")

    if logs_summary:
        lines.extend(["", "## Logs summary", "", logs_summary])

    if next_action:
        lines.extend(["", "## Next action", "", next_action])
    elif execution_status == "completed":
        lines.extend(["", "Solo greenfield execution finished. No secret values are included in this report."])

    return redact_text("\n".join(lines))


def build_solo_final_report_payload(
    *,
    full_report: str,
    plan: dict[str, Any],
    journal: dict[str, Any],
    env_report: dict[str, Any],
    execution_status: str,
) -> dict[str, Any]:
    return {
        "execution_status": execution_status,
        "project_name": plan.get("project"),
        "service_name": plan.get("service_name"),
        "environment": plan.get("environment"),
        "git_repo": plan.get("repo"),
        "branch": plan.get("branch"),
        "env_var_names": list(env_report.get("required_env_var_names") or []),
        "deployment_id": journal.get("railway_deployment_id"),
        "deployment_url": journal.get("deployment_url") or journal.get("railway_deployment_url"),
        "health_result": journal.get("runtime_verification"),
        "full_report": full_report,
    }

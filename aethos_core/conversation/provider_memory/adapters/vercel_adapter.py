# SPDX-License-Identifier: Apache-2.0
"""Vercel evidence adapter — deployment and redeploy follow-ups."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.provider_memory.provider_evidence_adapter import (
    OperationStatus,
    OperationVerification,
    ProviderEvidenceAdapter,
    ProviderLogEntry,
)


class VercelEvidenceAdapter(ProviderEvidenceAdapter):
    provider = "vercel"

    def get_operation_status(self, thread: Any, job: Any | None) -> OperationStatus:
        project = _project_name(thread, job)
        live = _fetch_latest_deployment(project)
        status_label = str(live.get("state") or getattr(thread, "status", "unknown"))
        health = "online" if status_label.lower() in {"ready", "success", "active"} else "unknown"
        return OperationStatus(
            execution_job_id=str(getattr(job, "id", "") or getattr(thread, "execution_job_id", "") or "unknown"),
            provider_command=_command_state(job),
            restart_evidence="detected" if live.get("ok") else "not detected",
            latest_log_timestamp=live.get("created_at"),
            service_health=health,
            status_label=status_label,
            verification_label="verified" if health == "online" else "pending provider evidence",
        )

    def get_latest_logs(
        self,
        thread: Any,
        job: Any | None,
        *,
        limit: int = 5,
        level_filter: str | None = None,
    ) -> list[ProviderLogEntry]:
        project = _project_name(thread, job)
        payload = _fetch_deployment_events(project, limit=limit)
        rows: list[ProviderLogEntry] = []
        for row in payload.get("events") or []:
            if not isinstance(row, dict):
                continue
            level = str(row.get("type") or row.get("level") or "INFO")
            if level_filter and level_filter.lower() not in level.lower():
                continue
            rows.append(
                ProviderLogEntry(
                    timestamp=str(row.get("created") or row.get("timestamp") or "") or None,
                    level=level,
                    message=str(row.get("text") or row.get("message") or "")[:400],
                )
            )
        return rows[:limit]

    def verify_operation(self, thread: Any, job: Any | None) -> OperationVerification:
        project = _project_name(thread, job)
        live = _fetch_latest_deployment(project)
        state = str(live.get("state") or "").lower()
        verified = state in {"ready", "success", "active"}
        conclusion = "redeploy_verified" if verified else "still_stabilizing" if state in {"building", "queued", "initializing"} else "inconclusive"
        return OperationVerification(
            conclusion=conclusion,
            verified=verified,
            latest_log_timestamp=live.get("created_at"),
            timestamps_available=bool(live.get("created_at")),
            logs_unavailable=not live.get("ok"),
            service_health="online" if verified else "unknown",
            provider_command=_command_state(job),
            evidence=live,
        )

    def explain_failure(self, thread: Any, job: Any | None) -> str:
        project = _project_name(thread, job)
        live = _fetch_latest_deployment(project)
        path = thread.service_path() if hasattr(thread, "service_path") else project
        if live.get("error_message"):
            return (
                f"The latest Vercel **{getattr(thread, 'operation', 'mutation') or 'mutation'}** for **{path}** failed.\n\n"
                f"Reason: {live.get('error_message')}\n\n"
                f"Deployment state: **{live.get('state', 'unknown')}**"
            )
        if job is not None:
            params = getattr(job, "params", None) or {}
            failure = params.get("failure_truth") or params.get("lifecycle_summary")
            if failure:
                return str(failure)
        return (
            f"I checked the active Vercel thread for **{path}**, but no structured failure reason is stored yet.\n\n"
            f"Current status: **{getattr(thread, 'status', 'unknown')}**."
        )


def _project_name(thread: Any, job: Any | None) -> str:
    if job is not None:
        params = getattr(job, "params", None) or {}
        target = dict(params.get("target") or {})
        name = str(params.get("target_name") or target.get("project_name") or target.get("service_name") or "")
        if name:
            return name
    evidence = dict(getattr(thread, "last_evidence", None) or {})
    return str(
        evidence.get("project_name")
        or getattr(thread, "service", None)
        or getattr(thread, "project", None)
        or ""
    )


def _command_state(job: Any | None) -> str:
    if job is None:
        return "unknown"
    params = getattr(job, "params", None) or {}
    if params.get("executed") is True:
        return "submitted"
    if params.get("execution_state") == "execution_failed":
        return "failed"
    return str(params.get("execution_state") or "unknown")


def _resolve_token() -> str | None:
    from aethos_core.runtime.vercel_readonly_jobs import resolve_vercel_auth_for_chat

    auth = resolve_vercel_auth_for_chat()
    token = str(auth.get("token") or "").strip()
    return token or None


def _fetch_latest_deployment(project_name: str) -> dict[str, Any]:
    project_name = (project_name or "").strip()
    if not project_name:
        return {"ok": False, "detail": "No Vercel project name in thread context."}
    token = _resolve_token()
    if not token:
        return {"ok": False, "detail": "Vercel credentials unavailable."}
    from aethos_core.providers.vercel.operations.deployments_api import fetch_deployments

    payload = fetch_deployments(token, project_name=project_name, limit=3)
    if not payload.get("ok"):
        return {"ok": False, "detail": str(payload.get("error") or "deployment fetch failed")}
    deployments = list(payload.get("deployments") or [])
    if not deployments:
        return {"ok": False, "detail": "No deployments returned for project."}
    latest = deployments[0]
    return {
        "ok": True,
        "state": latest.get("state"),
        "created_at": latest.get("created_at"),
        "deployment_id": latest.get("id"),
        "url": latest.get("url"),
        "error_message": latest.get("error_message"),
        "branch": latest.get("branch"),
    }


def _fetch_deployment_events(project_name: str, *, limit: int) -> dict[str, Any]:
    live = _fetch_latest_deployment(project_name)
    if not live.get("ok") or not live.get("deployment_id"):
        return {"events": []}
    token = _resolve_token()
    if not token:
        return {"events": []}
    from aethos_core.providers.vercel.api_client import get_deployment_events

    events = get_deployment_events(token, str(live.get("deployment_id") or ""), limit=limit)
    return {"events": events}

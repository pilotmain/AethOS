# SPDX-License-Identifier: Apache-2.0
"""Railway deployment logs API."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import fetch_deployment_logs, find_service_by_name, list_service_deployments


def _select_failed(deployments: list[dict[str, Any]]) -> dict[str, Any] | None:
    for dep in deployments:
        state = str(dep.get("state") or "").lower()
        if state in ("failed", "crashed", "error"):
            return dep
    return deployments[0] if deployments else None


def _select_latest_success(deployments: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not deployments:
        return None
    ordered = sorted(deployments, key=lambda dep: str(dep.get("created_at") or ""), reverse=True)
    for dep in ordered:
        state = str(dep.get("state") or "").lower()
        if state in {"success", "active", "completed", "ready"}:
            return dep
    return ordered[0]


def fetch_service_logs(token: str, *, service_name: str, deployment_id: str | None = None) -> dict[str, Any]:
    svc = find_service_by_name(token, service_name)
    if not svc:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Service `{service_name}` not found via Railway API.",
            "logs": [],
        }
    deployments = list_service_deployments(token, service_id=str(svc["service_id"]), limit=10)
    dep = None
    if deployment_id:
        dep = next((d for d in deployments if d.get("id") == deployment_id), None)
    if dep is None:
        dep = _select_latest_success(deployments) or _select_failed(deployments)
    if not dep or not dep.get("id"):
        return {
            "ok": False,
            "source": "provider_api",
            "error": "No deployment available for log inspection.",
            "logs": [],
        }
    logs = fetch_deployment_logs(token, deployment_id=str(dep["id"]))
    lines = [str(x.get("message") or "") for x in logs if str(x.get("message") or "").strip()]
    events = [
        {"type": "log", "text": str(x.get("message") or ""), "created": x.get("timestamp")}
        for x in logs
        if str(x.get("message") or "").strip()
    ]
    return {
        "ok": True,
        "source": "provider_api",
        "service_name": svc["service_name"],
        "deployment_id": dep["id"],
        "deployment_state": dep.get("state"),
        "deployment": dep,
        "logs": logs,
        "events": events,
        "event_count": len(events),
        "log_lines": lines,
        "log_text": "\n".join(lines[-80:]),
    }


def format_logs_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return str(payload.get("error") or "Log fetch failed.")
    lines = [
        f"Service: {payload.get('service_name')}",
        f"Deployment: `{payload.get('deployment_id')}` · state {payload.get('deployment_state')}",
        "",
        "Recent log lines:",
    ]
    for line in (payload.get("log_lines") or [])[-20:]:
        lines.append(f"- {line[:240]}")
    if len(lines) <= 4:
        lines.append("(no log lines returned)")
    return "\n".join(lines)

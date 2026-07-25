# SPDX-License-Identifier: Apache-2.0
"""Railway deployments API."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import find_service_by_name, list_service_deployments


def fetch_deployments(token: str, *, service_name: str, limit: int = 20) -> dict[str, Any]:
    svc = find_service_by_name(token, service_name)
    if not svc:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Service `{service_name}` not found via Railway API.",
            "deployments": [],
        }
    records = list_service_deployments(token, service_id=str(svc["service_id"]), limit=limit)
    return {
        "ok": True,
        "source": "provider_api",
        "service_id": svc["service_id"],
        "service_name": svc["service_name"],
        "project_id": svc.get("project_id"),
        "project_name": svc.get("project_name"),
        "deployment_count": len(records),
        "deployments": records,
    }


def format_deployments_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return str(payload.get("error") or "Deployment fetch failed.")
    lines = [
        f"Service: {payload.get('service_name')}",
        f"Project: {payload.get('project_name') or '—'}",
        f"Deployments ({payload.get('deployment_count', 0)}):",
        "",
    ]
    for dep in payload.get("deployments") or []:
        lines.append(
            f"- **{dep.get('state', 'unknown')}** · `{dep.get('id', '')[:12]}` · "
            f"branch `{dep.get('branch') or '—'}` · commit `{dep.get('commit') or '—'}`"
        )
        if dep.get("error_message"):
            lines.append(f"  - error: {dep['error_message'][:240]}")
    if len(lines) <= 4:
        lines.append("(no deployments returned)")
    return "\n".join(lines)

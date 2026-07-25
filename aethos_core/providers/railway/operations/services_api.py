# SPDX-License-Identifier: Apache-2.0
"""Railway service / project details API."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import find_service_by_name, list_services


def fetch_service_details(token: str, *, service_name: str) -> dict[str, Any]:
    svc = find_service_by_name(token, service_name)
    if not svc:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Service `{service_name}` not found via Railway API.",
            "details": {},
        }
    siblings = [
        s["service_name"]
        for s in list_services(token)
        if str(s.get("project_id") or "") == str(svc.get("project_id") or "")
    ]
    details = {
        "service_id": svc["service_id"],
        "service_name": svc["service_name"],
        "project_id": svc.get("project_id"),
        "project_name": svc.get("project_name"),
        "services_in_project": siblings,
        "provider": "railway",
    }
    return {"ok": True, "source": "provider_api", "details": details}


def format_service_details_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return str(payload.get("error") or "Service details fetch failed.")
    d = payload.get("details") or {}
    lines = [
        f"Service: {d.get('service_name')}",
        f"Project: {d.get('project_name') or '—'}",
        f"Service ID: `{d.get('service_id') or '—'}`",
        "",
        "Services in project:",
    ]
    for name in d.get("services_in_project") or []:
        lines.append(f"- {name}")
    return "\n".join(lines)

# SPDX-License-Identifier: Apache-2.0
"""Railway service events via deployment history."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import find_service_by_name, list_service_deployments


def fetch_service_events(
    token: str,
    *,
    service_name: str,
    service_id: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    svc = None
    if service_id:
        svc = {"service_id": service_id, "service_name": service_name}
    if not svc:
        svc = find_service_by_name(token, service_name)
    if not svc:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Service `{service_name}` not found via Railway API.",
            "events": [],
            "capability_gap": False,
        }

    sid = str(svc.get("service_id") or service_id or "")
    records = list_service_deployments(token, service_id=sid, limit=limit)
    events: list[dict[str, Any]] = []
    for dep in sorted(records, key=lambda row: str(row.get("created_at") or ""), reverse=True):
        events.append(
            {
                "id": dep.get("id"),
                "type": "deployment",
                "state": dep.get("state"),
                "created_at": dep.get("created_at"),
                "branch": dep.get("branch"),
                "commit": dep.get("commit"),
                "error_message": dep.get("error_message"),
                "message": f"Deployment {dep.get('id')} state={dep.get('state')}",
            }
        )

    return {
        "ok": bool(events),
        "source": "provider_api",
        "service_id": sid,
        "service_name": svc.get("service_name") or service_name,
        "project_name": svc.get("project_name"),
        "events": events,
        "capability_gap": False,
    }


def get_service_events(
    target: dict[str, Any],
    *,
    limit: int = 20,
) -> dict[str, Any]:
    """Fetch Railway service events for a failed-service investigation target."""
    from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

    service_name = str(target.get("service") or "")
    service_id = str(target.get("service_id") or "") or None
    token, _, err = resolve_railway_mutation_credentials()
    if err or not token:
        return {
            "ok": False,
            "source": "provider_api",
            "error": str(err or "Railway API token is not configured."),
            "events": [],
            "capability_gap": True,
        }
    try:
        return fetch_service_events(token, service_name=service_name, service_id=service_id, limit=limit)
    except Exception as exc:
        return {
            "ok": False,
            "source": "provider_api",
            "error": str(exc),
            "events": [],
            "capability_gap": True,
        }

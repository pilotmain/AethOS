# SPDX-License-Identifier: Apache-2.0
"""Railway inventory adapter."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.inventory_adapter import InventoryAdapter


class RailwayInventoryAdapter(InventoryAdapter):
    provider = "railway"

    def fetch_projects_inventory(self, *, auth_context: dict[str, Any]) -> dict[str, Any]:
        token = str(auth_context.get("token") or "")
        if not token:
            return {"ok": False, "items": [], "error": "missing token"}
        from aethos_core.providers.railway.api_client import list_services_with_status
        from aethos_core.providers.railway.discovery import _latest_deployment_for_service

        result = list_services_with_status(token)
        if not result.get("ok"):
            return {
                "ok": False,
                "items": [],
                "error": str(result.get("error") or "GraphQL query failed"),
            }
        rows: list[dict[str, Any]] = []
        enrich_count = 0
        max_enrich = 50
        for svc in result.get("services") or []:
            if not isinstance(svc, dict):
                continue
            service_id = str(svc.get("service_id") or "")
            dep_state = "unknown"
            health = "unknown"
            health_reason: str | None = None
            if enrich_count < max_enrich and service_id:
                latest_dep, _status, health, health_reason = _latest_deployment_for_service(token, service_id)
                enrich_count += 1
                if latest_dep is not None:
                    dep_state = latest_dep.status
            elif not service_id:
                health_reason = "missing_service_id"
            else:
                health_reason = "enrichment_limit"
            rows.append(
                {
                    "provider": "railway",
                    "name": svc.get("service_name"),
                    "project_id": svc.get("project_id"),
                    "service_id": service_id,
                    "project_name": svc.get("project_name"),
                    "latest_deployment_state": dep_state,
                    "health": health,
                    "health_reason": health_reason,
                    "production_url": "",
                    "known_repo": "",
                    "evidence": ["source:railway_api"],
                }
            )
        return {"ok": True, "items": rows, "error": None}

    def build_projects_inventory(self, *, auth_context: dict[str, Any]) -> list[dict[str, Any]]:
        fetched = self.fetch_projects_inventory(auth_context=auth_context)
        if not fetched.get("ok"):
            return []
        items = fetched.get("items")
        return items if isinstance(items, list) else []

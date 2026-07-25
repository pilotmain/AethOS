# SPDX-License-Identifier: Apache-2.0
"""Railway provider capability adapter."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_runtime.adapter_contract import ProviderCapabilityAdapter


class RailwayCapabilityAdapter(ProviderCapabilityAdapter):
    provider = "railway"

    def fetch_logs(self, *, target: dict[str, Any], limit: int = 20) -> dict[str, Any]:
        from aethos_core.failed_service_investigation.failed_service_diagnosis import fetch_railway_logs_multisource

        return fetch_railway_logs_multisource(
            service_name=str(target.get("service") or target.get("service_name") or ""),
            service_id=str(target.get("service_id") or "") or None,
            limit=limit,
            bypass_cache=True,
        )

    def fetch_events(self, *, target: dict[str, Any], limit: int = 20) -> dict[str, Any]:
        from aethos_core.providers.railway.operations.service_events_api import get_service_events

        return get_service_events(target, limit=limit)

    def fetch_health(self, *, target: dict[str, Any] | None = None) -> dict[str, Any]:
        from aethos_core.operational_planner.adapters.railway_wide_health import collect_railway_service_health_rows

        rows, error = collect_railway_service_health_rows()
        return {"ok": bool(rows), "rows": rows, "error": error}

    def classify_failure(self, *, logs: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
        from aethos_core.failed_service_investigation.root_cause_classifier import classify_root_cause

        result = classify_root_cause(
            logs=logs,
            service_name=str(target.get("service") or ""),
            deployment_state=str(target.get("deployment_state") or target.get("status") or ""),
        )
        return result.to_dict()

    def verify_restart(self, *, target: dict[str, Any]) -> dict[str, Any]:
        logs = self.fetch_logs(target=target, limit=10)
        return {"ok": bool(logs.get("ok")), "logs": logs.get("logs") or [], "source": "railway_capability_adapter"}

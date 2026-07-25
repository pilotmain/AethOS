# SPDX-License-Identifier: Apache-2.0
"""Railway read-only execution adapter."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.readonly_execution_adapter import ReadonlyExecutionAdapter
from aethos_core.providers.railway.operations.deployments_api import fetch_deployments, format_deployments_output
from aethos_core.providers.railway.operations.logs_api import fetch_service_logs, format_logs_output
from aethos_core.providers.railway.operations.services_api import fetch_service_details, format_service_details_output


class RailwayReadonlyExecutionAdapter(ReadonlyExecutionAdapter):
    provider = "railway"

    def __init__(self, token: str, *, credential_id: str = "") -> None:
        self._token = token
        self._credential_id = credential_id

    def get_deployments(self, *, project_name: str, limit: int = 20) -> dict[str, Any]:
        payload = fetch_deployments(self._token, service_name=project_name, limit=limit)
        payload["output"] = format_deployments_output(payload)
        return payload

    def get_domains(self, *, project_name: str) -> dict[str, Any]:
        return {"ok": False, "source": "provider_api", "error": "Railway domains read is not enabled yet.", "domains": []}

    def get_project_details(self, *, project_name: str) -> dict[str, Any]:
        payload = fetch_service_details(self._token, service_name=project_name)
        payload["output"] = format_service_details_output(payload)
        return payload

    def get_deployment_logs(
        self,
        *,
        project_name: str,
        deployment_id: str | None = None,
        project_id: str | None = None,
        team_id: str | None = None,
    ) -> dict[str, Any]:
        _ = project_id, team_id
        payload = fetch_service_logs(self._token, service_name=project_name, deployment_id=deployment_id)
        payload["output"] = format_logs_output(payload)
        return payload

    def get_service_events(self, *, service_name: str, limit: int = 20) -> dict[str, Any]:
        from aethos_core.providers.railway.operations.service_events_api import fetch_service_events

        payload = fetch_service_events(self._token, service_name=service_name, limit=limit)
        return payload


def adapter_from_credential(credential_id: str) -> RailwayReadonlyExecutionAdapter | None:
    from aethos_core.providers.railway.auth import RailwayAuthAdapter

    token = RailwayAuthAdapter().get_api_token(credential_id)
    if not token:
        return None
    return RailwayReadonlyExecutionAdapter(token, credential_id=credential_id)

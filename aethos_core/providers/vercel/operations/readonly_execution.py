# SPDX-License-Identifier: Apache-2.0
"""Vercel read-only execution adapter — API-first, browser fallback for gaps."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.readonly_execution_adapter import ReadonlyExecutionAdapter
from aethos_core.providers.vercel.operations.deployments_api import (
    fetch_deployments,
    format_deployments_output,
)
from aethos_core.providers.vercel.operations.domains_api import fetch_domains, format_domains_output
from aethos_core.providers.vercel.operations.logs_api import fetch_deployment_logs, format_logs_output
from aethos_core.providers.vercel.operations.project_details_api import (
    fetch_project_details,
    format_project_details_output,
)


class VercelReadonlyExecutionAdapter(ReadonlyExecutionAdapter):
    provider = "vercel"

    def __init__(self, token: str, *, credential_id: str = "") -> None:
        self._token = token
        self._credential_id = credential_id

    def get_deployments(self, *, project_name: str, limit: int = 20) -> dict[str, Any]:
        payload = fetch_deployments(self._token, project_name=project_name, limit=limit)
        payload["output"] = format_deployments_output(payload)
        return payload

    def get_domains(self, *, project_name: str) -> dict[str, Any]:
        payload = fetch_domains(self._token, project_name=project_name)
        payload["output"] = format_domains_output(payload)
        return payload

    def get_project_details(self, *, project_name: str) -> dict[str, Any]:
        payload = fetch_project_details(self._token, project_name=project_name)
        payload["output"] = format_project_details_output(payload)
        return payload

    def get_deployment_logs(
        self,
        *,
        project_name: str,
        deployment_id: str | None = None,
        project_id: str | None = None,
        team_id: str | None = None,
    ) -> dict[str, Any]:
        payload = fetch_deployment_logs(
            self._token,
            project_name=project_name,
            deployment_id=deployment_id,
            project_id=project_id,
            team_id=team_id,
        )
        payload["output"] = format_logs_output(payload)
        return payload

    def get_env_metadata(self, *, project_name: str) -> dict[str, Any]:
        from aethos_core.providers.vercel.operations.env_metadata_api import fetch_env_metadata, format_env_metadata_output

        payload = fetch_env_metadata(self._token, project_name=project_name)
        payload["output"] = format_env_metadata_output(payload)
        return payload


def adapter_from_credential(credential_id: str) -> VercelReadonlyExecutionAdapter | None:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    token = VercelAuthAdapter().get_api_token(credential_id)
    if not token:
        return None
    return VercelReadonlyExecutionAdapter(token, credential_id=credential_id)

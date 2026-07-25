# SPDX-License-Identifier: Apache-2.0
"""FIX 113 — Railway serviceInstanceRedeploy (deploy trigger only)."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import list_service_deployments
from aethos_core.providers.railway.operations.mutations_api import submit_service_instance_redeploy
from aethos_core.security.secret_redaction import redact_text


def _latest_deployment_for_service(token: str, *, service_id: str) -> dict[str, str]:
    deployments = list_service_deployments(token, service_id=service_id, limit=1)
    if not deployments:
        return {}
    latest = deployments[0] if isinstance(deployments[0], dict) else {}
    return {
        "deployment_id": str(latest.get("id") or ""),
        "deployment_url": str(latest.get("url") or latest.get("staticUrl") or ""),
        "deployment_status": str(latest.get("status") or ""),
    }


def trigger_service_instance_deploy(
    token: str,
    *,
    environment_id: str,
    service_id: str,
) -> dict[str, Any]:
    """
    Submit governed deploy trigger via serviceInstanceRedeploy.

    Returns deployment/provider request id metadata — never secret values.
    """
    result = submit_service_instance_redeploy(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    latest = _latest_deployment_for_service(token, service_id=service_id) if result.get("ok") else {}
    deployment_id = str(latest.get("deployment_id") or "").strip()
    return {
        "ok": bool(result.get("ok")),
        "detail": redact_text(str(result.get("detail") or "")),
        "graphql_operation": str(result.get("graphql_operation") or "serviceInstanceRedeploy"),
        "deployment_id": deployment_id,
        "deployment_url": str(latest.get("deployment_url") or ""),
        "deployment_status": str(latest.get("deployment_status") or ""),
        "provider_request_id": deployment_id or None,
        "environment_id": environment_id,
        "service_id": service_id,
        "graphql_errors": result.get("graphql_errors"),
    }

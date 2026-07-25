# SPDX-License-Identifier: Apache-2.0
"""FIX 114 — Read-only Railway deployment/runtime verification (no mutations)."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import list_service_deployments
from aethos_core.security.secret_redaction import redact_text

_VERIFY_RUNTIME_SUCCESS_STATES = frozenset(
    {"success", "succeeded", "completed", "active", "running", "deployed", "ready"}
)
_VERIFY_RUNTIME_FAILURE_STATES = frozenset(
    {"failed", "failure", "crashed", "error", "cancelled", "canceled", "removed"}
)


def normalize_deployment_state(state: str) -> str:
    return (state or "").strip().lower()


def deployment_state_is_healthy(state: str) -> bool:
    normalized = normalize_deployment_state(state)
    if normalized in _VERIFY_RUNTIME_FAILURE_STATES:
        return False
    return normalized in _VERIFY_RUNTIME_SUCCESS_STATES


def read_deployment_runtime_status(
    token: str,
    *,
    service_id: str,
    deployment_id: str,
) -> dict[str, Any]:
    """
    Read-only: resolve deployment state for a service (never triggers deploy/restart).

    Matches deployment_id when provided; otherwise uses latest deployment.
    """
    deployments = list_service_deployments(token, service_id=service_id, limit=20)
    if not deployments:
        return {
            "ok": False,
            "detail": "no deployments returned for service",
            "deployments_observed": 0,
        }

    target_id = (deployment_id or "").strip()
    matched: dict[str, Any] | None = None
    if target_id:
        for row in deployments:
            if str(row.get("id") or "") == target_id:
                matched = row
                break
    if matched is None:
        matched = deployments[0]

    state = normalize_deployment_state(str(matched.get("state") or ""))
    healthy = deployment_state_is_healthy(state)
    return {
        "ok": True,
        "detail": "deployment status read from Railway API (read-only)",
        "deployment_id": str(matched.get("id") or ""),
        "deployment_state": state,
        "deployment_healthy": healthy,
        "branch": str(matched.get("branch") or ""),
        "commit": str(matched.get("commit") or ""),
        "created_at": matched.get("created_at"),
        "deployments_observed": len(deployments),
        "error_message": redact_text(str(matched.get("error_message") or ""))[:200],
    }

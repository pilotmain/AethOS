# SPDX-License-Identifier: Apache-2.0
"""Shared provider orchestration runtime — readonly + mutation modes."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.orchestration.registry_runtime import (
    resolve_provider_execution_auth,
    resolve_readonly_execution_adapter,
)
from aethos_core.providers.base.provider_registry import ProviderRegistry

# Auth fallback operation when mutation ops are not in capability matrix lookups.
_AUTH_FALLBACK_OPERATION: dict[str, str] = {
    "railway": "read_projects",
    "github": "workflow_runs",
    "vercel": "read_projects",
}


def resolve_execution_auth(*, provider: str, operation_type: str, params: dict[str, Any]) -> dict[str, Any]:
    """Unified execution auth — same fallback behavior as readonly runners."""
    if provider == "railway":
        from aethos_core.operations.railway_operation_capabilities import resolve_execution_auth as railway_auth

        return railway_auth(operation_type, params)
    if provider == "github":
        from aethos_core.operations.github_operation_capabilities import resolve_execution_auth as github_auth

        auth_op = operation_type if operation_type != "workflow_rerun" else "workflow_runs"
        merged = dict(params)
        merged.setdefault("operation_type", auth_op)
        return github_auth(auth_op, merged)
    if provider == "vercel":
        from aethos_core.operations.execution.execution_runner import resolve_execution_auth as vercel_auth

        return vercel_auth(operation_type, params)

    stamped = {
        "auth_method": str(params.get("auth_method") or ""),
        "auth_method_label": str(params.get("auth_method_label") or ""),
        "credential_id": str(params.get("credential_id") or ""),
        "browser_used": bool(params.get("browser_used")),
    }
    if stamped["credential_id"]:
        return stamped
    return resolve_provider_execution_auth(provider)


def get_provider_api_token(*, provider: str, auth: dict[str, Any], require_validated: bool = True) -> str | None:
    credential_id = str(auth.get("credential_id") or "")
    if not credential_id:
        fallback_op = _AUTH_FALLBACK_OPERATION.get(provider, "read_projects")
        resolved = resolve_execution_auth(
            provider=provider,
            operation_type=fallback_op,
            params={"operation_type": fallback_op},
        )
        credential_id = str(resolved.get("credential_id") or "")
    if not credential_id:
        return None
    if require_validated:
        from aethos_core.connections.credential_runtime_gate import check_credential_gate

        gate = check_credential_gate(credential_id, provider=provider, require_validated=True)
        if not gate.get("ok"):
            return None
    spec = ProviderRegistry.get(provider)
    if not spec:
        return None
    token = spec.auth_adapter.get_api_token(credential_id)
    return str(token) if token else None


def resolve_readonly_adapter(*, provider: str, auth: dict[str, Any]) -> Any | None:
    credential_id = str(auth.get("credential_id") or "")
    if not credential_id:
        return None
    return resolve_readonly_execution_adapter(provider, credential_id)


def stamp_execution_auth(*, provider: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Approval-time auth stamp — registry-backed, shared by readonly + mutation."""
    _ = params
    return resolve_provider_execution_auth(provider)

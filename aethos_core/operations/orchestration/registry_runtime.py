# SPDX-License-Identifier: Apache-2.0
"""Registry-backed runtime resolution — Phase 9.3M convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.auth_labels import auth_method_label, auth_method_label_for_provider
from aethos_core.providers.base.capability_matrix import OperationCapability
from aethos_core.providers.base.provider_registry import ProviderRegistry

# Default readonly auth operations per provider (adapter edge — not unified semantics).
_DEFAULT_READONLY_AUTH_OPERATION: dict[str, str] = {
    "railway": "read_projects",
    "github": "read_repos",
    "vercel": "read_projects",
}


def get_operation_capability(provider: str, operation_type: str) -> OperationCapability | None:
    """Lookup provider operation capability via ProviderRegistry."""
    return ProviderRegistry.get_operation_capability(provider, operation_type)


def preflight_capability_metadata(provider: str, operation_type: str) -> dict[str, Any]:
    """Resolve preflight approval metadata via registry — provider fn remains authoritative."""
    spec = ProviderRegistry.get(provider)
    if not spec or not spec.preflight_capability_metadata_fn:
        return {}
    return spec.preflight_capability_metadata_fn(operation_type)


def resolve_readonly_execution_adapter(provider: str, credential_id: str) -> Any | None:
    """Resolve a provider readonly execution adapter via ProviderRegistry."""
    if not credential_id:
        return None
    spec = ProviderRegistry.get(provider)
    if not spec or not spec.readonly_execution_factory:
        return None
    return spec.readonly_execution_factory(credential_id)


def resolve_provider_execution_auth(provider: str) -> dict[str, Any]:
    """Resolve execution auth metadata for preflight approval via ProviderRegistry."""
    if provider == "local":
        return {}

    spec = ProviderRegistry.get(provider)
    if not spec:
        return {}

    operation = _DEFAULT_READONLY_AUTH_OPERATION.get(provider, "read_projects")
    resolved = spec.auth_adapter.resolve_best_auth_method(operation=operation)
    method = str(resolved.get("method") or "")

    if method == "api_token":
        cid = str(resolved.get("credential_id") or "")
        label = (
            auth_method_label_for_provider(provider, "api_token")
            if provider in ("railway", "github")
            else auth_method_label("api_token")
        )
        return {
            "auth_method": "api_token",
            "auth_method_label": label,
            "credential_id": cid,
            "browser_used": False,
        }

    if method == "browser" and provider == "vercel":
        return {
            "auth_method": "browser",
            "auth_method_label": auth_method_label("browser"),
            "browser_used": True,
        }

    if provider in ("railway", "github"):
        label = auth_method_label_for_provider(provider, method or None)
    else:
        label = auth_method_label(method or None)
    return {
        "auth_method": method or "none",
        "auth_method_label": label,
    }

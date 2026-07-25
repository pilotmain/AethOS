# SPDX-License-Identifier: Apache-2.0
"""Vercel operation capability matrix — API-first vs browser fallback."""

from __future__ import annotations

from typing import Any

import aethos_core.providers  # noqa: F401 — bootstrap registry

from aethos_core.connections.auth_labels import auth_method_label
from aethos_core.providers.base.capability_matrix import OperationCapability, is_api_capable as _is_api_capable
from aethos_core.providers.base.provider_registry import ProviderRegistry
from aethos_core.providers.vercel.provider import VERCEL_LEGACY_CAPABILITIES

# Backward-compatible alias for tests and legacy imports.
VERCEL_OPERATION_CAPABILITIES: dict[str, dict[str, Any]] = VERCEL_LEGACY_CAPABILITIES


def _vercel_cap(operation_type: str) -> OperationCapability | None:
    cap = ProviderRegistry.get_operation_capability("vercel", operation_type)
    if cap is not None:
        return cap
    raw = VERCEL_LEGACY_CAPABILITIES.get(operation_type)
    if not raw:
        return None
    from aethos_core.providers.base.capability_matrix import normalize_legacy_capability

    return normalize_legacy_capability(operation_type, raw)


def operation_capabilities(operation_type: str) -> dict[str, Any]:
    cap = _vercel_cap(operation_type)
    if cap is None:
        return {}
    legacy = VERCEL_LEGACY_CAPABILITIES.get(operation_type, {})
    return {**legacy, **cap.to_dict()}


def is_api_capable(operation_type: str) -> bool:
    cap = _vercel_cap(operation_type)
    if cap is None:
        return False
    return _is_api_capable(cap)


def browser_fallback_only(operation_type: str) -> bool:
    cap = _vercel_cap(operation_type)
    if cap is None:
        return False
    return cap.browser_fallback == "fallback"


def is_api_only_operation(operation_type: str) -> bool:
    cap = _vercel_cap(operation_type)
    if cap is None:
        return False
    from aethos_core.providers.base.capability_matrix import is_api_only

    return is_api_only(cap)


def execution_allows_browser_fallback(operation_type: str) -> bool:
    return browser_fallback_only(operation_type)


def browser_runtime_available() -> bool:
    from aethos_core.runtime.browser_runtime import browser_inventory_refresh_blocked_reason

    blocked, _reason = browser_inventory_refresh_blocked_reason(probe_launch=False)
    return not blocked


def should_attempt_browser_fallback(operation_type: str) -> bool:
    return execution_allows_browser_fallback(operation_type) and browser_runtime_available()


def resolve_execution_auth(operation_type: str, params: dict[str, Any]) -> dict[str, Any]:
    """Merge explicit execution params with live Vercel auth resolution."""
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    auth_method = str(params.get("auth_method") or "")
    credential_id = str(params.get("credential_id") or "")
    auth_label = str(params.get("auth_method_label") or "")

    if not credential_id and is_api_capable(operation_type):
        resolved = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
        if resolved.get("method") == "api_token":
            auth_method = "api_token"
            credential_id = str(resolved.get("credential_id") or "")
            auth_label = auth_method_label("api_token")

    if not auth_label and auth_method:
        auth_label = auth_method_label(auth_method)

    return {
        "auth_method": auth_method,
        "auth_method_label": auth_label,
        "credential_id": credential_id,
        "browser_used": False,
    }


def browser_runtime_required(operation_type: str, *, api_token_available: bool) -> bool:
    if api_token_available and is_api_capable(operation_type):
        return False
    cap = _vercel_cap(operation_type)
    if cap is None:
        return not api_token_available
    if cap.browser_required is False:
        if cap.browser_fallback == "fallback" and not api_token_available:
            return True
        return False
    return not api_token_available


def preflight_capability_metadata(operation_type: str) -> dict[str, Any]:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    resolved = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
    api_token = resolved.get("method") == "api_token"
    api_cap = is_api_capable(operation_type)
    return {
        "auth_method": "api_token" if api_token else str(resolved.get("method") or "none"),
        "api_capable": api_cap and api_token,
        "browser_required": browser_runtime_required(operation_type, api_token_available=api_token),
        "browser_runtime_required": browser_runtime_required(operation_type, api_token_available=api_token),
        "browser_fallback_available": browser_fallback_only(operation_type),
        "credential_id": str(resolved.get("credential_id") or "") if api_token else "",
    }

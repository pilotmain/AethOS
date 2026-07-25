# SPDX-License-Identifier: Apache-2.0
"""Railway operation capability helpers."""

from __future__ import annotations

from typing import Any

import aethos_core.providers  # noqa: F401

from aethos_core.connections.auth_labels import auth_method_label_for_provider
from aethos_core.providers.base.capability_matrix import is_api_capable as _is_api_capable
from aethos_core.providers.base.provider_registry import ProviderRegistry


def _railway_cap(operation_type: str):
    return ProviderRegistry.get_operation_capability("railway", operation_type)


def is_api_capable(operation_type: str) -> bool:
    cap = _railway_cap(operation_type)
    return _is_api_capable(cap) if cap else False


def resolve_execution_auth(operation_type: str, params: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.railway.auth import RailwayAuthAdapter

    auth_method = str(params.get("auth_method") or "")
    credential_id = str(params.get("credential_id") or "")
    auth_label = str(params.get("auth_method_label") or "")
    if not credential_id and is_api_capable(operation_type):
        resolved = RailwayAuthAdapter().resolve_best_auth_method(operation="read_projects")
        if resolved.get("method") == "api_token":
            auth_method = "api_token"
            credential_id = str(resolved.get("credential_id") or "")
            auth_label = auth_method_label_for_provider("railway", "api_token")
    if not auth_label and auth_method:
        auth_label = auth_method_label_for_provider("railway", auth_method)
    return {
        "auth_method": auth_method,
        "auth_method_label": auth_label,
        "credential_id": credential_id,
        "browser_used": False,
    }


def preflight_capability_metadata(operation_type: str) -> dict[str, Any]:
    from aethos_core.providers.railway.auth import RailwayAuthAdapter

    resolved = RailwayAuthAdapter().resolve_best_auth_method(operation="read_projects")
    api_token = resolved.get("method") == "api_token"
    auth_method = "api_token" if api_token else str(resolved.get("method") or "none")
    return {
        "auth_method": auth_method,
        "auth_method_label": auth_method_label_for_provider("railway", auth_method),
        "api_capable": is_api_capable(operation_type) and api_token,
        "browser_required": False,
        "browser_runtime_required": False,
        "browser_fallback_available": False,
        "credential_id": str(resolved.get("credential_id") or "") if api_token else "",
    }

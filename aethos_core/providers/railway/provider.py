# SPDX-License-Identifier: Apache-2.0
"""Railway provider registration — second ProviderRegistry implementation."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.capability_matrix import OperationCapability, normalize_legacy_capability
from aethos_core.providers.railway.operations.mutation_adapter import RailwayMutationAdapter
from aethos_core.providers.base.credential_ui import RAILWAY_CREDENTIAL_UI
from aethos_core.providers.base.provider_registry import ProviderRegistry, ProviderSpec
from aethos_core.providers.railway.auth import RailwayAuthAdapter

RAILWAY_CAPABILITIES: dict[str, dict[str, Any]] = {
    "list_projects": {"api": True, "browser": False, "enabled": True},
    "list_deployments": {"api": True, "browser": False, "enabled": True},
    "project_details": {"api": True, "browser": False, "enabled": True},
    "check_logs": {"api": "partial", "browser": False, "enabled": True},
    "why_down": {"api": "partial", "browser": False, "enabled": True},
    "redeploy": {"mutation": True, "enabled": True, "api": True},
    "restart": {"mutation": True, "enabled": True, "api": True},
    "set_env_var": {"mutation": True, "enabled": True, "api": True},
}


def railway_capabilities() -> dict[str, OperationCapability]:
    return {op: normalize_legacy_capability(op, raw) for op, raw in RAILWAY_CAPABILITIES.items()}


def register_railway_provider() -> ProviderSpec:
    from aethos_core.operations.railway_operation_capabilities import preflight_capability_metadata
    from aethos_core.providers.railway.inventory.inventory_adapter import RailwayInventoryAdapter
    from aethos_core.providers.railway.operations.readonly_execution import adapter_from_credential

    spec = ProviderSpec(
        name="railway",
        label="Railway",
        category="cloud",
        auth_adapter=RailwayAuthAdapter(),
        capabilities=railway_capabilities(),
        mutation_adapter=RailwayMutationAdapter(),
        readonly_execution_factory=adapter_from_credential,
        preflight_capability_metadata_fn=preflight_capability_metadata,
        inventory_adapter_factory=RailwayInventoryAdapter,
        credential_ui=RAILWAY_CREDENTIAL_UI,
    )
    ProviderRegistry.register(spec)
    return spec


def ensure_railway_registered() -> ProviderSpec:
    existing = ProviderRegistry.get("railway")
    if existing:
        return existing
    return register_railway_provider()

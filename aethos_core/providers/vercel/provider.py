# SPDX-License-Identifier: Apache-2.0
"""Vercel provider registration — first implementation of generic contracts."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.capability_matrix import OperationCapability, normalize_legacy_capability
from aethos_core.providers.vercel.operations.mutation_adapter import VercelMutationAdapter
from aethos_core.providers.base.credential_ui import VERCEL_CREDENTIAL_UI
from aethos_core.providers.base.provider_registry import ProviderRegistry, ProviderSpec
from aethos_core.providers.vercel.auth import VercelAuthAdapter

VERCEL_LEGACY_CAPABILITIES: dict[str, dict[str, Any]] = {
    "list_domains": {"api": True, "browser": False, "browser_required": False},
    "list_deployments": {"api": True, "browser": False, "browser_required": False},
    "project_details": {"api": True, "browser": False, "browser_required": False},
    "env_metadata": {"api": True, "browser": False, "browser_required": False},
    "check_logs": {"api": "partial", "browser": "fallback", "browser_required": False},
    "why_down": {"api": "partial", "browser": "fallback", "browser_required": False},
    "inspect_failed_deployment": {"api": "partial", "browser": "fallback", "browser_required": False},
    "redeploy": {"mutation": True, "enabled": True, "api": True, "browser_required": False},
    # rollback / promote_deployment are also "expanding · wiring in progress" in the
    # expansion registry — keep the legacy dict honest (not enabled) to match.
    "rollback": {"mutation": True, "enabled": False, "api": True, "browser_required": False},
    "restart": {"mutation": True, "enabled": True, "api": True, "browser_required": False},
    # set_env_var / remove_env_var are "expanding · wiring in progress" in the
    # authoritative expansion registry (vercel/expansion/capability_registry.py),
    # so they are NOT enabled here — the legacy dict must not overclaim them ready.
    "set_env_var": {"mutation": True, "enabled": False, "api": True, "browser_required": False},
    "remove_env_var": {"mutation": True, "enabled": False, "api": True, "browser_required": False},
    "promote_deployment": {"mutation": True, "enabled": False, "api": True, "browser_required": False},
    "deploy_from_git": {"mutation": True, "enabled": True, "api": True, "browser_required": False},
}


def vercel_capabilities() -> dict[str, OperationCapability]:
    return {
        op: normalize_legacy_capability(op, raw)
        for op, raw in VERCEL_LEGACY_CAPABILITIES.items()
    }


def register_vercel_provider() -> ProviderSpec:
    from aethos_core.operations.vercel_operation_capabilities import preflight_capability_metadata
    from aethos_core.providers.vercel.operations.readonly_execution import adapter_from_credential

    auth = VercelAuthAdapter()
    spec = ProviderSpec(
        name="vercel",
        label="Vercel",
        category="cloud",
        auth_adapter=auth,
        capabilities=vercel_capabilities(),
        mutation_adapter=VercelMutationAdapter(),
        readonly_execution_factory=adapter_from_credential,
        preflight_capability_metadata_fn=preflight_capability_metadata,
        credential_ui=VERCEL_CREDENTIAL_UI,
    )
    ProviderRegistry.register(spec)
    return spec


def ensure_vercel_registered() -> ProviderSpec:
    existing = ProviderRegistry.get("vercel")
    if existing:
        return existing
    return register_vercel_provider()

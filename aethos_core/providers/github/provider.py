# SPDX-License-Identifier: Apache-2.0
"""GitHub provider registration."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.capability_matrix import OperationCapability, normalize_legacy_capability
from aethos_core.providers.github.mutations.github_mutation_adapter import GitHubMutationAdapter
from aethos_core.providers.base.credential_ui import GITHUB_CREDENTIAL_UI
from aethos_core.providers.base.provider_registry import ProviderRegistry, ProviderSpec
from aethos_core.providers.github.auth import GitHubAuthAdapter

GITHUB_CAPABILITIES: dict[str, dict[str, Any]] = {
    "repo_metadata": {"api": True, "browser": False, "enabled": True},
    "inspect_repo": {"api": True, "browser": False, "enabled": True},
    "branch_status": {"api": True, "browser": False, "enabled": True},
    "recent_commits": {"api": True, "browser": False, "enabled": True},
    "failed_checks": {"api": True, "browser": False, "enabled": True},
    "workflow_runs": {"api": True, "browser": False, "enabled": True},
    "workflow_diagnostic": {"api": True, "browser": False, "enabled": True},
    "workflow_jobs": {"api": True, "browser": False, "enabled": True},
    "workflow_logs": {"api": "partial", "browser": False, "enabled": True},
    "actions_failure_diagnostic": {"api": True, "browser": False, "enabled": True},
    "commit_evidence": {"api": True, "browser": False, "enabled": False},
    "why_down": {"api": "partial", "browser": False, "enabled": False},
    "workflow_rerun": {"mutation": True, "enabled": True, "api": True},
    "create_branch": {"mutation": True, "enabled": True, "api": True},
    "commit_changes": {"mutation": True, "enabled": True, "api": True},
    "push_branch": {"mutation": True, "enabled": True, "api": True},
    "open_pr": {"mutation": True, "enabled": True, "api": True},
    "cancel_workflow": {"mutation": True, "enabled": True, "api": True},
    "redeploy": {"mutation": True, "enabled": True, "api": True},
}


def github_capabilities() -> dict[str, OperationCapability]:
    return {op: normalize_legacy_capability(op, raw) for op, raw in GITHUB_CAPABILITIES.items()}


def register_github_provider() -> ProviderSpec:
    from aethos_core.operations.github_operation_capabilities import preflight_capability_metadata
    from aethos_core.providers.github.inventory.inventory_adapter import GitHubInventoryAdapter
    from aethos_core.providers.github.operations.readonly_execution import adapter_from_credential

    spec = ProviderSpec(
        name="github",
        label="GitHub",
        category="code",
        auth_adapter=GitHubAuthAdapter(),
        capabilities=github_capabilities(),
        mutation_adapter=GitHubMutationAdapter(),
        readonly_execution_factory=adapter_from_credential,
        preflight_capability_metadata_fn=preflight_capability_metadata,
        inventory_adapter_factory=GitHubInventoryAdapter,
        credential_ui=GITHUB_CREDENTIAL_UI,
    )
    ProviderRegistry.register(spec)
    return spec


def ensure_github_registered() -> ProviderSpec:
    existing = ProviderRegistry.get("github")
    if existing:
        return existing
    return register_github_provider()

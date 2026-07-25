# SPDX-License-Identifier: Apache-2.0
"""AWS provider registration — readonly-first (P4)."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.aws.auth import AwsAuthAdapter
from aethos_core.providers.base.capability_matrix import OperationCapability, normalize_legacy_capability
from aethos_core.providers.base.credential_ui import AWS_CREDENTIAL_UI
from aethos_core.providers.base.provider_registry import ProviderRegistry, ProviderSpec

AWS_CAPABILITIES: dict[str, dict[str, Any]] = {
    "validate_identity": {"api": True, "enabled": True, "read_only": True},
    "list_regions": {"api": True, "enabled": True, "read_only": True},
    "list_ecs_services": {"api": True, "enabled": True, "read_only": True},
    "list_lambda_functions": {"api": True, "enabled": True, "read_only": True},
    "list_api_gateway_apis": {"api": True, "enabled": True, "read_only": True},
    "list_cloudwatch_logs": {"api": True, "enabled": True, "read_only": True},
}


def aws_capabilities() -> dict[str, OperationCapability]:
    return {op: normalize_legacy_capability(op, raw) for op, raw in AWS_CAPABILITIES.items()}


def register_aws_provider() -> ProviderSpec:
    spec = ProviderSpec(
        name="aws",
        label="AWS",
        category="cloud",
        auth_adapter=AwsAuthAdapter(),
        capabilities=aws_capabilities(),
        mutation_adapter=None,
        credential_ui=AWS_CREDENTIAL_UI,
    )
    ProviderRegistry.register(spec)
    return spec


def ensure_aws_registered() -> ProviderSpec:
    existing = ProviderRegistry.get("aws")
    if existing:
        return existing
    return register_aws_provider()

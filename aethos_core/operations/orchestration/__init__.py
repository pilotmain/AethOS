# SPDX-License-Identifier: Apache-2.0
"""Shared orchestration utilities — Phase 9.3M convergence entry point."""

from aethos_core.operations.orchestration.preflight_builder import (
    GITHUB_PREFLIGHT_PROFILE,
    RAILWAY_PREFLIGHT_PROFILE,
    build_api_readonly_resolved_preflight,
    build_ambiguous_target_preflight,
)
from aethos_core.operations.orchestration.registry_runtime import (
    get_operation_capability,
    preflight_capability_metadata,
    resolve_provider_execution_auth,
    resolve_readonly_execution_adapter,
)

__all__ = [
    "GITHUB_PREFLIGHT_PROFILE",
    "RAILWAY_PREFLIGHT_PROFILE",
    "build_ambiguous_target_preflight",
    "build_api_readonly_resolved_preflight",
    "get_operation_capability",
    "preflight_capability_metadata",
    "resolve_provider_execution_auth",
    "resolve_readonly_execution_adapter",
]

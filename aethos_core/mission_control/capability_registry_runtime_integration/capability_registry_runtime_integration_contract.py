# SPDX-License-Identifier: Apache-2.0
"""FIX 296 — capability registry runtime integration contract."""

from __future__ import annotations

from typing import Final

CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_FIX: Final[str] = "FIX 296"

CAPABILITY_ANSWERING_AUTHORITY_FIX_296: Final[bool] = False
AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_296: Final[bool] = False
PROVIDER_AUTHORITY_FIX_296: Final[bool] = False
MUTATION_PERFORMED_FIX_296: Final[bool] = False
EXECUTION_PERFORMED_FIX_296: Final[bool] = False

CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_ROUTE_ID: Final[str] = (
    "mission_control_capability_registry_runtime_integration"
)

CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_INVARIANT: Final[str] = (
    "capability_registry_runtime_integration_answers_from_evidence_without_capability_authority"
)

PLATFORM_CAPABILITY_SECTIONS: Final[tuple[str, ...]] = (
    "governance",
    "software_delivery",
    "operations",
    "repository_intelligence",
    "product_intelligence",
    "lifecycle_and_business_intelligence",
    "multi_tenant_platform_readiness",
    "provider_readiness",
    "limitations",
)

RUNTIME_ANSWER_SECTIONS: Final[tuple[str, ...]] = (
    "capability_summary",
    "proven_capabilities",
    "operational_capabilities",
    "experimental_capabilities",
    "planned_blocked_capabilities",
    "provider_capability_matrix",
    "repository_trust_matrix",
    "authority_boundaries",
)

PROVEN_STATUSES: Final[frozenset[str]] = frozenset(
    {"PROVEN", "CONDITIONALLY_TRUSTED", "OPERATIONAL"}
)
OPERATIONAL_STATUSES: Final[frozenset[str]] = frozenset({"OPERATIONAL"})
EXPERIMENTAL_STATUSES: Final[frozenset[str]] = frozenset({"EXPERIMENTAL", "IMPLEMENTED"})
PLANNED_STATUSES: Final[frozenset[str]] = frozenset({"PLANNED", "BLOCKED", "DEPRECATED"})

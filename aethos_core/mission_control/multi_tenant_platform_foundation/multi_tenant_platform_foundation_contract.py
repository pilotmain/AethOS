# SPDX-License-Identifier: Apache-2.0
"""FIX 300 — multi-tenant platform foundation contract."""

from __future__ import annotations

from typing import Final

MULTI_TENANT_PLATFORM_FOUNDATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_multi_tenant_platform_foundation_v1"
)
MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_multi_tenant_platform_foundation_record_v1"
)
MULTI_TENANT_PLATFORM_FOUNDATION_FIX: Final[str] = "FIX 300"

MUTATION_PERFORMED_FIX_300: Final[bool] = False
EXECUTION_PERFORMED_FIX_300: Final[bool] = False
TENANT_AUTHORITY_FIX_300: Final[bool] = False
AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300: Final[bool] = False
CROSS_TENANT_ACCESS_ENABLED_FIX_300: Final[bool] = False
CROSS_TENANT_TRUST_ENABLED_FIX_300: Final[bool] = False
PERMISSION_ESCALATION_ENABLED_FIX_300: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_300: Final[bool] = False
REPOSITORY_MUTATION_AUTHORITY_FIX_300: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_300: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_300: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_300: Final[bool] = False
MERGE_AUTHORITY_FIX_300: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_300: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_300: Final[bool] = False
MULTI_TENANT_PLATFORM_COMPOSES_EVIDENCE_ONLY_FIX_300: Final[bool] = True

MULTI_TENANT_PLATFORM_FOUNDATION_ROUTE_ID: Final[str] = (
    "mission_control_multi_tenant_platform_foundation"
)
MULTI_TENANT_PLATFORM_FOUNDATION_ORIGIN: Final[str] = (
    "mission_control_multi_tenant_platform_foundation"
)

MULTI_TENANT_PLATFORM_FOUNDATION_INVARIANT: Final[str] = (
    "multi_tenant_platform_foundation_models_tenancy_without_governance_bypass"
)

TENANT_DOMAINS: Final[tuple[str, ...]] = (
    "organizations",
    "workspaces",
    "projects",
    "identity",
    "roles",
    "permissions",
    "trust_boundaries",
    "governance_isolation",
    "onboarding",
    "channels",
)

TENANT_ROLES: Final[tuple[str, ...]] = (
    "OWNER",
    "ADMIN",
    "OPERATOR",
    "REVIEWER",
    "OBSERVER",
)

TENANT_PERMISSIONS: Final[tuple[str, ...]] = (
    "view",
    "review",
    "approve",
    "operate",
    "administer",
    "govern",
)

TENANT_CHANNELS: Final[tuple[str, ...]] = (
    "web",
    "telegram",
    "slack",
    "email",
    "voice",
)

HUMAN_TENANT_DECISION_KINDS: Final[tuple[str, ...]] = (
    "human_tenant_decision_approve",
    "human_tenant_decision_hold",
    "human_tenant_decision_reject",
    "human_tenant_decision_defer",
)

MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "organization_create_review_note",
    "workspace_create_review_note",
    "project_registration_review_note",
    "membership_review_note",
    "tenant_governance_review_note",
    *HUMAN_TENANT_DECISION_KINDS,
    "multi_tenant_platform_foundation_record",
)

TENANT_ROLE_MAP: Final[tuple[tuple[str, str], ...]] = (
    ("admin", "ADMIN"),
    ("operator", "OPERATOR"),
    ("reviewer", "REVIEWER"),
    ("viewer", "OBSERVER"),
)

MULTI_TENANT_PLATFORM_FOUNDATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("tenancy_not_bypass", "Multi-tenant platform ≠ governance bypass."),
    ("compose_only", "Composes existing org, workspace, identity, and capability evidence without re-execution."),
    ("isolated_trust", "Each organization maintains independent trust, governance, and evidence."),
    ("no_automatic_provisioning", "Tenant creation requires human review — never automatic."),
    ("no_cross_tenant_access", "Organization A cannot access Organization B records."),
    ("no_cross_tenant_trust", "Trust baselines do not inherit across tenants."),
    ("no_permission_escalation", "Permission escalation remains disabled at foundation layer."),
    ("channel_readiness", "Channels route into the same Mission Control core."),
    ("onboarding_guidance", "Onboarding explains capability discovery and trust boundaries."),
    ("human_review", "Human tenant reviews record decisions without provisioning execution."),
)

FORBIDDEN_TENANT_PLATFORM_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_tenant_creation", "Platform foundation never auto-creates tenants."),
    ("cross_tenant_access", "Platform foundation never grants cross-tenant access."),
    ("cross_tenant_trust_inheritance", "Platform foundation never inherits trust across tenants."),
    ("permission_escalation", "Platform foundation never escalates permissions."),
    ("governance_bypass", "Platform foundation never bypasses governance lanes."),
    ("repository_mutation", "Platform foundation never mutates repositories."),
    ("provider_mutation", "Platform foundation never mutates providers."),
    ("trust_mutation", "Platform foundation never mutates trust baselines."),
)

MULTI_TENANT_PLATFORM_FOUNDATION_EXECUTABLE: Final[bool] = False

MAX_MULTI_TENANT_PLATFORM_FOUNDATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_MULTI_TENANT_PLATFORM_FOUNDATION_RECORDS: Final[int] = 500

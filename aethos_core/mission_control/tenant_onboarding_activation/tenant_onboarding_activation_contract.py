# SPDX-License-Identifier: Apache-2.0
"""FIX 301 — tenant onboarding and activation contract."""

from __future__ import annotations

from typing import Final

TENANT_ONBOARDING_ACTIVATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_tenant_onboarding_activation_v1"
)
TENANT_ONBOARDING_ACTIVATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_tenant_onboarding_activation_record_v1"
)
TENANT_ONBOARDING_ACTIVATION_FIX: Final[str] = "FIX 301"

MUTATION_PERFORMED_FIX_301: Final[bool] = False
EXECUTION_PERFORMED_FIX_301: Final[bool] = False
ONBOARDING_AUTHORITY_FIX_301: Final[bool] = False
AUTOMATIC_PROVISIONING_ENABLED_FIX_301: Final[bool] = False
AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301: Final[bool] = False
SECRET_COLLECTION_ENABLED_FIX_301: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_301: Final[bool] = False
CROSS_TENANT_ACCESS_ENABLED_FIX_301: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_301: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_301: Final[bool] = False
TENANT_ONBOARDING_COMPOSES_EVIDENCE_ONLY_FIX_301: Final[bool] = True

TENANT_ONBOARDING_ACTIVATION_ROUTE_ID: Final[str] = (
    "mission_control_tenant_onboarding_activation"
)

TENANT_ONBOARDING_ACTIVATION_INVARIANT: Final[str] = (
    "tenant_onboarding_activation_guidance_without_platform_authority"
)

ONBOARDING_STEPS: Final[tuple[str, ...]] = (
    "organization_setup",
    "workspace_setup",
    "project_registration",
    "provider_connection",
    "capability_discovery",
    "trust_explanation",
    "first_mission_control_session",
)

ONBOARDING_STEP_LABELS: Final[tuple[tuple[str, str], ...]] = (
    ("organization_setup", "Organization setup"),
    ("workspace_setup", "Workspace setup"),
    ("project_registration", "Project registration"),
    ("provider_connection", "Provider connection"),
    ("capability_discovery", "Capability discovery"),
    ("trust_explanation", "Trust explanation"),
    ("first_mission_control_session", "First Mission Control session"),
)

HUMAN_ONBOARDING_DECISION_KINDS: Final[tuple[str, ...]] = (
    "onboarding_decision_approve",
    "onboarding_decision_hold",
    "onboarding_decision_reject",
    "onboarding_decision_defer",
)

TENANT_ONBOARDING_ACTIVATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "organization_setup_review_note",
    "workspace_setup_review_note",
    "project_registration_review_note",
    "provider_connection_note",
    *HUMAN_ONBOARDING_DECISION_KINDS,
    "tenant_onboarding_activation_record",
)

STEP_RECORD_KINDS: Final[tuple[tuple[str, str], ...]] = (
    ("organization_setup", "organization_setup_review_note"),
    ("workspace_setup", "workspace_setup_review_note"),
    ("project_registration", "project_registration_review_note"),
    ("provider_connection", "provider_connection_note"),
)

PROVIDER_CONNECTION_TARGETS: Final[tuple[str, ...]] = (
    "GitHub",
    "Railway",
    "Vercel",
)

FUTURE_PROVIDER_CONNECTION_TARGETS: Final[tuple[str, ...]] = (
    "AWS",
    "Azure",
    "GCP",
    "Kubernetes",
)

TENANT_ONBOARDING_ACTIVATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("onboarding_not_authority", "Onboarding guidance ≠ platform authority."),
    ("compose_only", "Composes FIX 300 tenancy and FIX 295/296 capability evidence without re-execution."),
    ("no_automatic_provisioning", "Organization, workspace, and project setup remain review artifacts."),
    ("no_secret_collection", "Provider connection guidance never collects secrets in chat."),
    ("no_provider_mutation", "Provider connection checklist is manual setup guidance only."),
    ("no_trust_mutation", "Trust explanation is read-only — never mutates trust baselines."),
    ("human_review", "Onboarding decisions record approve/hold/reject/defer without provisioning."),
    ("capability_discovery", "Capability discovery uses FIX 295 registry and FIX 296 runtime integration."),
    ("trust_explanation", "Trust explanation composes FIX 186–196 baselines and FIX 300 tenant trust registry."),
    ("first_value", "First Mission Control activation packet guides the first governed workflow entry."),
)

FORBIDDEN_ONBOARDING_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_organization_creation", "Onboarding never auto-creates organizations."),
    ("automatic_workspace_creation", "Onboarding never auto-creates workspaces."),
    ("automatic_user_invitation", "Onboarding never auto-invites users."),
    ("automatic_permission_grants", "Onboarding never grants permissions automatically."),
    ("automatic_provider_connection", "Onboarding never connects providers automatically."),
    ("secret_collection_in_chat", "Onboarding never requests secrets in chat."),
    ("cross_tenant_access", "Onboarding never grants cross-tenant access."),
    ("trust_mutation", "Onboarding never mutates trust baselines."),
    ("provider_mutation", "Onboarding never mutates providers."),
    ("repository_mutation", "Onboarding never mutates repositories."),
)

TENANT_ONBOARDING_ACTIVATION_EXECUTABLE: Final[bool] = False

MAX_TENANT_ONBOARDING_ACTIVATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_TENANT_ONBOARDING_ACTIVATION_RECORDS: Final[int] = 500

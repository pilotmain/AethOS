# SPDX-License-Identifier: Apache-2.0
"""FIX 306 — customer administration console contract."""

from __future__ import annotations

from typing import Final

CUSTOMER_ADMINISTRATION_CONSOLE_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_administration_console_v1"
)
CUSTOMER_ADMINISTRATION_CONSOLE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_administration_console_record_v1"
)
CUSTOMER_ADMINISTRATION_CONSOLE_FIX: Final[str] = "FIX 306"

MUTATION_PERFORMED_FIX_306: Final[bool] = False
EXECUTION_PERFORMED_FIX_306: Final[bool] = False
ADMINISTRATION_AUTHORITY_FIX_306: Final[bool] = False
AUTOMATIC_USER_CREATION_ENABLED_FIX_306: Final[bool] = False
AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306: Final[bool] = False
CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_306: Final[bool] = False
BILLING_MUTATION_AUTHORITY_FIX_306: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_306: Final[bool] = False
CUSTOMER_ADMINISTRATION_COMPOSES_EVIDENCE_ONLY_FIX_306: Final[bool] = True

CUSTOMER_ADMINISTRATION_CONSOLE_ROUTE_ID: Final[str] = (
    "mission_control_customer_administration_console"
)

CUSTOMER_ADMINISTRATION_CONSOLE_INVARIANT: Final[str] = (
    "customer_administration_console_visibility_without_administrative_authority"
)

ADMINISTRATION_DOMAINS: Final[tuple[str, ...]] = (
    "organization_administration",
    "user_administration",
    "role_administration",
    "workspace_administration",
    "project_administration",
    "provider_administration",
    "channel_administration",
    "billing_administration",
    "governance_administration",
    "customer_administration_dashboard",
)

ADMIN_ONLY_SURFACES: Final[tuple[str, ...]] = (
    "user_administration_report",
    "role_administration_report",
    "provider_administration_report",
    "billing_administration_report",
    "governance_administration_report",
)

HUMAN_ADMINISTRATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "administration_decision_approve",
    "administration_decision_hold",
    "administration_decision_reject",
    "administration_decision_defer",
)

CUSTOMER_ADMINISTRATION_CONSOLE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "administration_note",
    *HUMAN_ADMINISTRATION_DECISION_KINDS,
    "customer_administration_console_record",
)

CUSTOMER_ADMINISTRATION_CONSOLE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("visibility_not_authority", "Administration visibility ≠ administrative authority."),
    ("governed_actions", "Console provides visibility and governed actions — not bypass."),
    ("no_trust_mutation", "Console never mutates trust or bypasses approval flows."),
    ("no_authorization_bypass", "Console never bypasses authorization."),
    ("tenant_scoped", "Administration is scoped to the current organization only."),
    ("compose_fixes", "Composes FIX 300–305 without re-execution or mutation."),
    ("unified_control_plane", "Single place to understand org, users, projects, providers, channels, billing, governance."),
    ("human_review", "Administration review records decisions without automatic mutations."),
    ("no_user_creation", "No automatic user creation or permission granting."),
    ("managed_customer", "Moves from onboarded customer to managed customer through visibility."),
)

FORBIDDEN_ADMINISTRATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_user_creation", "Administration console never creates users automatically."),
    ("automatic_permission_grants", "Administration console never grants permissions automatically."),
    ("automatic_trust_promotion", "Administration console never promotes trust automatically."),
    ("automatic_provider_mutation", "Administration console never mutates providers automatically."),
    ("automatic_billing_mutation", "Administration console never mutates billing automatically."),
    ("cross_tenant_administration", "Administration console never administers across tenant boundaries."),
    ("authorization_bypass", "Administration console never bypasses authorization."),
    ("governance_bypass", "Administration console never bypasses governance approval flows."),
)

CUSTOMER_ADMINISTRATION_CONSOLE_EXECUTABLE: Final[bool] = False

MAX_CUSTOMER_ADMINISTRATION_CONSOLE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_CUSTOMER_ADMINISTRATION_CONSOLE_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 302 — identity and access hardening contract."""

from __future__ import annotations

from typing import Final

IDENTITY_ACCESS_HARDENING_SCHEMA_VERSION: Final[str] = (
    "mission_control_identity_access_hardening_v1"
)
IDENTITY_ACCESS_HARDENING_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_identity_access_hardening_record_v1"
)
IDENTITY_ACCESS_HARDENING_FIX: Final[str] = "FIX 302"

MUTATION_PERFORMED_FIX_302: Final[bool] = False
EXECUTION_PERFORMED_FIX_302: Final[bool] = False
AUTHORIZATION_AUTHORITY_FIX_302: Final[bool] = False
AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302: Final[bool] = False
AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302: Final[bool] = False
CROSS_TENANT_ACCESS_ENABLED_FIX_302: Final[bool] = False
AUTHORIZATION_BYPASS_ENABLED_FIX_302: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_302: Final[bool] = False
IDENTITY_ACCESS_COMPOSES_EVIDENCE_ONLY_FIX_302: Final[bool] = True

IDENTITY_ACCESS_HARDENING_ROUTE_ID: Final[str] = (
    "mission_control_identity_access_hardening"
)

IDENTITY_ACCESS_HARDENING_INVARIANT: Final[str] = (
    "identity_access_hardening_enforces_without_authority_escalation"
)

AUTHORIZATION_DOMAINS: Final[tuple[str, ...]] = (
    "identity_resolution",
    "permission_evaluation",
    "tenant_boundary_enforcement",
    "mission_control_authorization",
    "repository_access_controls",
    "governance_action_controls",
    "audit_trail",
    "least_privilege_analysis",
    "channel_authorization",
    "session_trust",
)

TENANT_PERMISSIONS: Final[tuple[str, ...]] = (
    "view",
    "review",
    "approve",
    "operate",
    "administer",
    "govern",
)

PLATFORM_ROLES: Final[tuple[str, ...]] = (
    "viewer",
    "operator",
    "reviewer",
    "admin",
)

TENANT_ROLE_LABELS: Final[tuple[tuple[str, str], ...]] = (
    ("viewer", "OBSERVER"),
    ("operator", "OPERATOR"),
    ("reviewer", "REVIEWER"),
    ("admin", "ADMIN"),
)

GOVERNANCE_ACTIONS: Final[tuple[str, ...]] = (
    "approval_recording",
    "trust_decision",
    "expansion_decision",
    "lifecycle_decision",
    "merge_decision",
    "deploy_decision",
    "rollback_decision",
)

GOVERNANCE_ACTION_PERMISSION: Final[tuple[tuple[str, str], ...]] = (
    ("approval_recording", "approve"),
    ("trust_decision", "govern"),
    ("expansion_decision", "govern"),
    ("lifecycle_decision", "operate"),
    ("merge_decision", "approve"),
    ("deploy_decision", "operate"),
    ("rollback_decision", "operate"),
)

MISSION_CONTROL_PROTECTED_SURFACES: Final[tuple[str, ...]] = (
    "mission_control_apis",
    "mission_control_actions",
    "mission_control_dashboards",
    "mission_control_records",
)

CHANNELS: Final[tuple[str, ...]] = (
    "web",
    "telegram",
    "slack",
    "email",
    "voice",
)

HUMAN_AUTHORIZATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "authorization_decision_approve",
    "authorization_decision_hold",
    "authorization_decision_reject",
    "authorization_decision_defer",
)

IDENTITY_ACCESS_HARDENING_RECORD_KINDS: Final[tuple[str, ...]] = (
    "authorization_note",
    *HUMAN_AUTHORIZATION_DECISION_KINDS,
    "identity_access_hardening_record",
)

IDENTITY_ACCESS_HARDENING_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("enforcement_not_escalation", "Authorization enforcement ≠ authority escalation."),
    ("compose_only", "Evaluates live org RBAC and tenant boundaries without granting permissions."),
    ("centralized_evaluation", "Every operation answers who, role, permission, tenant, trust, and allow/deny."),
    ("tenant_isolation", "Cross-tenant access and trust reads remain blocked."),
    ("least_privilege", "Detects unused, excessive, overlapping permissions and privilege drift."),
    ("governance_protection", "Governance actions require explicit permission checks."),
    ("channel_parity", "Channel identity maps to the same authorization model."),
    ("session_trust", "Authentication, membership, and trust state tracked read-only."),
    ("human_review", "Authorization review records decisions without self-granting."),
    ("no_bypass", "Hidden privilege elevation and authorization bypass remain forbidden."),
)

FORBIDDEN_AUTHORIZATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("permission_self_granting", "Authorization layer never grants itself permissions."),
    ("role_self_escalation", "Authorization layer never escalates roles automatically."),
    ("cross_tenant_access", "Authorization layer never allows cross-tenant access."),
    ("cross_tenant_trust_mutation", "Authorization layer never mutates cross-tenant trust."),
    ("authorization_bypass", "Authorization layer never bypasses permission checks."),
    ("hidden_privilege_elevation", "Authorization layer never hides privilege elevation."),
)

IDENTITY_ACCESS_HARDENING_EXECUTABLE: Final[bool] = False

MAX_IDENTITY_ACCESS_HARDENING_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_IDENTITY_ACCESS_HARDENING_RECORDS: Final[int] = 500

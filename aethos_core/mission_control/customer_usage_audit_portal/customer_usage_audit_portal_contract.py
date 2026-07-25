# SPDX-License-Identifier: Apache-2.0
"""FIX 307 — customer usage & audit portal contract."""

from __future__ import annotations

from typing import Final

CUSTOMER_USAGE_AUDIT_PORTAL_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_usage_audit_portal_v1"
)
CUSTOMER_USAGE_AUDIT_PORTAL_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_usage_audit_portal_record_v1"
)
CUSTOMER_USAGE_AUDIT_PORTAL_FIX: Final[str] = "FIX 307"

MUTATION_PERFORMED_FIX_307: Final[bool] = False
EXECUTION_PERFORMED_FIX_307: Final[bool] = False
AUDIT_AUTHORITY_FIX_307: Final[bool] = False
AUDIT_MUTATION_ENABLED_FIX_307: Final[bool] = False
EVIDENCE_MUTATION_ENABLED_FIX_307: Final[bool] = False
CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307: Final[bool] = False
AUTHORIZATION_BYPASS_ENABLED_FIX_307: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_307: Final[bool] = False
CUSTOMER_USAGE_AUDIT_COMPOSES_EVIDENCE_ONLY_FIX_307: Final[bool] = True

CUSTOMER_USAGE_AUDIT_PORTAL_ROUTE_ID: Final[str] = (
    "mission_control_customer_usage_audit_portal"
)

CUSTOMER_USAGE_AUDIT_PORTAL_INVARIANT: Final[str] = (
    "customer_usage_audit_portal_visibility_without_audit_authority_or_mutation"
)

AUDIT_PORTAL_DOMAINS: Final[tuple[str, ...]] = (
    "activity_timeline",
    "governance_timeline",
    "usage_timeline",
    "audit_registry",
    "repository_activity",
    "user_activity",
    "provider_activity",
    "billing_usage_history",
    "evidence_explorer",
    "customer_audit_dashboard",
)

GOVERNANCE_RECORD_KIND_MARKERS: Final[tuple[str, ...]] = (
    "decision",
    "approve",
    "hold",
    "reject",
    "defer",
    "trust",
    "merge",
    "deploy",
    "rollback",
    "lifecycle",
    "governance",
    "authorization",
)

USAGE_RECORD_KIND_MARKERS: Final[tuple[str, ...]] = (
    "usage",
    "execution",
    "workflow",
    "project",
    "workspace",
    "channel",
    "provider_connection",
    "billing",
    "onboarding",
)

HUMAN_AUDIT_DECISION_KINDS: Final[tuple[str, ...]] = (
    "audit_decision_approve",
    "audit_decision_hold",
    "audit_decision_reject",
    "audit_decision_defer",
)

CUSTOMER_USAGE_AUDIT_PORTAL_RECORD_KINDS: Final[tuple[str, ...]] = (
    "audit_note",
    *HUMAN_AUDIT_DECISION_KINDS,
    "customer_usage_audit_portal_record",
)

CUSTOMER_USAGE_AUDIT_PORTAL_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("visibility_not_authority", "Audit visibility ≠ audit authority."),
    ("immutable_records", "Portal surfaces audit records without mutation or deletion."),
    ("tenant_scoped", "Audit visibility is scoped to the current tenant."),
    ("compose_only", "Composes FIX 181–307 records and Mission Control artifacts without re-execution."),
    ("evidence_first", "Evidence explorer surfaces trust, pilot, lifecycle, and governance artifacts."),
    ("transparent_customer", "Customers can answer what happened, who did it, and when without support."),
    ("no_governance_bypass", "Portal never bypasses governance or authorization."),
    ("no_cross_tenant", "Cross-tenant audit visibility remains blocked."),
    ("human_review", "Audit review records decisions without mutating audit history."),
    ("usage_transparency", "Usage timeline composes projects, workflows, channels, and provider activity."),
)

FORBIDDEN_AUDIT_PORTAL_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("audit_record_mutation", "Audit portal never mutates audit records."),
    ("audit_deletion", "Audit portal never deletes audit records."),
    ("evidence_deletion", "Audit portal never deletes evidence."),
    ("trust_modification", "Audit portal never modifies trust."),
    ("governance_modification", "Audit portal never modifies governance state."),
    ("cross_tenant_audit_visibility", "Audit portal never exposes cross-tenant audit records."),
    ("authorization_bypass", "Audit portal never bypasses authorization."),
    ("hidden_execution", "Audit portal never introduces hidden execution paths."),
)

CUSTOMER_USAGE_AUDIT_PORTAL_EXECUTABLE: Final[bool] = False

MAX_CUSTOMER_USAGE_AUDIT_PORTAL_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_CUSTOMER_USAGE_AUDIT_PORTAL_RECORDS: Final[int] = 500

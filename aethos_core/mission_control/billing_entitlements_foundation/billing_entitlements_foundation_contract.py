# SPDX-License-Identifier: Apache-2.0
"""FIX 305 — billing & entitlements foundation contract."""

from __future__ import annotations

from typing import Final

BILLING_ENTITLEMENTS_FOUNDATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_billing_entitlements_foundation_v1"
)
BILLING_ENTITLEMENTS_FOUNDATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_billing_entitlements_foundation_record_v1"
)
BILLING_ENTITLEMENTS_FOUNDATION_FIX: Final[str] = "FIX 305"

MUTATION_PERFORMED_FIX_305: Final[bool] = False
EXECUTION_PERFORMED_FIX_305: Final[bool] = False
BILLING_AUTHORITY_FIX_305: Final[bool] = False
AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305: Final[bool] = False
AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305: Final[bool] = False
AUTOMATIC_PLAN_DOWNGRADE_ENABLED_FIX_305: Final[bool] = False
PAYMENT_PROCESSING_ENABLED_FIX_305: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_305: Final[bool] = False
BILLING_ENTITLEMENTS_COMPOSES_EVIDENCE_ONLY_FIX_305: Final[bool] = True

BILLING_ENTITLEMENTS_FOUNDATION_ROUTE_ID: Final[str] = (
    "mission_control_billing_entitlements_foundation"
)

BILLING_ENTITLEMENTS_FOUNDATION_INVARIANT: Final[str] = (
    "billing_entitlements_foundation_entitlements_not_authority_without_payment_processing"
)

PLANS: Final[tuple[str, ...]] = (
    "FREE",
    "STARTER",
    "PRO",
    "BUSINESS",
    "ENTERPRISE",
)

BILLING_DOMAINS: Final[tuple[str, ...]] = (
    "plan_registry",
    "subscription_registry",
    "entitlement_registry",
    "usage_registry",
    "capability_entitlement_matrix",
    "channel_entitlement_matrix",
    "provider_entitlement_matrix",
    "usage_limits",
    "billing_readiness",
    "billing_dashboard",
)

ORG_PLAN_TO_COMMERCIAL_PLAN: Final[tuple[tuple[str, str], ...]] = (
    ("free", "FREE"),
    ("starter", "STARTER"),
    ("team", "STARTER"),
    ("pro", "PRO"),
    ("business", "BUSINESS"),
    ("enterprise", "ENTERPRISE"),
)

PLAN_LIMITS: Final[tuple[tuple[str, dict[str, int | None]], ...]] = (
    (
        "FREE",
        {
            "max_organizations": 1,
            "max_workspaces": 1,
            "max_projects": 1,
            "max_repositories": 1,
            "max_executions": 10,
        },
    ),
    (
        "STARTER",
        {
            "max_organizations": 1,
            "max_workspaces": 2,
            "max_projects": 2,
            "max_repositories": 3,
            "max_executions": 50,
        },
    ),
    (
        "PRO",
        {
            "max_organizations": 1,
            "max_workspaces": 5,
            "max_projects": 10,
            "max_repositories": 10,
            "max_executions": 500,
        },
    ),
    (
        "BUSINESS",
        {
            "max_organizations": 3,
            "max_workspaces": 20,
            "max_projects": 50,
            "max_repositories": 50,
            "max_executions": 5000,
        },
    ),
    (
        "ENTERPRISE",
        {
            "max_organizations": None,
            "max_workspaces": None,
            "max_projects": None,
            "max_repositories": None,
            "max_executions": None,
        },
    ),
)

PLAN_CAPABILITIES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("FREE", ("onboarding", "capability_discovery")),
    ("STARTER", ("onboarding", "capability_discovery", "provider_connection_guidance")),
    ("PRO", ("governed_delivery", "repository_intelligence", "provider_connection_guidance")),
    (
        "BUSINESS",
        ("multi_project_operations", "portfolio_intelligence", "governed_delivery", "repository_intelligence"),
    ),
    (
        "ENTERPRISE",
        ("advanced_governance", "enterprise_administration", "multi_project_operations", "portfolio_intelligence"),
    ),
)

PLAN_CHANNELS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("FREE", ("web",)),
    ("STARTER", ("web", "telegram")),
    ("PRO", ("web", "telegram")),
    ("BUSINESS", ("web", "telegram", "slack", "email")),
    ("ENTERPRISE", ("web", "telegram", "slack", "email", "voice")),
)

PLAN_PROVIDERS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("FREE", ()),
    ("STARTER", ("GitHub",)),
    ("PRO", ("GitHub", "Railway", "Vercel")),
    ("BUSINESS", ("GitHub", "Railway", "Vercel")),
    ("ENTERPRISE", ("GitHub", "Railway", "Vercel", "AWS", "Azure", "GCP", "Kubernetes")),
)

UPGRADE_PATHS: Final[tuple[tuple[str, str], ...]] = (
    ("FREE", "STARTER"),
    ("STARTER", "PRO"),
    ("PRO", "BUSINESS"),
    ("BUSINESS", "ENTERPRISE"),
)

HUMAN_BILLING_DECISION_KINDS: Final[tuple[str, ...]] = (
    "billing_decision_approve",
    "billing_decision_hold",
    "billing_decision_reject",
    "billing_decision_defer",
)

BILLING_ENTITLEMENTS_FOUNDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "billing_note",
    *HUMAN_BILLING_DECISION_KINDS,
    "billing_entitlements_foundation_record",
)

BILLING_ENTITLEMENTS_FOUNDATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("entitlements_not_authority", "Entitlements ≠ authority — billing controls access, not governance."),
    ("governance_parity", "Paid users still follow the same approval and trust rules."),
    ("compose_only", "Composes FIX 300 tenancy and FIX 304 channel context without payment processing."),
    ("plan_visibility", "Plans, subscriptions, entitlements, and limits are visible and explainable."),
    ("usage_tracking", "Usage composes from tenant artifacts without automatic enforcement mutation."),
    ("no_payment", "Payment collection, charging, and subscription mutation belong to future integrations."),
    ("upgrade_guidance", "Upgrade paths are advisory — no automatic plan upgrades or downgrades."),
    ("limit_transparency", "Usage limits are reported; exceeding limits does not bypass governance."),
    ("human_review", "Billing review records decisions without subscription mutation."),
    ("commercial_foundation", "Establishes commercial model without making AethOS sellable via payment rails."),
)

FORBIDDEN_BILLING_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("payment_collection", "Billing foundation never collects payments."),
    ("credit_card_storage", "Billing foundation never stores credit cards."),
    ("automatic_charging", "Billing foundation never charges automatically."),
    ("subscription_mutation", "Billing foundation never mutates subscriptions."),
    ("plan_upgrade", "Billing foundation never upgrades plans automatically."),
    ("plan_downgrade", "Billing foundation never downgrades plans automatically."),
    ("invoice_generation", "Billing foundation never generates invoices."),
    ("refund_processing", "Billing foundation never processes refunds."),
    ("governance_bypass", "Entitlements never bypass governance or trust boundaries."),
)

BILLING_ENTITLEMENTS_FOUNDATION_EXECUTABLE: Final[bool] = False

MAX_BILLING_ENTITLEMENTS_FOUNDATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_BILLING_ENTITLEMENTS_FOUNDATION_RECORDS: Final[int] = 500

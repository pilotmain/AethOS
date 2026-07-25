# SPDX-License-Identifier: Apache-2.0
"""FIX 308 — payment integration readiness contract."""

from __future__ import annotations

from typing import Final

PAYMENT_INTEGRATION_READINESS_SCHEMA_VERSION: Final[str] = (
    "mission_control_payment_integration_readiness_v1"
)
PAYMENT_INTEGRATION_READINESS_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_payment_integration_readiness_record_v1"
)
PAYMENT_INTEGRATION_READINESS_FIX: Final[str] = "FIX 308"

MUTATION_PERFORMED_FIX_308: Final[bool] = False
EXECUTION_PERFORMED_FIX_308: Final[bool] = False
PAYMENT_PROCESSING_ENABLED_FIX_308: Final[bool] = False
CREDIT_CARD_STORAGE_ENABLED_FIX_308: Final[bool] = False
AUTOMATIC_CHARGING_ENABLED_FIX_308: Final[bool] = False
AUTOMATIC_REFUND_ENABLED_FIX_308: Final[bool] = False
SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_308: Final[bool] = False
PAYMENT_READINESS_COMPOSES_EVIDENCE_ONLY_FIX_308: Final[bool] = True

PAYMENT_INTEGRATION_READINESS_ROUTE_ID: Final[str] = (
    "mission_control_payment_integration_readiness"
)

PAYMENT_INTEGRATION_READINESS_INVARIANT: Final[str] = (
    "payment_integration_readiness_models_future_payments_without_processing"
)

PAYMENT_READINESS_DOMAINS: Final[tuple[str, ...]] = (
    "customer_billing_identity",
    "payment_provider_registry",
    "subscription_lifecycle",
    "billing_event_registry",
    "invoice_readiness",
    "usage_monetization",
    "commercial_analytics",
    "upgrade_path_registry",
    "payment_readiness_dashboard",
    "commercial_governance",
)

PAYMENT_PROVIDERS: Final[tuple[str, ...]] = (
    "Stripe",
    "Paddle",
    "Lemon Squeezy",
)

SUBSCRIPTION_LIFECYCLE_STATES: Final[tuple[str, ...]] = (
    "trial",
    "active",
    "past_due",
    "suspended",
    "cancelled",
    "expired",
)

BILLING_EVENT_TYPES: Final[tuple[str, ...]] = (
    "subscription_created",
    "subscription_updated",
    "subscription_cancelled",
    "entitlement_changed",
    "usage_threshold_reached",
)

USAGE_MONETIZATION_CATEGORIES: Final[tuple[tuple[str, str], ...]] = (
    ("organizations", "tenant_count"),
    ("workspaces", "workspace_count"),
    ("projects", "project_count"),
    ("repositories", "repository_count"),
    ("executions", "agent_execution_count"),
    ("storage", "storage_mb"),
    ("ai_consumption", "ai_consumption_units"),
)

HUMAN_PAYMENT_READINESS_DECISION_KINDS: Final[tuple[str, ...]] = (
    "payment_readiness_decision_approve",
    "payment_readiness_decision_hold",
    "payment_readiness_decision_reject",
    "payment_readiness_decision_defer",
)

PAYMENT_INTEGRATION_READINESS_RECORD_KINDS: Final[tuple[str, ...]] = (
    "payment_readiness_note",
    *HUMAN_PAYMENT_READINESS_DECISION_KINDS,
    "payment_integration_readiness_record",
)

PAYMENT_INTEGRATION_READINESS_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("readiness_not_processing", "Payment readiness ≠ payment processing."),
    ("no_card_storage", "AethOS may not store payment methods."),
    ("no_charging", "AethOS may not charge customers."),
    ("compose_fix_305", "Composes FIX 305 plans, subscriptions, usage, and entitlements."),
    ("future_proof", "Models commercial relationships for future provider integration."),
    ("lifecycle_visibility", "Subscription lifecycle states are visible without mutation."),
    ("billing_events", "Billing events are modeled as readiness artifacts only."),
    ("upgrade_guidance", "Upgrade paths are advisory — no automatic plan changes."),
    ("human_review", "Payment readiness review records decisions without provider mutation."),
    ("commercial_scale", "Prepares for commercial scale without payment authority."),
)

FORBIDDEN_PAYMENT_READINESS_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("payment_collection", "Payment readiness never collects payments."),
    ("credit_card_storage", "Payment readiness never stores credit cards."),
    ("charging_customers", "Payment readiness never charges customers."),
    ("refund_processing", "Payment readiness never processes refunds."),
    ("subscription_mutation", "Payment readiness never mutates subscriptions."),
    ("invoice_generation", "Payment readiness never generates invoices."),
    ("provider_api_mutation", "Payment readiness never mutates provider APIs."),
    ("hidden_payment_paths", "Payment readiness never introduces hidden payment paths."),
)

PAYMENT_INTEGRATION_READINESS_EXECUTABLE: Final[bool] = False

MAX_PAYMENT_INTEGRATION_READINESS_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PAYMENT_INTEGRATION_READINESS_RECORDS: Final[int] = 500

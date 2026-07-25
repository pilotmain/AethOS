# SPDX-License-Identifier: Apache-2.0
"""FIX 310 — customer support & success foundation contract."""

from __future__ import annotations

from typing import Final

CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_support_success_foundation_v1"
)
CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_support_success_foundation_record_v1"
)
CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_FIX: Final[str] = "FIX 310"

MUTATION_PERFORMED_FIX_310: Final[bool] = False
EXECUTION_PERFORMED_FIX_310: Final[bool] = False
CUSTOMER_SUPPORT_AUTHORITY_FIX_310: Final[bool] = False
AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310: Final[bool] = False
AUTOMATIC_ESCALATION_ENABLED_FIX_310: Final[bool] = False
AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310: Final[bool] = False
AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_310: Final[bool] = False
CUSTOMER_SUPPORT_COMPOSES_EVIDENCE_ONLY_FIX_310: Final[bool] = True

CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_ROUTE_ID: Final[str] = (
    "mission_control_customer_support_success_foundation"
)

CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_INVARIANT: Final[str] = (
    "customer_support_visibility_without_customer_support_authority"
)

SUPPORT_DOMAINS: Final[tuple[str, ...]] = (
    "customer_health_registry",
    "customer_success_dashboard",
    "support_request_registry",
    "customer_adoption_report",
    "customer_trust_report",
    "customer_risk_registry",
    "customer_escalation_registry",
    "success_opportunity_registry",
    "support_analytics_dashboard",
    "customer_support_success_dashboard",
)

CUSTOMER_HEALTH_STATUSES: Final[tuple[str, ...]] = (
    "HEALTHY",
    "AT_RISK",
    "NEW",
    "HIGH_VALUE",
    "UNKNOWN",
)

ESCALATION_SEVERITIES: Final[tuple[str, ...]] = (
    "critical",
    "high",
    "medium",
    "low",
)

OPPORTUNITY_TYPES: Final[tuple[str, ...]] = (
    "upsell",
    "adoption",
    "training",
)

HUMAN_SUPPORT_DECISION_KINDS: Final[tuple[str, ...]] = (
    "support_review_decision_approve",
    "support_review_decision_hold",
    "support_review_decision_reject",
    "support_review_decision_defer",
)

CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "support_note",
    "customer_success_note",
    *HUMAN_SUPPORT_DECISION_KINDS,
    "customer_support_success_foundation_record",
)

CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("visibility_not_authority", "Customer support visibility ≠ customer support authority."),
    ("human_intervention", "Humans remain responsible for support actions."),
    ("compose_only", "Composes FIX 300–309 evidence without ticket execution."),
    ("no_outreach", "No automatic customer contact or messaging."),
    ("no_mutation", "No provider, subscription, plan, or trust mutation."),
    ("health_tracking", "Customer health derived from adoption and engagement signals."),
    ("risk_visibility", "Support risks visible before external beta users arrive."),
    ("escalation_tracking", "Escalations tracked without automatic resolution."),
    ("success_opportunities", "Upsell and adoption opportunities surfaced for human review."),
    ("launch_operations", "Moves from launch assessment to launch operations readiness."),
)

FORBIDDEN_SUPPORT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("customer_messaging", "Support foundation never sends customer messages."),
    ("email_sending", "Support foundation never sends email."),
    ("ticket_execution", "Support foundation never executes tickets."),
    ("provider_mutation", "Support foundation never mutates providers."),
    ("subscription_mutation", "Support foundation never mutates subscriptions."),
    ("plan_changes", "Support foundation never changes plans."),
    ("trust_mutation", "Support foundation never mutates trust."),
    ("automatic_intervention", "Support foundation never intervenes automatically."),
)

CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_EXECUTABLE: Final[bool] = False

MAX_CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_RECORDS: Final[int] = 500

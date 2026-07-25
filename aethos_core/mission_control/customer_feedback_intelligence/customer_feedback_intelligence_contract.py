# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — customer feedback intelligence contract."""

from __future__ import annotations

from typing import Final

CUSTOMER_FEEDBACK_INTELLIGENCE_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_feedback_intelligence_v1"
)
CUSTOMER_FEEDBACK_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_feedback_intelligence_record_v1"
)
CUSTOMER_FEEDBACK_INTELLIGENCE_FIX: Final[str] = "FIX 319"

MUTATION_PERFORMED_FIX_319: Final[bool] = False
EXECUTION_PERFORMED_FIX_319: Final[bool] = False
FEEDBACK_AUTHORITY_FIX_319: Final[bool] = False
AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_319: Final[bool] = False
AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319: Final[bool] = False
AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_319: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_319: Final[bool] = False
CUSTOMER_FEEDBACK_COMPOSES_EVIDENCE_ONLY_FIX_319: Final[bool] = True

CUSTOMER_FEEDBACK_INTELLIGENCE_ROUTE_ID: Final[str] = "mission_control_customer_feedback_intelligence"

CUSTOMER_FEEDBACK_INTELLIGENCE_INVARIANT: Final[str] = (
    "customer_feedback_intelligence_without_automatic_work_creation"
)

CUSTOMER_FEEDBACK_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "customer_feedback_registry",
    "feedback_classification_report",
    "feedback_sentiment_report",
    "feedback_trend_report",
    "capability_gap_report",
    "customer_friction_report",
    "feedback_opportunity_registry",
    "feedback_priority_matrix",
    "customer_feedback_dashboard",
    "feedback_review_registry",
)

FEEDBACK_SOURCES: Final[tuple[str, ...]] = (
    "support_notes",
    "customer_success_observations",
    "beta_feedback",
    "onboarding_feedback",
    "product_feedback",
    "operator_observations",
)

FEEDBACK_CLASSIFICATIONS: Final[tuple[str, ...]] = (
    "feature_request",
    "usability_issue",
    "onboarding_issue",
    "trust_concern",
    "capability_gap",
    "commercial_concern",
    "operational_issue",
    "positive_feedback",
)

SENTIMENT_LABELS: Final[tuple[str, ...]] = ("positive", "neutral", "negative")

FEEDBACK_CORE_PRINCIPLE: Final[str] = "feedback_intelligence ≠ customer_authority"

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_message_content_mining_outside_submitted_feedback",
    "no_cross_tenant_feedback_aggregation",
    "no_identity_exposure",
    "no_customer_profiling",
    "tenant_boundaries_preserved",
)

HUMAN_FEEDBACK_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "feedback_review_decision_approve",
    "feedback_review_decision_hold",
    "feedback_review_decision_reject",
    "feedback_review_decision_defer",
)

FEEDBACK_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "feedback_note",
    *HUMAN_FEEDBACK_REVIEW_DECISION_KINDS,
    "feedback_snapshot",
)

FORBIDDEN_FEEDBACK_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_feature_creation", "Never creates features automatically from feedback."),
    ("automatic_backlog_creation", "Never creates backlog items automatically."),
    ("automatic_customer_contact", "Never contacts customers automatically."),
    ("cross_tenant_aggregation", "Never aggregates feedback across tenants."),
    ("message_content_mining", "Never mines private message content outside submitted feedback."),
)

CUSTOMER_FEEDBACK_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_FEEDBACK_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_FEEDBACK_REVIEW_RECORDS: Final[int] = 500

IMPACT_LEVELS: Final[tuple[str, ...]] = ("high", "medium", "low")
EFFORT_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")

# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — product analytics foundation contract."""

from __future__ import annotations

from typing import Final

PRODUCT_ANALYTICS_FOUNDATION_SCHEMA_VERSION: Final[str] = "mission_control_product_analytics_foundation_v1"
PRODUCT_ANALYTICS_FOUNDATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_product_analytics_foundation_record_v1"
)
PRODUCT_ANALYTICS_FOUNDATION_FIX: Final[str] = "FIX 318"

MUTATION_PERFORMED_FIX_318: Final[bool] = False
EXECUTION_PERFORMED_FIX_318: Final[bool] = False
ANALYTICS_AUTHORITY_FIX_318: Final[bool] = False
AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318: Final[bool] = False
AUTOMATIC_USER_TARGETING_ENABLED_FIX_318: Final[bool] = False
AUTOMATIC_PLAN_MUTATION_ENABLED_FIX_318: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_318: Final[bool] = False
PRODUCT_ANALYTICS_COMPOSES_EVIDENCE_ONLY_FIX_318: Final[bool] = True

PRODUCT_ANALYTICS_FOUNDATION_ROUTE_ID: Final[str] = "mission_control_product_analytics_foundation"

PRODUCT_ANALYTICS_FOUNDATION_INVARIANT: Final[str] = (
    "product_analytics_without_surveillance_or_automatic_behavior_modification"
)

PRODUCT_ANALYTICS_FOUNDATION_DOMAINS: Final[tuple[str, ...]] = (
    "analytics_event_registry",
    "user_journey_report",
    "onboarding_analytics_report",
    "capability_usage_report",
    "provider_analytics_report",
    "commercial_analytics_report",
    "customer_success_analytics_report",
    "behavioral_opportunity_registry",
    "analytics_dashboard",
    "analytics_review_registry",
)

CANONICAL_ANALYTICS_EVENTS: Final[tuple[str, ...]] = (
    "organization_created",
    "workspace_created",
    "project_registered",
    "provider_connected",
    "onboarding_completed",
    "beta_admitted",
    "launch_review_completed",
)

PRIVACY_PRINCIPLES: Final[tuple[str, ...]] = (
    "no_secret_collection",
    "no_credential_storage",
    "no_message_content_analysis",
    "no_cross_tenant_analytics",
    "no_identity_bypass",
    "tenant_isolation_preserved",
)

ANALYTICS_CORE_PRINCIPLE: Final[str] = "analytics_visibility ≠ user_surveillance"

HUMAN_ANALYTICS_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "analytics_review_decision_approve",
    "analytics_review_decision_hold",
    "analytics_review_decision_reject",
    "analytics_review_decision_defer",
)

ANALYTICS_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "analytics_note",
    *HUMAN_ANALYTICS_REVIEW_DECISION_KINDS,
    "analytics_snapshot",
)

FORBIDDEN_ANALYTICS_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_behavior_modification", "Never modifies user behavior automatically."),
    ("automatic_user_targeting", "Never targets users automatically."),
    ("automatic_plan_mutation", "Never mutates plans or entitlements automatically."),
    ("cross_tenant_analytics", "Never aggregates analytics across tenant boundaries."),
    ("message_content_analysis", "Never analyzes private message content for analytics."),
)

PRODUCT_ANALYTICS_FOUNDATION_EXECUTABLE: Final[bool] = False

MAX_ANALYTICS_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_ANALYTICS_REVIEW_RECORDS: Final[int] = 500

JOURNEY_STAGES: Final[tuple[str, ...]] = (
    "entry",
    "activation",
    "adoption",
    "retention",
    "expansion",
)

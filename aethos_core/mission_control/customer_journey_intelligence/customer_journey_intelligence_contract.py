# SPDX-License-Identifier: Apache-2.0
"""FIX 321 — customer journey intelligence contract."""

from __future__ import annotations

from typing import Final

CUSTOMER_JOURNEY_INTELLIGENCE_SCHEMA_VERSION: Final[str] = "mission_control_customer_journey_intelligence_v1"
CUSTOMER_JOURNEY_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_journey_intelligence_record_v1"
)
CUSTOMER_JOURNEY_INTELLIGENCE_FIX: Final[str] = "FIX 321"

MUTATION_PERFORMED_FIX_321: Final[bool] = False
EXECUTION_PERFORMED_FIX_321: Final[bool] = False
JOURNEY_AUTHORITY_FIX_321: Final[bool] = False
AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_321: Final[bool] = False
AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321: Final[bool] = False
AUTOMATIC_JOURNEY_MODIFICATION_ENABLED_FIX_321: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_321: Final[bool] = False
CUSTOMER_JOURNEY_COMPOSES_EVIDENCE_ONLY_FIX_321: Final[bool] = True

CUSTOMER_JOURNEY_INTELLIGENCE_ROUTE_ID: Final[str] = "mission_control_customer_journey_intelligence"

CUSTOMER_JOURNEY_INTELLIGENCE_INVARIANT: Final[str] = (
    "customer_journey_intelligence_without_customer_manipulation"
)

CUSTOMER_JOURNEY_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "customer_journey_registry",
    "journey_funnel_report",
    "journey_dropoff_report",
    "journey_success_report",
    "journey_friction_report",
    "journey_cohort_report",
    "journey_opportunity_registry",
    "journey_priority_matrix",
    "customer_journey_dashboard",
    "journey_review_registry",
)

JOURNEY_STAGES: Final[tuple[str, ...]] = (
    "awareness",
    "evaluation",
    "onboarding",
    "activation",
    "adoption",
    "retention",
    "expansion",
    "advocacy",
)

JOURNEY_FUNNEL_TRANSITIONS: Final[tuple[tuple[str, str], ...]] = (
    ("awareness", "evaluation"),
    ("evaluation", "onboarding"),
    ("onboarding", "activation"),
    ("activation", "adoption"),
    ("adoption", "retention"),
    ("retention", "expansion"),
    ("expansion", "advocacy"),
)

JOURNEY_OPPORTUNITY_TYPES: Final[tuple[str, ...]] = (
    "activation",
    "retention",
    "expansion",
)

PROGRESSION_STATES: Final[tuple[str, ...]] = (
    "not_started",
    "in_progress",
    "completed",
    "stalled",
)

JOURNEY_CORE_PRINCIPLE: Final[str] = "journey_intelligence ≠ customer_manipulation"

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_journey_analysis",
    "no_customer_targeting",
    "no_customer_profiling",
    "no_automatic_interventions",
    "tenant_isolation_preserved",
)

HUMAN_JOURNEY_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "journey_review_decision_approve",
    "journey_review_decision_hold",
    "journey_review_decision_reject",
    "journey_review_decision_defer",
)

JOURNEY_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "journey_note",
    *HUMAN_JOURNEY_REVIEW_DECISION_KINDS,
    "journey_snapshot",
)

FORBIDDEN_JOURNEY_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_customer_targeting", "Never targets customers automatically."),
    ("automatic_customer_intervention", "Never intervenes in customer journeys automatically."),
    ("automatic_journey_modification", "Never modifies customer journeys automatically."),
    ("cross_tenant_journey_analysis", "Never aggregates journey signals across tenants."),
)

CUSTOMER_JOURNEY_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_JOURNEY_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_JOURNEY_REVIEW_RECORDS: Final[int] = 500

IMPACT_LEVELS: Final[tuple[str, ...]] = ("high", "medium", "low")
EFFORT_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")

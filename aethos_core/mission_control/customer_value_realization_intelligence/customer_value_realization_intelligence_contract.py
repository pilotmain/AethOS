# SPDX-License-Identifier: Apache-2.0
"""FIX 323 — customer value realization intelligence contract."""

from __future__ import annotations

from typing import Final

CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_value_realization_intelligence_v1"
)
CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_customer_value_realization_intelligence_record_v1"
)
CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_FIX: Final[str] = "FIX 323"

MUTATION_PERFORMED_FIX_323: Final[bool] = False
EXECUTION_PERFORMED_FIX_323: Final[bool] = False
VALUE_REALIZATION_AUTHORITY_FIX_323: Final[bool] = False
AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323: Final[bool] = False
AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_323: Final[bool] = False
AUTOMATIC_GOAL_MODIFICATION_ENABLED_FIX_323: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_323: Final[bool] = False
CUSTOMER_VALUE_REALIZATION_COMPOSES_EVIDENCE_ONLY_FIX_323: Final[bool] = True

CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_ROUTE_ID: Final[str] = (
    "mission_control_customer_value_realization_intelligence"
)

CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_INVARIANT: Final[str] = (
    "customer_value_realization_intelligence_without_customer_success_authority"
)

CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "value_outcome_registry",
    "expected_value_registry",
    "value_gap_report",
    "capability_value_report",
    "journey_value_report",
    "customer_success_outcome_report",
    "value_opportunity_registry",
    "value_realization_scorecard",
    "customer_value_dashboard",
    "value_review_registry",
)

VALUE_OUTCOME_CATEGORIES: Final[tuple[str, ...]] = (
    "time_saved",
    "workflow_improvement",
    "operational_improvement",
    "governance_improvement",
    "visibility_improvement",
)

VALUE_OPPORTUNITY_TYPES: Final[tuple[str, ...]] = (
    "unrealized_value",
    "adoption",
    "education",
    "onboarding",
)

VALUE_REALIZATION_SCORECARD_DIMENSIONS: Final[tuple[str, ...]] = (
    "outcome_achievement",
    "value_adoption",
    "value_retention",
    "value_expansion",
)

VALUE_REALIZATION_LEVELS: Final[tuple[str, ...]] = (
    "UNKNOWN",
    "LOW",
    "MODERATE",
    "HIGH",
    "EXCEPTIONAL",
)

VALUE_REALIZATION_CORE_PRINCIPLE: Final[str] = "value_realization_intelligence ≠ customer_success_authority"

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_exposure",
    "no_customer_targeting",
    "no_customer_profiling",
    "no_automatic_customer_intervention",
    "tenant_isolation_preserved",
)

HUMAN_VALUE_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "value_review_decision_approve",
    "value_review_decision_hold",
    "value_review_decision_reject",
    "value_review_decision_defer",
)

VALUE_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "value_note",
    *HUMAN_VALUE_REVIEW_DECISION_KINDS,
    "value_snapshot",
)

FORBIDDEN_VALUE_REALIZATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_customer_success", "Never executes customer success programs automatically."),
    ("automatic_customer_outreach", "Never contacts customers automatically."),
    ("automatic_goal_modification", "Never modifies customer goals automatically."),
    ("cross_tenant_value_analysis", "Never aggregates value realization signals across tenants."),
)

CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_VALUE_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_VALUE_REVIEW_RECORDS: Final[int] = 500

IMPACT_LEVELS: Final[tuple[str, ...]] = ("high", "medium", "low")
EFFORT_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")

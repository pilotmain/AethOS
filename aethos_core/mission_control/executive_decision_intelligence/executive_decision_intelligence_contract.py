# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence contract."""

from __future__ import annotations

from typing import Final

EXECUTIVE_DECISION_INTELLIGENCE_SCHEMA_VERSION: Final[str] = "mission_control_executive_decision_intelligence_v1"
EXECUTIVE_DECISION_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_executive_decision_intelligence_record_v1"
)
EXECUTIVE_DECISION_INTELLIGENCE_FIX: Final[str] = "FIX 325"

MUTATION_PERFORMED_FIX_325: Final[bool] = False
EXECUTION_PERFORMED_FIX_325: Final[bool] = False
EXECUTIVE_AUTHORITY_FIX_325: Final[bool] = False
AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_325: Final[bool] = False
AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_325: Final[bool] = False
AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_325: Final[bool] = False
AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_325: Final[bool] = False
EXECUTIVE_DECISION_COMPOSES_EVIDENCE_ONLY_FIX_325: Final[bool] = True

EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID: Final[str] = "mission_control_executive_decision_intelligence"

EXECUTIVE_DECISION_INTELLIGENCE_INVARIANT: Final[str] = (
    "executive_decision_intelligence_without_executive_authority"
)

EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "executive_decision_registry",
    "decision_opportunity_report",
    "decision_risk_report",
    "executive_recommendation_report",
    "tradeoff_analysis_report",
    "executive_alignment_report",
    "executive_opportunity_registry",
    "executive_priority_matrix",
    "executive_decision_dashboard",
    "executive_review_registry",
)

EXECUTIVE_DECISION_STATUSES: Final[tuple[str, ...]] = (
    "pending",
    "reviewed",
    "deferred",
)

EXECUTIVE_RECOMMENDATION_LEVELS: Final[tuple[str, ...]] = (
    "REVIEW",
    "PRIORITIZE",
    "ACCELERATE",
    "DEFER",
    "HOLD",
)

EXECUTIVE_OPPORTUNITY_SOURCES: Final[tuple[str, ...]] = (
    "strategic",
    "growth",
    "value",
    "pmf",
    "improvement",
)

EXECUTIVE_CORE_PRINCIPLE: Final[str] = "executive_decision_intelligence ≠ executive_authority"

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_decision_visibility",
    "no_automatic_executive_decisions",
    "no_automatic_budget_changes",
    "tenant_isolation_preserved",
)

HUMAN_EXECUTIVE_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "executive_review_decision_approve",
    "executive_review_decision_hold",
    "executive_review_decision_reject",
    "executive_review_decision_defer",
)

EXECUTIVE_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "executive_note",
    *HUMAN_EXECUTIVE_REVIEW_DECISION_KINDS,
    "executive_snapshot",
)

FORBIDDEN_EXECUTIVE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_decision_execution", "Never executes executive decisions automatically."),
    ("automatic_strategy_execution", "Never executes strategy automatically."),
    ("automatic_resource_reallocation", "Never reallocates resources automatically."),
    ("automatic_budget_allocation", "Never allocates budget automatically."),
    ("cross_tenant_decision_visibility", "Never aggregates decision signals across tenants."),
)

EXECUTIVE_DECISION_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_EXECUTIVE_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_EXECUTIVE_REVIEW_RECORDS: Final[int] = 500

EFFORT_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")

# SPDX-License-Identifier: Apache-2.0
"""FIX 326 — strategic planning intelligence contract."""

from __future__ import annotations

from typing import Final

STRATEGIC_PLANNING_INTELLIGENCE_SCHEMA_VERSION: Final[str] = "mission_control_strategic_planning_intelligence_v1"
STRATEGIC_PLANNING_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_strategic_planning_intelligence_record_v1"
)
STRATEGIC_PLANNING_INTELLIGENCE_FIX: Final[str] = "FIX 326"

MUTATION_PERFORMED_FIX_326: Final[bool] = False
EXECUTION_PERFORMED_FIX_326: Final[bool] = False
STRATEGIC_PLANNING_AUTHORITY_FIX_326: Final[bool] = False
AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326: Final[bool] = False
AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_326: Final[bool] = False
AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_326: Final[bool] = False
AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_326: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_326: Final[bool] = False
STRATEGIC_PLANNING_COMPOSES_EVIDENCE_ONLY_FIX_326: Final[bool] = True

STRATEGIC_PLANNING_INTELLIGENCE_ROUTE_ID: Final[str] = "mission_control_strategic_planning_intelligence"

STRATEGIC_PLANNING_INTELLIGENCE_INVARIANT: Final[str] = (
    "strategic_planning_intelligence_without_strategic_execution_authority"
)

STRATEGIC_PLANNING_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "strategic_planning_registry",
    "strategic_scenario_report",
    "scenario_impact_report",
    "strategic_risk_forecast",
    "strategic_opportunity_forecast",
    "resource_planning_report",
    "strategic_plan_registry",
    "strategic_comparison_matrix",
    "strategic_planning_dashboard",
    "strategic_planning_review_registry",
)

STRATEGIC_PLAN_STATUSES: Final[tuple[str, ...]] = (
    "active",
    "proposed",
    "archived",
)

STRATEGIC_SCENARIO_TYPES: Final[tuple[str, ...]] = (
    "conservative_growth",
    "balanced_growth",
    "aggressive_growth",
    "efficiency_optimization",
    "customer_expansion",
)

SCENARIO_IMPACT_DIMENSIONS: Final[tuple[str, ...]] = (
    "customer_impact",
    "product_impact",
    "operational_impact",
    "commercial_impact",
)

STRATEGIC_RISK_FORECAST_CATEGORIES: Final[tuple[str, ...]] = (
    "operational_risks",
    "commercial_risks",
    "adoption_risks",
    "execution_risks",
)

STRATEGIC_OPPORTUNITY_FORECAST_TYPES: Final[tuple[str, ...]] = (
    "growth_opportunities",
    "expansion_opportunities",
    "efficiency_opportunities",
)

RESOURCE_PLANNING_DIMENSIONS: Final[tuple[str, ...]] = (
    "engineering_allocation",
    "operational_allocation",
    "support_allocation",
    "investment_allocation",
)

COMPARISON_MATRIX_DIMENSIONS: Final[tuple[str, ...]] = (
    "value",
    "effort",
    "risk",
    "confidence",
    "timeline",
)

STRATEGIC_PLANNING_CORE_PRINCIPLE: Final[str] = (
    "strategic_planning_intelligence ≠ strategic_execution_authority"
)

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_planning_visibility",
    "no_automatic_strategic_execution",
    "no_automatic_investment_decisions",
    "tenant_isolation_preserved",
)

HUMAN_PLANNING_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "planning_review_decision_approve",
    "planning_review_decision_hold",
    "planning_review_decision_reject",
    "planning_review_decision_defer",
)

PLANNING_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "planning_note",
    *HUMAN_PLANNING_REVIEW_DECISION_KINDS,
    "planning_snapshot",
)

FORBIDDEN_PLANNING_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_strategy_execution", "Never executes strategic plans automatically."),
    ("automatic_project_creation", "Never creates projects automatically."),
    ("automatic_budget_allocation", "Never allocates budget automatically."),
    ("automatic_resource_assignment", "Never assigns resources automatically."),
    ("cross_tenant_planning_visibility", "Never aggregates planning signals across tenants."),
)

STRATEGIC_PLANNING_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_PLANNING_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PLANNING_REVIEW_RECORDS: Final[int] = 500

TIMELINE_LEVELS: Final[tuple[str, ...]] = ("short", "medium", "long")
EFFORT_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")

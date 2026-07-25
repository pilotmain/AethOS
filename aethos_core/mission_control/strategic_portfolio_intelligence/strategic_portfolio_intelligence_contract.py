# SPDX-License-Identifier: Apache-2.0
"""FIX 324 — strategic portfolio intelligence contract."""

from __future__ import annotations

from typing import Final

STRATEGIC_PORTFOLIO_INTELLIGENCE_SCHEMA_VERSION: Final[str] = "mission_control_strategic_portfolio_intelligence_v1"
STRATEGIC_PORTFOLIO_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_strategic_portfolio_intelligence_record_v1"
)
STRATEGIC_PORTFOLIO_INTELLIGENCE_FIX: Final[str] = "FIX 324"

MUTATION_PERFORMED_FIX_324: Final[bool] = False
EXECUTION_PERFORMED_FIX_324: Final[bool] = False
STRATEGIC_AUTHORITY_FIX_324: Final[bool] = False
AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324: Final[bool] = False
AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324: Final[bool] = False
AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324: Final[bool] = False
AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_324: Final[bool] = False
STRATEGIC_PORTFOLIO_COMPOSES_EVIDENCE_ONLY_FIX_324: Final[bool] = True

STRATEGIC_PORTFOLIO_INTELLIGENCE_ROUTE_ID: Final[str] = "mission_control_strategic_portfolio_intelligence"

STRATEGIC_PORTFOLIO_INTELLIGENCE_INVARIANT: Final[str] = (
    "strategic_portfolio_intelligence_without_executive_authority"
)

STRATEGIC_PORTFOLIO_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "portfolio_asset_registry",
    "strategic_value_report",
    "investment_opportunity_report",
    "portfolio_risk_report",
    "resource_allocation_report",
    "strategic_alignment_report",
    "portfolio_opportunity_registry",
    "strategic_priority_matrix",
    "strategic_portfolio_dashboard",
    "strategic_review_registry",
)

PORTFOLIO_ASSET_TYPES: Final[tuple[str, ...]] = (
    "product",
    "repository",
    "initiative",
    "program",
    "strategic_investment",
)

PORTFOLIO_OPPORTUNITY_TYPES: Final[tuple[str, ...]] = (
    "growth",
    "efficiency",
    "strategic",
)

PORTFOLIO_RISK_CATEGORIES: Final[tuple[str, ...]] = (
    "operational_risk",
    "product_risk",
    "customer_risk",
    "commercial_risk",
)

STRATEGIC_CORE_PRINCIPLE: Final[str] = "strategic_portfolio_intelligence ≠ executive_authority"

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_portfolio_visibility",
    "no_automatic_strategic_decisions",
    "no_automatic_budget_changes",
    "tenant_isolation_preserved",
)

HUMAN_STRATEGIC_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "strategic_review_decision_approve",
    "strategic_review_decision_hold",
    "strategic_review_decision_reject",
    "strategic_review_decision_defer",
)

STRATEGIC_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "strategic_note",
    *HUMAN_STRATEGIC_REVIEW_DECISION_KINDS,
    "strategic_snapshot",
)

FORBIDDEN_STRATEGIC_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_budget_allocation", "Never allocates budget automatically."),
    ("automatic_project_creation", "Never creates projects automatically."),
    ("automatic_resource_reallocation", "Never reallocates resources automatically."),
    ("automatic_strategy_execution", "Never executes strategy automatically."),
    ("cross_tenant_portfolio_visibility", "Never aggregates portfolio signals across tenants."),
)

STRATEGIC_PORTFOLIO_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_STRATEGIC_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_STRATEGIC_REVIEW_RECORDS: Final[int] = 500

IMPACT_LEVELS: Final[tuple[str, ...]] = ("high", "medium", "low")
EFFORT_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")

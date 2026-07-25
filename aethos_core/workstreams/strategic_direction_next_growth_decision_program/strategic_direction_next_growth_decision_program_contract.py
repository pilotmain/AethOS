# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H1 / FIX 358 — strategic direction & next-growth decision program contract."""

from __future__ import annotations

from typing import Final

STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ID: Final[str] = "WORKSTREAM_H1"
STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_FIX: Final[str] = "FIX 358"
STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_strategic_direction_next_growth_decision_program_v1"
)
STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_strategic_direction_next_growth_decision_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "strategic_direction_intelligence_evaluates_options_without_strategic_authority"
)

MUTATION_PERFORMED_FIX_358: Final[bool] = False
EXECUTION_PERFORMED_FIX_358: Final[bool] = False
STRATEGIC_AUTHORITY_FIX_358: Final[bool] = False
BUDGET_ALLOCATION_FIX_358: Final[bool] = False
PROJECT_CREATION_FIX_358: Final[bool] = False
RESOURCE_COMMITMENT_FIX_358: Final[bool] = False
PLAN_EXECUTION_FIX_358: Final[bool] = False
ROADMAP_MUTATION_FIX_358: Final[bool] = False
AUTHORITY_EXPANSION_FIX_358: Final[bool] = False
AUTOMATIC_PRIORITIZATION_FIX_358: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_358: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_358: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_358: Final[bool] = False
LOCAL_STRATEGIC_DIRECTION_EXECUTABLE_FIX_358: Final[bool] = True

STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_strategic_direction_next_growth_decision_program"
)

STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_INVARIANT: Final[str] = (
    "strategic_direction_without_strategic_authority_budget_allocation_or_plan_execution"
)

STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_strategic_baseline_registry",
    "phase_2_growth_path_analysis",
    "phase_3_product_expansion_analysis",
    "phase_4_provider_strategy_analysis",
    "phase_5_customer_strategy_analysis",
    "phase_6_strategic_tradeoff_analysis",
    "phase_7_strategic_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

STRATEGIC_OUTCOME_CATEGORIES: Final[tuple[str, ...]] = (
    "option_a_customer_growth",
    "option_b_product_depth",
    "option_c_ecosystem_expansion",
    "option_d_enterprise_expansion",
)

STRATEGIC_DIRECTION_METRICS: Final[tuple[str, ...]] = (
    "opportunity_score",
    "strategic_leverage_score",
    "execution_risk_score",
    "confidence_score",
    "growth_potential_score",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 324",
    "FIX 325",
    "FIX 326",
    "FIX 330",
)

HUMAN_STRATEGIC_DIRECTION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "strategic_direction_review_approve",
    "strategic_direction_review_hold",
    "strategic_direction_review_reject",
    "strategic_direction_review_defer",
)

STRATEGIC_DIRECTION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "strategic_direction_note",
    *HUMAN_STRATEGIC_DIRECTION_DECISION_KINDS,
    "strategic_direction_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_budget_allocation",
    "no_project_creation",
    "no_roadmap_mutation",
    "no_authority_expansion",
    "no_strategy_execution",
    "no_automatic_prioritization",
)

FORBIDDEN_STRATEGIC_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("strategic_authority", "Never choose strategy from strategic direction intelligence."),
    ("budget_allocation", "Never allocate budget from strategic direction program."),
    ("project_creation", "Never create projects from strategic options analysis."),
    ("resource_commitment", "Never commit resources from strategic direction validation."),
    ("plan_execution", "Never execute plans from strategic direction program."),
    ("roadmap_mutation", "Never mutate roadmap from strategic direction intelligence."),
    ("automatic_prioritization", "Never auto-prioritize growth paths without human review."),
)

MAX_STRATEGIC_DIRECTION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_STRATEGIC_DIRECTION_RECORDS: Final[int] = 500

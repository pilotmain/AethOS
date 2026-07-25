# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H2 / FIX 359 — governed strategic execution program contract."""

from __future__ import annotations

from typing import Final

GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID: Final[str] = "WORKSTREAM_H2"
GOVERNED_STRATEGIC_EXECUTION_PROGRAM_FIX: Final[str] = "FIX 359"
GOVERNED_STRATEGIC_EXECUTION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_governed_strategic_execution_program_v1"
)
GOVERNED_STRATEGIC_EXECUTION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_governed_strategic_execution_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "strategic_execution_planning_prepares_execution_without_strategic_execution_authority"
)

MUTATION_PERFORMED_FIX_359: Final[bool] = False
EXECUTION_PERFORMED_FIX_359: Final[bool] = False
STRATEGIC_EXECUTION_AUTHORITY_FIX_359: Final[bool] = False
EXECUTION_AUTHORITY_FIX_359: Final[bool] = False
BUDGET_ALLOCATION_FIX_359: Final[bool] = False
PROJECT_CREATION_FIX_359: Final[bool] = False
RESOURCE_COMMITMENT_FIX_359: Final[bool] = False
INITIATIVE_LAUNCH_FIX_359: Final[bool] = False
ROADMAP_MUTATION_FIX_359: Final[bool] = False
AUTHORITY_EXPANSION_FIX_359: Final[bool] = False
AUTOMATIC_PRIORITIZATION_FIX_359: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_359: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_359: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_359: Final[bool] = False
LOCAL_STRATEGIC_EXECUTION_EXECUTABLE_FIX_359: Final[bool] = True

GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_governed_strategic_execution_program"
)

GOVERNED_STRATEGIC_EXECUTION_PROGRAM_INVARIANT: Final[str] = (
    "strategic_execution_planning_without_execution_authority_budget_allocation_or_initiative_launch"
)

GOVERNED_STRATEGIC_EXECUTION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_strategic_initiative_registry",
    "phase_2_initiative_decomposition",
    "phase_3_dependency_analysis",
    "phase_4_resource_planning_analysis",
    "phase_5_risk_planning_analysis",
    "phase_6_governance_readiness_analysis",
    "phase_7_execution_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

EXECUTION_READINESS_LEVELS: Final[tuple[str, ...]] = (
    "concept",
    "planned",
    "governed",
    "ready",
    "approved",
)

APPROVED_GROWTH_PATHS: Final[tuple[str, ...]] = (
    "customer_acquisition_expansion",
    "enterprise_expansion",
    "self_serve_expansion",
    "partner_expansion",
)

STRATEGIC_EXECUTION_METRICS: Final[tuple[str, ...]] = (
    "initiative_readiness_score",
    "dependency_complexity_score",
    "governance_readiness_score",
    "execution_readiness_score",
    "strategic_leverage_score",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 324",
    "FIX 325",
    "FIX 326",
    "FIX 330",
)

RISK_PLANNING_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 309",
    "FIX 313",
    "FIX 324",
    "FIX 325",
)

STRATEGIC_INITIATIVE_MIN_SIZE: Final[int] = 1

HUMAN_STRATEGIC_EXECUTION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "strategic_execution_review_approve",
    "strategic_execution_review_hold",
    "strategic_execution_review_reject",
    "strategic_execution_review_defer",
)

STRATEGIC_EXECUTION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "strategic_execution_note",
    "strategic_initiative_entry",
    *HUMAN_STRATEGIC_EXECUTION_DECISION_KINDS,
    "strategic_execution_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_budget_allocation",
    "no_project_creation",
    "no_roadmap_mutation",
    "no_execution_authority",
    "no_governance_bypass",
    "no_automatic_prioritization",
)

FORBIDDEN_EXECUTION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("strategic_execution_authority", "Never execute strategy from execution planning program."),
    ("execution_authority", "Never grant execution authority from strategic execution planning."),
    ("budget_allocation", "Never allocate budget from initiative planning."),
    ("project_creation", "Never create projects or obligations from execution planning."),
    ("resource_commitment", "Never commit resources from strategic execution program."),
    ("initiative_launch", "Never launch initiatives from execution planning."),
    ("roadmap_mutation", "Never mutate roadmap from strategic execution planning."),
    ("governance_bypass", "Never bypass governance from execution readiness assessment."),
)

MAX_STRATEGIC_EXECUTION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_STRATEGIC_EXECUTION_RECORDS: Final[int] = 500

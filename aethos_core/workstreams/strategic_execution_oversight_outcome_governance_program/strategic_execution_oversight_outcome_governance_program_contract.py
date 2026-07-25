# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H3 / FIX 360 — strategic execution oversight & outcome governance contract."""

from __future__ import annotations

from typing import Final

STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ID: Final[str] = "WORKSTREAM_H3"
STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_FIX: Final[str] = "FIX 360"
STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_strategic_execution_oversight_outcome_governance_program_v1"
)
STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_strategic_execution_oversight_outcome_governance_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "strategic_oversight_evaluates_outcomes_without_execution_authority"
)

MUTATION_PERFORMED_FIX_360: Final[bool] = False
EXECUTION_PERFORMED_FIX_360: Final[bool] = False
EXECUTION_AUTHORITY_FIX_360: Final[bool] = False
STRATEGY_MUTATION_FIX_360: Final[bool] = False
BUDGET_ALLOCATION_FIX_360: Final[bool] = False
RESOURCE_COMMITMENT_FIX_360: Final[bool] = False
GOVERNANCE_BYPASS_FIX_360: Final[bool] = False
AUTOMATIC_INITIATIVE_CHANGES_FIX_360: Final[bool] = False
AUTHORITY_EXPANSION_FIX_360: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_360: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_360: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_360: Final[bool] = False
LOCAL_STRATEGIC_OVERSIGHT_EXECUTABLE_FIX_360: Final[bool] = True

STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_strategic_execution_oversight_outcome_governance_program"
)

STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_INVARIANT: Final[str] = (
    "strategic_oversight_without_execution_authority_strategy_mutation_or_governance_bypass"
)

STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PHASES: Final[tuple[str, ...]] = (
    "phase_1_strategic_initiative_oversight_registry",
    "phase_2_outcome_tracking_analysis",
    "phase_3_strategic_risk_monitoring",
    "phase_4_governance_monitoring",
    "phase_5_strategic_learning_analysis",
    "phase_6_outcome_gap_analysis",
    "phase_7_strategic_improvement_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

OVERSIGHT_MATURITY_LEVELS: Final[tuple[str, ...]] = (
    "tracked",
    "governed",
    "measured",
    "learning",
    "adaptive",
)

OVERSIGHT_METRICS: Final[tuple[str, ...]] = (
    "initiative_success_rate",
    "milestone_completion_rate",
    "governance_compliance_score",
    "outcome_realization_score",
    "strategic_learning_score",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 325",
    "FIX 326",
    "FIX 330",
)

RISK_MONITORING_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 309",
    "FIX 313",
    "FIX 324",
    "FIX 325",
)

OVERSIGHT_INITIATIVE_MIN_SIZE: Final[int] = 1

HUMAN_STRATEGIC_OVERSIGHT_DECISION_KINDS: Final[tuple[str, ...]] = (
    "strategic_oversight_review_approve",
    "strategic_oversight_review_hold",
    "strategic_oversight_review_reject",
    "strategic_oversight_review_defer",
)

STRATEGIC_OVERSIGHT_RECORD_KINDS: Final[tuple[str, ...]] = (
    "strategic_oversight_note",
    "strategic_oversight_milestone_entry",
    "strategic_oversight_status_entry",
    *HUMAN_STRATEGIC_OVERSIGHT_DECISION_KINDS,
    "strategic_oversight_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_execution_authority",
    "no_strategy_mutation",
    "no_budget_allocation",
    "no_resource_commitment",
    "no_governance_bypass",
    "no_automatic_initiative_changes",
)

FORBIDDEN_OVERSIGHT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("execution_authority", "Never execute initiatives from strategic oversight program."),
    ("strategy_mutation", "Never modify strategy from outcome governance."),
    ("budget_allocation", "Never allocate budget from oversight monitoring."),
    ("resource_commitment", "Never commit resources from outcome governance."),
    ("governance_bypass", "Never bypass governance from oversight program."),
    ("automatic_initiative_changes", "Never auto-change initiatives from oversight analysis."),
)

MAX_STRATEGIC_OVERSIGHT_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_STRATEGIC_OVERSIGHT_RECORDS: Final[int] = 500

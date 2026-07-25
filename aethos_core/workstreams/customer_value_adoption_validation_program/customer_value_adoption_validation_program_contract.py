# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F2 / FIX 348 — customer value & adoption validation program contract."""

from __future__ import annotations

from typing import Final

CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID: Final[str] = "WORKSTREAM_F2"
CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_FIX: Final[str] = "FIX 348"
CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_customer_value_adoption_validation_program_v1"
)
CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_customer_value_adoption_validation_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "value_validation_measures_customer_outcomes_without_customer_manipulation_or_outreach"
)

MUTATION_PERFORMED_FIX_348: Final[bool] = False
EXECUTION_PERFORMED_FIX_348: Final[bool] = False
CUSTOMER_MANIPULATION_FIX_348: Final[bool] = False
AUTOMATED_OUTREACH_FIX_348: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_348: Final[bool] = False
AUTHORITY_EXPANSION_FIX_348: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_348: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_348: Final[bool] = False
LOCAL_VALUE_VALIDATION_EXECUTABLE_FIX_348: Final[bool] = True

CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_customer_value_adoption_validation_program"
)

CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_INVARIANT: Final[str] = (
    "customer_value_adoption_validation_without_manipulation_outreach_or_authority_expansion"
)

CUSTOMER_VALUE_ADOPTION_VALIDATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_delivered_solution_registry",
    "phase_2_usage_observation",
    "phase_3_adoption_analysis",
    "phase_4_value_validation",
    "phase_5_retention_intelligence",
    "phase_6_friction_analysis",
    "phase_7_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

VALIDATION_METRICS: Final[tuple[str, ...]] = (
    "adoption_rate",
    "repeat_usage_rate",
    "retention_rate",
    "value_realization_score",
    "customer_satisfaction_trend",
    "abandonment_rate",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 310",
    "FIX 320",
    "FIX 323",
    "FIX 330",
)

HUMAN_CUSTOMER_VALUE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "customer_value_review_approve",
    "customer_value_review_hold",
    "customer_value_review_reject",
    "customer_value_review_defer",
)

CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "customer_value_note",
    "customer_usage_observation",
    *HUMAN_CUSTOMER_VALUE_DECISION_KINDS,
    "customer_value_validation_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_customer_targeting",
    "no_customer_manipulation",
    "no_automated_outreach",
    "no_automatic_product_changes",
    "no_automatic_roadmap_changes",
    "no_authority_expansion",
)

FORBIDDEN_VALIDATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("customer_manipulation", "Never manipulate customer behavior during validation."),
    ("automated_outreach", "Never automate customer outreach from validation program."),
    ("customer_targeting", "Never target customers for persuasion from validation layer."),
    ("automatic_product_changes", "Never change product automatically from validation evidence."),
    ("authority_expansion", "Never expand authority from value validation program."),
)

MAX_CUSTOMER_VALUE_ADOPTION_VALIDATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORDS: Final[int] = 500

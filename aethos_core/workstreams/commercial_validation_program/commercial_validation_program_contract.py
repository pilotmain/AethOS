# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F5 / FIX 351 — commercial validation program contract."""

from __future__ import annotations

from typing import Final

COMMERCIAL_VALIDATION_PROGRAM_ID: Final[str] = "WORKSTREAM_F5"
COMMERCIAL_VALIDATION_PROGRAM_FIX: Final[str] = "FIX 351"
COMMERCIAL_VALIDATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_commercial_validation_program_v1"
)
COMMERCIAL_VALIDATION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_commercial_validation_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "commercial_validation_measures_business_outcomes_without_commercial_authority"
)

MUTATION_PERFORMED_FIX_351: Final[bool] = False
EXECUTION_PERFORMED_FIX_351: Final[bool] = False
COMMERCIAL_AUTHORITY_FIX_351: Final[bool] = False
PAYMENT_PROCESSING_FIX_351: Final[bool] = False
AUTOMATIC_PLAN_UPGRADE_FIX_351: Final[bool] = False
AUTOMATIC_PLAN_DOWNGRADE_FIX_351: Final[bool] = False
PRICING_MUTATION_FIX_351: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_351: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_351: Final[bool] = False
AUTHORITY_EXPANSION_FIX_351: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_351: Final[bool] = False
LOCAL_COMMERCIAL_VALIDATION_EXECUTABLE_FIX_351: Final[bool] = True

COMMERCIAL_VALIDATION_PROGRAM_ROUTE_ID: Final[str] = "workstream_commercial_validation_program"

COMMERCIAL_VALIDATION_PROGRAM_INVARIANT: Final[str] = (
    "commercial_validation_without_commercial_authority_payment_processing_or_plan_mutation"
)

COMMERCIAL_VALIDATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_commercial_cohort_registry",
    "phase_2_adoption_to_plan_analysis",
    "phase_3_retention_analysis",
    "phase_4_expansion_analysis",
    "phase_5_value_to_revenue_analysis",
    "phase_6_commercial_friction_analysis",
    "phase_7_commercial_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

COMMERCIAL_COHORT_MIN_SIZE: Final[int] = 3

COMMERCIAL_PLANS: Final[tuple[str, ...]] = (
    "FREE",
    "STARTER",
    "PRO",
    "BUSINESS",
    "ENTERPRISE",
)

COMMERCIAL_METRICS: Final[tuple[str, ...]] = (
    "activation_rate",
    "retention_rate",
    "expansion_rate",
    "plan_adoption",
    "plan_conversion",
    "value_realization_score",
    "commercial_sustainability_score",
)

ADOPTION_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 305",
    "FIX 308",
    "FIX 318",
    "FIX 320",
)

RETENTION_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 320",
    "FIX 321",
    "FIX 323",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 305",
    "FIX 308",
    "FIX 320",
    "FIX 323",
    "FIX 330",
)

HUMAN_COMMERCIAL_VALIDATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "commercial_validation_review_approve",
    "commercial_validation_review_hold",
    "commercial_validation_review_reject",
    "commercial_validation_review_defer",
)

COMMERCIAL_VALIDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "commercial_validation_note",
    "commercial_cohort_entry",
    *HUMAN_COMMERCIAL_VALIDATION_DECISION_KINDS,
    "commercial_validation_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_payment_processing",
    "no_automatic_billing",
    "no_automatic_upgrades",
    "no_automatic_downgrades",
    "no_pricing_mutation",
    "no_authority_expansion",
)

FORBIDDEN_COMMERCIAL_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("commercial_authority", "Never grant commercial authority from validation evidence."),
    ("payment_processing", "Never charge customers or process payments from validation."),
    ("automatic_plan_upgrades", "Never upgrade plans automatically from validation evidence."),
    ("automatic_plan_downgrades", "Never downgrade plans automatically from validation evidence."),
    ("pricing_mutation", "Never mutate pricing from validation program."),
    ("authority_expansion", "Never expand authority from commercial validation."),
)

MAX_COMMERCIAL_VALIDATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_COMMERCIAL_VALIDATION_RECORDS: Final[int] = 500

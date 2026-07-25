# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F6 / FIX 352 — unit economics & business sustainability program contract."""

from __future__ import annotations

from typing import Final

UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ID: Final[str] = "WORKSTREAM_F6"
UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_FIX: Final[str] = "FIX 352"
UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_unit_economics_business_sustainability_program_v1"
)
UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_unit_economics_business_sustainability_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "economic_validation_measures_sustainability_signals_without_commercial_authority"
)

MUTATION_PERFORMED_FIX_352: Final[bool] = False
EXECUTION_PERFORMED_FIX_352: Final[bool] = False
COMMERCIAL_AUTHORITY_FIX_352: Final[bool] = False
PAYMENT_PROCESSING_FIX_352: Final[bool] = False
BILLING_EXECUTION_FIX_352: Final[bool] = False
PRICING_MUTATION_FIX_352: Final[bool] = False
PLAN_MUTATION_FIX_352: Final[bool] = False
FINANCIAL_FORECASTING_AS_FACT_FIX_352: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_352: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_352: Final[bool] = False
AUTHORITY_EXPANSION_FIX_352: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_352: Final[bool] = False
LOCAL_ECONOMIC_VALIDATION_EXECUTABLE_FIX_352: Final[bool] = True

UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_unit_economics_business_sustainability_program"
)

UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_INVARIANT: Final[str] = (
    "economic_validation_without_commercial_authority_billing_execution_or_financial_forecasting_as_fact"
)

UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PHASES: Final[tuple[str, ...]] = (
    "phase_1_economic_cohort_registry",
    "phase_2_delivery_cost_analysis",
    "phase_3_customer_success_cost_analysis",
    "phase_4_retention_economics",
    "phase_5_unit_economics_analysis",
    "phase_6_economic_friction_analysis",
    "phase_7_sustainability_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

ECONOMIC_COHORT_MIN_SIZE: Final[int] = 3

ET_COST_STAGES: Final[tuple[tuple[str, str], ...]] = (
    ("workspace", "et1_workspace"),
    ("generation", "et2_code_generation"),
    ("git_delivery", "et3_git_delivery"),
    ("deployment", "et4_deployment"),
    ("certification", "et5_certification"),
)

ECONOMIC_METRICS: Final[tuple[str, ...]] = (
    "delivery_cost",
    "support_cost",
    "retention_strength",
    "expansion_strength",
    "sustainability_score",
    "operational_efficiency_score",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 305",
    "FIX 308",
    "FIX 320",
    "FIX 323",
    "FIX 330",
)

HUMAN_BUSINESS_SUSTAINABILITY_DECISION_KINDS: Final[tuple[str, ...]] = (
    "business_sustainability_review_approve",
    "business_sustainability_review_hold",
    "business_sustainability_review_reject",
    "business_sustainability_review_defer",
)

BUSINESS_SUSTAINABILITY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "business_sustainability_note",
    "economic_cohort_entry",
    *HUMAN_BUSINESS_SUSTAINABILITY_DECISION_KINDS,
    "business_sustainability_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_billing_execution",
    "no_pricing_changes",
    "no_plan_mutation",
    "no_payment_processing",
    "no_authority_expansion",
    "no_financial_forecasting_presented_as_fact",
)

FORBIDDEN_ECONOMIC_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("commercial_authority", "Never grant commercial authority from economic validation."),
    ("billing_execution", "Never execute billing from sustainability evidence."),
    ("payment_processing", "Never process payments from economic validation."),
    ("pricing_mutation", "Never alter pricing from sustainability program."),
    ("plan_mutation", "Never mutate plans from economic validation."),
    ("financial_forecasting_as_fact", "Never present financial forecasts as established fact."),
)

MAX_BUSINESS_SUSTAINABILITY_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_BUSINESS_SUSTAINABILITY_RECORDS: Final[int] = 500

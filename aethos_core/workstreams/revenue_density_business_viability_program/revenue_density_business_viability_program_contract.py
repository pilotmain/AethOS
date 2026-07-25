# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G3 / FIX 356 — revenue density & business viability program contract."""

from __future__ import annotations

from typing import Final

REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID: Final[str] = "WORKSTREAM_G3"
REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_FIX: Final[str] = "FIX 356"
REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_revenue_density_business_viability_program_v1"
)
REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_revenue_density_business_viability_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "revenue_density_measures_business_signals_without_commercial_authority"
)

MUTATION_PERFORMED_FIX_356: Final[bool] = False
EXECUTION_PERFORMED_FIX_356: Final[bool] = False
COMMERCIAL_AUTHORITY_FIX_356: Final[bool] = False
PAYMENT_PROCESSING_FIX_356: Final[bool] = False
BILLING_EXECUTION_FIX_356: Final[bool] = False
SUBSCRIPTION_MUTATION_FIX_356: Final[bool] = False
PLAN_UPGRADE_FIX_356: Final[bool] = False
PRICING_MUTATION_FIX_356: Final[bool] = False
AUTHORITY_EXPANSION_FIX_356: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_356: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_356: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_356: Final[bool] = False
LOCAL_REVENUE_DENSITY_EXECUTABLE_FIX_356: Final[bool] = True

REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_revenue_density_business_viability_program"
)

REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_INVARIANT: Final[str] = (
    "revenue_density_without_commercial_authority_billing_execution_or_plan_mutation"
)

REVENUE_DENSITY_BUSINESS_VIABILITY_PHASES: Final[tuple[str, ...]] = (
    "phase_1_revenue_cohort_registry",
    "phase_2_plan_utilization_analysis",
    "phase_3_expansion_potential_analysis",
    "phase_4_retention_value_analysis",
    "phase_5_revenue_signal_analysis",
    "phase_6_revenue_friction_analysis",
    "phase_7_revenue_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

REVENUE_COHORT_MIN_SIZE: Final[int] = 3

COMMERCIAL_PLANS: Final[tuple[str, ...]] = (
    "FREE",
    "STARTER",
    "PRO",
    "BUSINESS",
    "ENTERPRISE",
)

REVENUE_MATURITY_LEVELS: Final[tuple[str, ...]] = (
    "potential",
    "emerging",
    "viable",
    "sustainable",
)

REVENUE_DENSITY_METRICS: Final[tuple[str, ...]] = (
    "plan_utilization_score",
    "expansion_score",
    "retention_strength",
    "adoption_strength",
    "revenue_density_score",
    "business_viability_score",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 305",
    "FIX 308",
    "FIX 320",
    "FIX 323",
    "FIX 330",
)

HUMAN_REVENUE_DENSITY_DECISION_KINDS: Final[tuple[str, ...]] = (
    "revenue_density_review_approve",
    "revenue_density_review_hold",
    "revenue_density_review_reject",
    "revenue_density_review_defer",
)

REVENUE_DENSITY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "revenue_density_note",
    "revenue_cohort_entry",
    *HUMAN_REVENUE_DENSITY_DECISION_KINDS,
    "revenue_density_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_billing_execution",
    "no_payment_processing",
    "no_subscription_mutation",
    "no_plan_upgrades",
    "no_pricing_changes",
    "no_authority_expansion",
)

FORBIDDEN_REVENUE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("commercial_authority", "Never grant commercial authority from revenue density validation."),
    ("billing_execution", "Never execute billing from revenue density program."),
    ("payment_processing", "Never process payments from revenue density validation."),
    ("subscription_mutation", "Never mutate subscriptions from revenue signals."),
    ("plan_upgrades", "Never upgrade plans automatically from revenue density evidence."),
    ("pricing_mutation", "Never alter pricing from revenue density program."),
    ("authority_expansion", "Never expand authority from business viability validation."),
)

MAX_REVENUE_DENSITY_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_REVENUE_DENSITY_RECORDS: Final[int] = 500

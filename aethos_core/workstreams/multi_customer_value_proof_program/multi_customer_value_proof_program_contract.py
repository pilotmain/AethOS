# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F3 / FIX 349 — multi-customer value proof program contract."""

from __future__ import annotations

from typing import Final

MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID: Final[str] = "WORKSTREAM_F3"
MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_FIX: Final[str] = "FIX 349"
MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_multi_customer_value_proof_program_v1"
)
MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_multi_customer_value_proof_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "multi_customer_validation_measures_repeatable_outcomes_without_customer_authority"
)

MUTATION_PERFORMED_FIX_349: Final[bool] = False
EXECUTION_PERFORMED_FIX_349: Final[bool] = False
CUSTOMER_AUTHORITY_FIX_349: Final[bool] = False
CUSTOMER_MANIPULATION_FIX_349: Final[bool] = False
AUTOMATED_OUTREACH_FIX_349: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_349: Final[bool] = False
AUTHORITY_EXPANSION_FIX_349: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_349: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_349: Final[bool] = False
LOCAL_MULTI_CUSTOMER_PROOF_EXECUTABLE_FIX_349: Final[bool] = True

MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_multi_customer_value_proof_program"
)

MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_INVARIANT: Final[str] = (
    "multi_customer_value_proof_without_customer_authority_manipulation_or_outreach"
)

MULTI_CUSTOMER_VALUE_PROOF_PHASES: Final[tuple[str, ...]] = (
    "phase_1_customer_cohort_registry",
    "phase_2_delivery_outcome_registry",
    "phase_3_adoption_analysis",
    "phase_4_value_analysis",
    "phase_5_retention_analysis",
    "phase_6_success_pattern_discovery",
    "phase_7_value_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

COHORT_MIN_SIZE: Final[int] = 2

DELIVERY_TYPES: Final[tuple[str, ...]] = (
    "fastapi_microservice",
    "nextjs_landing_page",
    "health_check_endpoint",
    "admin_dashboard",
    "automation_utility",
)

PROOF_METRICS: Final[tuple[str, ...]] = (
    "adoption_rate",
    "retention_rate",
    "value_realization_score",
    "customer_satisfaction",
    "repeatability_score",
    "success_pattern_frequency",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 320",
    "FIX 323",
    "FIX 330",
)

HUMAN_MULTI_CUSTOMER_DECISION_KINDS: Final[tuple[str, ...]] = (
    "multi_customer_review_approve",
    "multi_customer_review_hold",
    "multi_customer_review_reject",
    "multi_customer_review_defer",
)

MULTI_CUSTOMER_VALUE_PROOF_RECORD_KINDS: Final[tuple[str, ...]] = (
    "multi_customer_note",
    "multi_customer_cohort_entry",
    *HUMAN_MULTI_CUSTOMER_DECISION_KINDS,
    "multi_customer_value_proof_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_customer_manipulation",
    "no_automated_outreach",
    "no_automatic_roadmap_changes",
    "no_authority_expansion",
    "no_customer_targeting",
)

FORBIDDEN_PROOF_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("customer_authority", "Never grant customer authority from multi-customer proof."),
    ("customer_manipulation", "Never manipulate customers during multi-customer validation."),
    ("automated_outreach", "Never automate outreach from proof program."),
    ("customer_targeting", "Never target customers for persuasion."),
    ("authority_expansion", "Never expand authority from proof evidence."),
)

MAX_MULTI_CUSTOMER_VALUE_PROOF_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_MULTI_CUSTOMER_VALUE_PROOF_RECORDS: Final[int] = 500

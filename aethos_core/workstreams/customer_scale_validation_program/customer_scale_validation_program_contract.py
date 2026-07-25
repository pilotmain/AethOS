# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F4 / FIX 350 — customer scale validation program contract."""

from __future__ import annotations

from typing import Final

CUSTOMER_SCALE_VALIDATION_PROGRAM_ID: Final[str] = "WORKSTREAM_F4"
CUSTOMER_SCALE_VALIDATION_PROGRAM_FIX: Final[str] = "FIX 350"
CUSTOMER_SCALE_VALIDATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_customer_scale_validation_program_v1"
)
CUSTOMER_SCALE_VALIDATION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_customer_scale_validation_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "customer_scale_validation_measures_operational_capability_without_customer_authority"
)

MUTATION_PERFORMED_FIX_350: Final[bool] = False
EXECUTION_PERFORMED_FIX_350: Final[bool] = False
CUSTOMER_AUTHORITY_FIX_350: Final[bool] = False
CUSTOMER_MANIPULATION_FIX_350: Final[bool] = False
AUTOMATED_OUTREACH_FIX_350: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_350: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_350: Final[bool] = False
AUTHORITY_EXPANSION_FIX_350: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_350: Final[bool] = False
LOCAL_SCALE_VALIDATION_EXECUTABLE_FIX_350: Final[bool] = True

CUSTOMER_SCALE_VALIDATION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_customer_scale_validation_program"
)

CUSTOMER_SCALE_VALIDATION_PROGRAM_INVARIANT: Final[str] = (
    "customer_scale_validation_without_customer_authority_governance_bypass_or_manipulation"
)

CUSTOMER_SCALE_VALIDATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_scale_cohort_registry",
    "phase_2_concurrent_delivery_analysis",
    "phase_3_governance_capacity_analysis",
    "phase_4_execution_capacity_analysis",
    "phase_5_provider_capacity_analysis",
    "phase_6_customer_outcome_stability",
    "phase_7_scale_bottleneck_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

SCALE_COHORT_MIN_SIZE: Final[int] = 3

SCALE_PROVIDERS: Final[tuple[str, ...]] = (
    "Railway",
    "Vercel",
    "AWS",
    "Kubernetes",
    "Azure",
    "GCP",
)

SCALE_METRICS: Final[tuple[str, ...]] = (
    "concurrent_customers",
    "delivery_throughput",
    "deployment_throughput",
    "governance_latency_ms",
    "approval_latency_ms",
    "adoption_rate",
    "retention_rate",
    "value_realization_score",
    "customer_satisfaction_trend",
    "bottleneck_frequency",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 320",
    "FIX 323",
    "FIX 329",
    "FIX 330",
)

HUMAN_CUSTOMER_SCALE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "customer_scale_review_approve",
    "customer_scale_review_hold",
    "customer_scale_review_reject",
    "customer_scale_review_defer",
)

CUSTOMER_SCALE_VALIDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "customer_scale_note",
    "customer_scale_cohort_entry",
    *HUMAN_CUSTOMER_SCALE_DECISION_KINDS,
    "customer_scale_validation_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_customer_targeting",
    "no_automated_outreach",
    "no_automatic_plan_upgrades",
    "no_authority_expansion",
    "no_governance_bypass",
    "no_customer_manipulation",
)

FORBIDDEN_SCALE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("customer_authority", "Never grant customer authority from scale validation."),
    ("governance_bypass", "Never bypass governance during scale validation."),
    ("customer_manipulation", "Never manipulate customers during scale validation."),
    ("automatic_plan_upgrades", "Never upgrade plans automatically from scale evidence."),
    ("authority_expansion", "Never expand authority from scale program."),
)

MAX_CUSTOMER_SCALE_VALIDATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_CUSTOMER_SCALE_VALIDATION_RECORDS: Final[int] = 500

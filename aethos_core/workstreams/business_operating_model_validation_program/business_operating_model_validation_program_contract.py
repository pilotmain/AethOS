# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F7 / FIX 353 — business operating model validation program contract."""

from __future__ import annotations

from typing import Final

BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID: Final[str] = "WORKSTREAM_F7"
BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_FIX: Final[str] = "FIX 353"
BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_business_operating_model_validation_program_v1"
)
BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_business_operating_model_validation_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "operating_model_validation_measures_sustainability_without_operating_authority"
)

MUTATION_PERFORMED_FIX_353: Final[bool] = False
EXECUTION_PERFORMED_FIX_353: Final[bool] = False
OPERATING_AUTHORITY_FIX_353: Final[bool] = False
GOVERNANCE_MUTATION_FIX_353: Final[bool] = False
AUTHORITY_EXPANSION_FIX_353: Final[bool] = False
PRICING_MUTATION_FIX_353: Final[bool] = False
PROVIDER_MUTATION_FIX_353: Final[bool] = False
ORGANIZATIONAL_RESTRUCTURING_FIX_353: Final[bool] = False
BUSINESS_AUTOMATION_FIX_353: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_353: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_353: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_353: Final[bool] = False
LOCAL_OPERATING_MODEL_VALIDATION_EXECUTABLE_FIX_353: Final[bool] = True

BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_business_operating_model_validation_program"
)

BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_INVARIANT: Final[str] = (
    "operating_model_validation_without_operating_authority_governance_mutation_or_provider_mutation"
)

BUSINESS_OPERATING_MODEL_VALIDATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_operating_model_registry",
    "phase_2_delivery_sustainability_analysis",
    "phase_3_support_sustainability_analysis",
    "phase_4_governance_sustainability_analysis",
    "phase_5_provider_sustainability_analysis",
    "phase_6_economic_sustainability_analysis",
    "phase_7_operating_model_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

OPERATING_MODEL_COHORT_MIN_SIZE: Final[int] = 3

OPERATING_MODEL_PROVIDERS: Final[tuple[str, ...]] = (
    "Railway",
    "Vercel",
    "AWS",
    "Kubernetes",
    "Azure",
    "GCP",
)

OPERATING_MODEL_METRICS: Final[tuple[str, ...]] = (
    "delivery_efficiency",
    "governance_efficiency",
    "support_efficiency",
    "provider_efficiency",
    "business_sustainability_score",
    "operating_leverage_score",
)

GOVERNANCE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 302",
    "FIX 307",
    "FIX 313",
)

PROVIDER_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 303",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 324",
    "FIX 325",
    "FIX 329",
    "FIX 330",
)

HUMAN_OPERATING_MODEL_DECISION_KINDS: Final[tuple[str, ...]] = (
    "operating_model_review_approve",
    "operating_model_review_hold",
    "operating_model_review_reject",
    "operating_model_review_defer",
)

OPERATING_MODEL_RECORD_KINDS: Final[tuple[str, ...]] = (
    "operating_model_note",
    "operating_model_cohort_entry",
    *HUMAN_OPERATING_MODEL_DECISION_KINDS,
    "operating_model_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_governance_mutation",
    "no_authority_expansion",
    "no_pricing_mutation",
    "no_provider_mutation",
    "no_organizational_restructuring",
    "no_business_automation",
)

FORBIDDEN_OPERATING_MODEL_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("operating_authority", "Never grant operating authority from validation evidence."),
    ("governance_mutation", "Never change governance from operating model validation."),
    ("authority_expansion", "Never expand authority from operating model program."),
    ("pricing_mutation", "Never alter pricing from operating model validation."),
    ("provider_mutation", "Never mutate providers from operating model validation."),
    ("organizational_restructuring", "Never restructure organization from validation program."),
    ("business_automation", "Never automate business decisions from validation evidence."),
)

MAX_OPERATING_MODEL_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_OPERATING_MODEL_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_B1 — limited external customer validation program contract."""

from __future__ import annotations

from typing import Final

LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_ID: Final[str] = "WORKSTREAM_B1"
LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_limited_external_customer_validation_program_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "customer_validation_gathers_evidence_humans_approve_admissions_and_review_outcomes"
)

VALIDATION_COHORT_TARGET_SIZE: Final[int] = 10
VALIDATION_COHORT_MIN_SIZE: Final[int] = 5

COHORT_PROFILES: Final[tuple[str, ...]] = (
    "technical_founders",
    "solo_developers",
    "engineering_managers",
    "platform_engineers",
)

COHORT_AVOID: Final[tuple[str, ...]] = (
    "enterprise_rollouts",
    "production_critical_customers",
    "high_risk_environments",
)

SUCCESS_QUESTIONS: Final[tuple[str, ...]] = (
    "understand_what_aethos_is",
    "complete_onboarding",
    "connect_a_provider",
    "understand_trust_boundaries",
    "run_governed_workflow",
    "obtain_value",
    "return_voluntarily",
)

LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_candidate_selection",
    "phase_2_onboarding_validation",
    "phase_3_provider_connection_validation",
    "phase_4_trust_understanding_validation",
    "phase_5_first_workflow_validation",
    "phase_6_customer_feedback_collection",
    "phase_7_value_realization_validation",
    "phase_8_product_market_signal_review",
)

PHASE_OUTPUTS: Final[tuple[str, ...]] = (
    "validation_candidate_registry",
    "validation_admission_review",
    "onboarding_validation_report",
    "provider_validation_report",
    "trust_understanding_report",
    "workflow_validation_report",
    "validation_feedback_registry",
    "validation_feedback_report",
    "customer_value_validation_report",
    "pmf_signal_report",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_new_intelligence_modules",
    "no_new_governance_modules",
    "no_new_trust_systems",
    "no_enterprise_rollout",
    "no_provider_expansion",
    "no_architecture_redesign",
)

PROVIDER_TARGETS: Final[tuple[str, ...]] = ("GitHub", "Railway", "Vercel")

# SPDX-License-Identifier: Apache-2.0
"""PHASE_J3 / FIX 366 — compounding value & continuous improvement program contract."""

from __future__ import annotations

from typing import Final

COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID: Final[str] = "PHASE_J3"
COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_FIX: Final[str] = "FIX 366"
COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "phase_compounding_value_continuous_improvement_program_v1"
)
COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "phase_compounding_value_continuous_improvement_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "continuous_improvement_measurement_tracks_compounding_value_without_autonomous_self_modification"
)

MUTATION_PERFORMED_FIX_366: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_366: Final[bool] = False
AUTONOMOUS_SELF_MODIFICATION_FIX_366: Final[bool] = False
AUTOMATIC_POLICY_CHANGES_FIX_366: Final[bool] = False
AUTONOMOUS_STRATEGIC_CONTROL_FIX_366: Final[bool] = False
AUTHORITY_EXPANSION_FIX_366: Final[bool] = False
GOVERNANCE_MUTATION_FIX_366: Final[bool] = False
GOVERNANCE_BYPASS_FIX_366: Final[bool] = False
TRUST_PROMOTION_FIX_366: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_366: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_366: Final[bool] = False
LOCAL_COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_EXECUTABLE_FIX_366: Final[bool] = True

COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ROUTE_ID: Final[str] = (
    "phase_compounding_value_continuous_improvement_program"
)

COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_INVARIANT: Final[str] = (
    "continuous_improvement_measurement_without_autonomous_self_modification_governance_mutation_or_trust_promotion"
)

COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PHASES: Final[tuple[str, ...]] = (
    "phase_1_improvement_baseline_registry",
    "phase_2_delivery_improvement_analysis",
    "phase_3_operational_improvement_analysis",
    "phase_4_customer_improvement_analysis",
    "phase_5_business_improvement_analysis",
    "phase_6_learning_effectiveness_analysis",
    "phase_7_improvement_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

IMPROVEMENT_LEVELS: Final[tuple[str, ...]] = (
    "static",
    "improving",
    "consistent",
    "compounding",
    "transformative",
)

IMPROVEMENT_CATEGORIES: Final[tuple[str, ...]] = (
    "delivery",
    "deployment",
    "recovery",
    "customer",
    "business",
    "operational",
)

COMPOUNDING_VALUE_METRICS: Final[tuple[str, ...]] = (
    "improvement_velocity",
    "delivery_improvement_score",
    "operational_improvement_score",
    "customer_improvement_score",
    "business_improvement_score",
    "compounding_value_score",
)

EXECUTIVE_WORKSTREAM_MODULES: Final[tuple[str, ...]] = (
    "PHASE_J1",
    "PHASE_J2",
    "WORKSTREAM_H3",
    "WORKSTREAM_G4",
    "FIX_330",
)

HUMAN_CONTINUOUS_IMPROVEMENT_DECISION_KINDS: Final[tuple[str, ...]] = (
    "continuous_improvement_review_approve",
    "continuous_improvement_review_hold",
    "continuous_improvement_review_reject",
    "continuous_improvement_review_defer",
)

CONTINUOUS_IMPROVEMENT_RECORD_KINDS: Final[tuple[str, ...]] = (
    "continuous_improvement_note",
    "continuous_improvement_baseline_entry",
    *HUMAN_CONTINUOUS_IMPROVEMENT_DECISION_KINDS,
    "continuous_improvement_record",
)

IMPROVEMENT_BASELINE_MIN_SIZE: Final[int] = 1

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_self_modification",
    "no_governance_mutation",
    "no_authority_expansion",
    "no_trust_promotion",
    "no_automatic_policy_changes",
    "no_autonomous_strategic_control",
)

FORBIDDEN_CONTINUOUS_IMPROVEMENT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_self_modification", "Never modify the platform from improvement measurement."),
    ("automatic_policy_changes", "Never change execution policies from improvement measurement."),
    ("authority_expansion", "Never expand authority from continuous improvement measurement."),
    ("governance_mutation", "Never bypass or alter governance from improvement measurement."),
    ("governance_bypass", "Never bypass approvals from continuous improvement measurement."),
    ("trust_promotion", "Never promote trust from improvement measurement."),
    ("autonomous_strategic_control", "Never assume strategic control from improvement measurement."),
)

MAX_CONTINUOUS_IMPROVEMENT_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_CONTINUOUS_IMPROVEMENT_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""PHASE_I1 / FIX 361 — autonomous execution maturity program contract."""

from __future__ import annotations

from typing import Final

AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID: Final[str] = "PHASE_I1"
AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_FIX: Final[str] = "FIX 361"
AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "phase_autonomous_execution_maturity_program_v1"
)
AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "phase_autonomous_execution_maturity_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "autonomous_execution_maturity_measures_capability_without_autonomous_authority"
)

MUTATION_PERFORMED_FIX_361: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_361: Final[bool] = False
AUTONOMOUS_AUTHORITY_FIX_361: Final[bool] = False
AUTHORITY_EXPANSION_FIX_361: Final[bool] = False
GOVERNANCE_MUTATION_FIX_361: Final[bool] = False
GOVERNANCE_BYPASS_FIX_361: Final[bool] = False
TRUST_PROMOTION_FIX_361: Final[bool] = False
AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_361: Final[bool] = False
AUTONOMOUS_STRATEGIC_CONTROL_FIX_361: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_361: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_361: Final[bool] = False
LOCAL_AUTONOMOUS_EXECUTION_MATURITY_EXECUTABLE_FIX_361: Final[bool] = True

AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ROUTE_ID: Final[str] = (
    "phase_autonomous_execution_maturity_program"
)

AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_INVARIANT: Final[str] = (
    "autonomous_execution_maturity_without_autonomous_authority_governance_mutation_or_trust_promotion"
)

AUTONOMOUS_EXECUTION_MATURITY_PHASES: Final[tuple[str, ...]] = (
    "phase_1_autonomous_execution_registry",
    "phase_2_planning_accuracy_analysis",
    "phase_3_execution_success_analysis",
    "phase_4_recovery_analysis",
    "phase_5_human_intervention_analysis",
    "phase_6_autonomous_learning_analysis",
    "phase_7_autonomous_capability_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

AUTONOMOUS_MATURITY_LEVELS: Final[tuple[str, ...]] = (
    "assisted",
    "guided",
    "operational",
    "autonomous",
    "governed_autonomy",
)

EXECUTION_CATEGORIES: Final[tuple[str, ...]] = (
    "delivery",
    "deployment",
    "verification",
    "recovery",
    "operational",
)

AUTONOMOUS_EXECUTION_MATURITY_METRICS: Final[tuple[str, ...]] = (
    "planning_accuracy_score",
    "execution_success_rate",
    "recovery_effectiveness_score",
    "human_intervention_rate",
    "autonomous_learning_score",
    "autonomous_execution_maturity_score",
)

EXECUTIVE_WORKSTREAM_MODULES: Final[tuple[str, ...]] = (
    "WORKSTREAM_C1",
    "WORKSTREAM_C2",
    "WORKSTREAM_D1",
    "WORKSTREAM_D2",
    "WORKSTREAM_F1",
    "WORKSTREAM_H3",
)

HUMAN_AUTONOMOUS_EXECUTION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "autonomous_execution_review_approve",
    "autonomous_execution_review_hold",
    "autonomous_execution_review_reject",
    "autonomous_execution_review_defer",
)

AUTONOMOUS_EXECUTION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "autonomous_execution_note",
    "autonomous_execution_request_entry",
    *HUMAN_AUTONOMOUS_EXECUTION_DECISION_KINDS,
    "autonomous_execution_record",
)

AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE: Final[int] = 1

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_authority_expansion",
    "no_governance_mutation",
    "no_trust_promotion",
    "no_autonomous_organizational_control",
    "no_autonomous_strategic_control",
)

FORBIDDEN_AUTONOMOUS_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_authority", "Never grant autonomous authority from maturity measurement."),
    ("authority_expansion", "Never expand authority from autonomous execution maturity."),
    ("governance_mutation", "Never self-modify governance from maturity program."),
    ("governance_bypass", "Never bypass approvals from autonomous execution maturity."),
    ("trust_promotion", "Never self-promote trust from maturity measurement."),
    ("autonomous_organizational_control", "Never assume organizational control autonomously."),
    ("autonomous_strategic_control", "Never assume strategic control autonomously."),
)

MAX_AUTONOMOUS_EXECUTION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_AUTONOMOUS_EXECUTION_RECORDS: Final[int] = 500

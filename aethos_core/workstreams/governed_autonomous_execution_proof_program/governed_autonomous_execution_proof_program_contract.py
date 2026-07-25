# SPDX-License-Identifier: Apache-2.0
"""PHASE_I2 / FIX 362 — governed autonomous execution proof program contract."""

from __future__ import annotations

from typing import Final

GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID: Final[str] = "PHASE_I2"
GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_FIX: Final[str] = "FIX 362"
GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "phase_governed_autonomous_execution_proof_program_v1"
)
GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "phase_governed_autonomous_execution_proof_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "autonomous_execution_proof_measures_demonstrated_capability_without_autonomous_authority"
)

MUTATION_PERFORMED_FIX_362: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_362: Final[bool] = False
AUTONOMOUS_AUTHORITY_FIX_362: Final[bool] = False
AUTHORITY_EXPANSION_FIX_362: Final[bool] = False
GOVERNANCE_MUTATION_FIX_362: Final[bool] = False
GOVERNANCE_BYPASS_FIX_362: Final[bool] = False
TRUST_PROMOTION_FIX_362: Final[bool] = False
AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_362: Final[bool] = False
APPROVAL_BYPASS_FIX_362: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_362: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_362: Final[bool] = False
LOCAL_GOVERNED_AUTONOMOUS_EXECUTION_PROOF_EXECUTABLE_FIX_362: Final[bool] = True

GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ROUTE_ID: Final[str] = (
    "phase_governed_autonomous_execution_proof_program"
)

GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_INVARIANT: Final[str] = (
    "autonomous_execution_proof_without_autonomous_authority_governance_mutation_or_trust_promotion"
)

GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PHASES: Final[tuple[str, ...]] = (
    "phase_1_autonomous_run_registry",
    "phase_2_success_evidence_analysis",
    "phase_3_recovery_evidence_analysis",
    "phase_4_human_intervention_trend_analysis",
    "phase_5_capability_proof_analysis",
    "phase_6_operational_consistency_analysis",
    "phase_7_proof_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

AUTONOMOUS_PROOF_LEVELS: Final[tuple[str, ...]] = (
    "demonstrated",
    "repeatable",
    "reliable",
    "resilient",
    "proven",
)

EXECUTION_CATEGORIES: Final[tuple[str, ...]] = (
    "delivery",
    "deployment",
    "verification",
    "recovery",
    "operational",
)

VERIFICATION_STATES: Final[tuple[str, ...]] = (
    "pending",
    "verified",
    "failed",
)

AUTONOMOUS_EXECUTION_PROOF_METRICS: Final[tuple[str, ...]] = (
    "success_evidence_score",
    "recovery_evidence_score",
    "intervention_trend_score",
    "consistency_score",
    "autonomous_execution_proof_score",
)

EXECUTIVE_WORKSTREAM_MODULES: Final[tuple[str, ...]] = (
    "PHASE_I1",
    "WORKSTREAM_C1",
    "WORKSTREAM_C2",
    "WORKSTREAM_D2",
    "WORKSTREAM_F1",
    "WORKSTREAM_F2",
    "WORKSTREAM_F3",
    "WORKSTREAM_F4",
    "WORKSTREAM_F5",
    "WORKSTREAM_F6",
    "WORKSTREAM_F7",
    "WORKSTREAM_G4",
    "WORKSTREAM_H3",
)

HUMAN_AUTONOMOUS_PROOF_DECISION_KINDS: Final[tuple[str, ...]] = (
    "autonomous_proof_review_approve",
    "autonomous_proof_review_hold",
    "autonomous_proof_review_reject",
    "autonomous_proof_review_defer",
)

AUTONOMOUS_PROOF_RECORD_KINDS: Final[tuple[str, ...]] = (
    "autonomous_proof_note",
    "autonomous_proof_run_entry",
    *HUMAN_AUTONOMOUS_PROOF_DECISION_KINDS,
    "autonomous_proof_record",
)

AUTONOMOUS_PROOF_RUN_MIN_SIZE: Final[int] = 1
AUTONOMOUS_PROOF_REPEAT_MIN_SIZE: Final[int] = 2

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_authority_expansion",
    "no_governance_mutation",
    "no_trust_promotion",
    "no_approval_bypass",
    "no_autonomous_organizational_control",
)

FORBIDDEN_AUTONOMOUS_PROOF_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_authority", "Never grant autonomous authority from execution proof."),
    ("authority_expansion", "Never expand authority from autonomous execution proof."),
    ("governance_mutation", "Never self-modify governance from proof program."),
    ("governance_bypass", "Never bypass approvals from autonomous execution proof."),
    ("approval_bypass", "Never bypass human approvals from proof accumulation."),
    ("trust_promotion", "Never self-promote trust from execution proof."),
    ("autonomous_organizational_control", "Never assume organizational control autonomously."),
)

MAX_AUTONOMOUS_PROOF_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_AUTONOMOUS_PROOF_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""PHASE_I3 / FIX 363 — governed autonomous operations certification program contract."""

from __future__ import annotations

from typing import Final

GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID: Final[str] = "PHASE_I3"
GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_FIX: Final[str] = "FIX 363"
GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "phase_governed_autonomous_operations_certification_program_v1"
)
GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "phase_governed_autonomous_operations_certification_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "autonomous_operations_certification_measures_demonstrated_capability_without_autonomous_authority"
)

MUTATION_PERFORMED_FIX_363: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_363: Final[bool] = False
AUTONOMOUS_AUTHORITY_FIX_363: Final[bool] = False
AUTHORITY_EXPANSION_FIX_363: Final[bool] = False
GOVERNANCE_MUTATION_FIX_363: Final[bool] = False
GOVERNANCE_BYPASS_FIX_363: Final[bool] = False
TRUST_PROMOTION_FIX_363: Final[bool] = False
AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_363: Final[bool] = False
APPROVAL_BYPASS_FIX_363: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_363: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_363: Final[bool] = False
LOCAL_GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_EXECUTABLE_FIX_363: Final[bool] = True

GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ROUTE_ID: Final[str] = (
    "phase_governed_autonomous_operations_certification_program"
)

GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_INVARIANT: Final[str] = (
    "autonomous_operations_certification_without_autonomous_authority_governance_mutation_or_trust_promotion"
)

GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_certification_candidate_registry",
    "phase_2_reliability_certification_analysis",
    "phase_3_recovery_certification_analysis",
    "phase_4_human_intervention_certification_analysis",
    "phase_5_capability_certification_matrix",
    "phase_6_multi_environment_certification",
    "phase_7_certification_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

AUTONOMOUS_OPERATIONS_CERTIFICATION_LEVELS: Final[tuple[str, ...]] = (
    "demonstrated",
    "repeatable",
    "reliable",
    "resilient",
    "certified",
)

WORKLOAD_CATEGORIES: Final[tuple[str, ...]] = (
    "delivery",
    "deployment",
    "verification",
    "recovery",
    "operational",
)

PROVIDER_CATEGORIES: Final[tuple[str, ...]] = (
    "Railway",
    "Vercel",
    "AWS",
    "Kubernetes",
    "Azure",
    "GCP",
)

AUTONOMOUS_OPERATIONS_CERTIFICATION_METRICS: Final[tuple[str, ...]] = (
    "execution_reliability_score",
    "deployment_reliability_score",
    "verification_reliability_score",
    "recovery_certification_score",
    "intervention_certification_score",
    "autonomous_operations_certification_score",
)

EXECUTIVE_WORKSTREAM_MODULES: Final[tuple[str, ...]] = (
    "PHASE_I1",
    "PHASE_I2",
    "WORKSTREAM_D2",
    "WORKSTREAM_G4",
    "WORKSTREAM_H3",
)

HUMAN_AUTONOMOUS_CERTIFICATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "autonomous_certification_review_approve",
    "autonomous_certification_review_hold",
    "autonomous_certification_review_reject",
    "autonomous_certification_review_defer",
)

AUTONOMOUS_CERTIFICATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "autonomous_certification_note",
    "autonomous_certification_candidate_entry",
    *HUMAN_AUTONOMOUS_CERTIFICATION_DECISION_KINDS,
    "autonomous_certification_record",
)

AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE: Final[int] = 1
AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE: Final[int] = 2

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_authority_expansion",
    "no_governance_mutation",
    "no_trust_promotion",
    "no_approval_bypass",
    "no_autonomous_organizational_control",
)

FORBIDDEN_AUTONOMOUS_CERTIFICATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_authority", "Never grant autonomous authority from operations certification."),
    ("authority_expansion", "Never expand authority from autonomous operations certification."),
    ("governance_mutation", "Never alter governance from certification program."),
    ("governance_bypass", "Never bypass approvals from operations certification."),
    ("approval_bypass", "Never bypass human approvals from certification accumulation."),
    ("trust_promotion", "Never modify trust states from operations certification."),
    ("autonomous_organizational_control", "Never assume organizational control autonomously."),
)

MAX_AUTONOMOUS_CERTIFICATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_AUTONOMOUS_CERTIFICATION_RECORDS: Final[int] = 500

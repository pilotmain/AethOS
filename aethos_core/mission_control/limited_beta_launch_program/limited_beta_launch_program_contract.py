# SPDX-License-Identifier: Apache-2.0
"""FIX 312 — limited beta launch program contract."""

from __future__ import annotations

from typing import Final

LIMITED_BETA_LAUNCH_PROGRAM_SCHEMA_VERSION: Final[str] = "mission_control_limited_beta_launch_program_v1"
LIMITED_BETA_LAUNCH_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_limited_beta_launch_program_record_v1"
)
LIMITED_BETA_LAUNCH_PROGRAM_FIX: Final[str] = "FIX 312"

MUTATION_PERFORMED_FIX_312: Final[bool] = False
EXECUTION_PERFORMED_FIX_312: Final[bool] = False
BETA_AUTHORITY_FIX_312: Final[bool] = False
AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312: Final[bool] = False
AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312: Final[bool] = False
AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312: Final[bool] = False
AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_312: Final[bool] = False
BETA_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_312: Final[bool] = True

LIMITED_BETA_LAUNCH_PROGRAM_ROUTE_ID: Final[str] = "mission_control_limited_beta_launch_program"

LIMITED_BETA_LAUNCH_PROGRAM_INVARIANT: Final[str] = (
    "beta_program_management_without_customer_provisioning_authority"
)

BETA_PROGRAM_DOMAINS: Final[tuple[str, ...]] = (
    "beta_cohort_registry",
    "beta_candidate_registry",
    "beta_admission_review_registry",
    "beta_readiness_report",
    "beta_feedback_registry",
    "beta_risk_registry",
    "beta_success_metrics",
    "beta_operations_dashboard",
    "beta_evidence_registry",
    "beta_launch_recommendation",
)

BETA_LAUNCH_RECOMMENDATIONS: Final[tuple[str, ...]] = (
    "DO_NOT_LAUNCH",
    "LIMITED_BETA_READY",
    "EXPAND_BETA",
    "READY_FOR_PUBLIC_REVIEW",
)

COHORT_STATUSES: Final[tuple[str, ...]] = (
    "PLANNED",
    "ACTIVE",
    "PAUSED",
    "CLOSED",
)

HUMAN_BETA_ADMISSION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "beta_admission_review_decision_approve",
    "beta_admission_review_decision_hold",
    "beta_admission_review_decision_reject",
    "beta_admission_review_decision_defer",
)

HUMAN_BETA_LAUNCH_DECISION_KINDS: Final[tuple[str, ...]] = (
    "beta_launch_review_decision_approve",
    "beta_launch_review_decision_hold",
    "beta_launch_review_decision_reject",
    "beta_launch_review_decision_defer",
)

LIMITED_BETA_LAUNCH_PROGRAM_RECORD_KINDS: Final[tuple[str, ...]] = (
    "beta_candidate_note",
    *HUMAN_BETA_ADMISSION_DECISION_KINDS,
    *HUMAN_BETA_LAUNCH_DECISION_KINDS,
    "limited_beta_launch_program_record",
)

LIMITED_BETA_LAUNCH_PROGRAM_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("management_not_provisioning", "Beta program management ≠ customer provisioning authority."),
    ("human_admissions", "Humans remain responsible for beta admissions."),
    ("compose_only", "Composes FIX 300–311 evidence without user provisioning."),
    ("controlled_introduction", "Controlled framework for introducing real users before public launch."),
    ("feedback_tracking", "Product, usability, capability, and trust feedback tracked for review."),
    ("risk_visibility", "Product, operational, adoption, and governance risks visible before expansion."),
    ("evidence_recommendation", "Launch recommendation derived from evidence — not automatic launch."),
    ("success_metrics", "Activation, onboarding, provider, workflow, and health metrics aggregated."),
    ("no_entitlement_mutation", "No plan assignment, entitlement, or subscription mutation."),
    ("beta_operations", "Platform understands beta operations before public launch."),
)

FORBIDDEN_BETA_PROGRAM_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("user_provisioning", "Beta program never provisions users."),
    ("plan_assignment", "Beta program never assigns plans."),
    ("entitlement_mutation", "Beta program never mutates entitlements."),
    ("trust_mutation", "Beta program never mutates trust."),
    ("subscription_mutation", "Beta program never mutates subscriptions."),
    ("automatic_beta_expansion", "Beta program never expands beta automatically."),
    ("automatic_launch", "Beta program never launches automatically."),
)

LIMITED_BETA_LAUNCH_PROGRAM_EXECUTABLE: Final[bool] = False

MAX_LIMITED_BETA_LAUNCH_PROGRAM_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_LIMITED_BETA_LAUNCH_PROGRAM_RECORDS: Final[int] = 500

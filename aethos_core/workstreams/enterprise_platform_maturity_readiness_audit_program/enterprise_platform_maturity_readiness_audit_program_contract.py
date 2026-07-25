# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G4 / FIX 357 — enterprise platform maturity & readiness audit contract."""

from __future__ import annotations

from typing import Final

ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID: Final[str] = "WORKSTREAM_G4"
ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_FIX: Final[str] = "FIX 357"
ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_enterprise_platform_maturity_readiness_audit_program_v1"
)
ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_enterprise_platform_maturity_readiness_audit_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "platform_maturity_audit_evaluates_readiness_without_launch_authority"
)

MUTATION_PERFORMED_FIX_357: Final[bool] = False
EXECUTION_PERFORMED_FIX_357: Final[bool] = False
LAUNCH_AUTHORITY_FIX_357: Final[bool] = False
AUTHORITY_EXPANSION_FIX_357: Final[bool] = False
GOVERNANCE_MUTATION_FIX_357: Final[bool] = False
TRUST_PROMOTION_FIX_357: Final[bool] = False
BUSINESS_AUTOMATION_FIX_357: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_357: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_357: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_357: Final[bool] = False
LOCAL_PLATFORM_MATURITY_EXECUTABLE_FIX_357: Final[bool] = True

ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_enterprise_platform_maturity_readiness_audit_program"
)

ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_INVARIANT: Final[str] = (
    "platform_maturity_audit_without_launch_authority_governance_mutation_or_trust_promotion"
)

ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PHASES: Final[tuple[str, ...]] = (
    "phase_1_platform_inventory",
    "phase_2_architecture_maturity_audit",
    "phase_3_execution_maturity_audit",
    "phase_4_operational_maturity_audit",
    "phase_5_customer_commercial_maturity_audit",
    "phase_6_evidence_trust_maturity_audit",
    "phase_7_platform_gap_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

PLATFORM_MATURITY_LEVELS: Final[tuple[str, ...]] = (
    "foundational",
    "operational",
    "adopted",
    "sustainable",
    "enterprise_mature",
)

PLATFORM_MATURITY_METRICS: Final[tuple[str, ...]] = (
    "architecture_maturity_score",
    "execution_maturity_score",
    "operational_maturity_score",
    "customer_maturity_score",
    "commercial_maturity_score",
    "evidence_maturity_score",
    "overall_platform_maturity_score",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 330",
)

EXECUTIVE_WORKSTREAM_MODULES: Final[tuple[str, ...]] = (
    "WORKSTREAM_F7",
    "WORKSTREAM_G1",
    "WORKSTREAM_G2",
    "WORKSTREAM_G3",
)

HUMAN_PLATFORM_MATURITY_DECISION_KINDS: Final[tuple[str, ...]] = (
    "platform_maturity_review_approve",
    "platform_maturity_review_hold",
    "platform_maturity_review_reject",
    "platform_maturity_review_defer",
)

PLATFORM_MATURITY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "platform_maturity_note",
    *HUMAN_PLATFORM_MATURITY_DECISION_KINDS,
    "platform_maturity_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_launch_declaration",
    "no_authority_expansion",
    "no_governance_mutation",
    "no_trust_promotion",
    "no_business_automation",
    "no_organizational_restructuring",
)

FORBIDDEN_MATURITY_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("launch_authority", "Never declare launch from platform maturity audit."),
    ("authority_expansion", "Never expand authority from maturity assessment."),
    ("governance_mutation", "Never mutate governance from maturity audit."),
    ("trust_promotion", "Never promote trust from maturity assessment."),
    ("business_automation", "Never automate business decisions from maturity audit."),
    ("organizational_restructuring", "Never restructure organization from maturity audit."),
)

MAX_PLATFORM_MATURITY_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_PLATFORM_MATURITY_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G1 / FIX 354 — real evidence density & trust maturity program contract."""

from __future__ import annotations

from typing import Final

REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ID: Final[str] = "WORKSTREAM_G1"
REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_FIX: Final[str] = "FIX 354"
REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_real_evidence_density_trust_maturity_program_v1"
)
REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_real_evidence_density_trust_maturity_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "evidence_density_measures_confidence_without_trust_authority"
)

MUTATION_PERFORMED_FIX_354: Final[bool] = False
EXECUTION_PERFORMED_FIX_354: Final[bool] = False
TRUST_AUTHORITY_FIX_354: Final[bool] = False
TRUST_PROMOTION_FIX_354: Final[bool] = False
AUTOMATIC_EVIDENCE_ACCEPTANCE_FIX_354: Final[bool] = False
CUSTOMER_MANIPULATION_FIX_354: Final[bool] = False
PROVIDER_MUTATION_FIX_354: Final[bool] = False
GOVERNANCE_MUTATION_FIX_354: Final[bool] = False
AUTHORITY_EXPANSION_FIX_354: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_354: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_354: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_354: Final[bool] = False
LOCAL_EVIDENCE_MATURITY_EXECUTABLE_FIX_354: Final[bool] = True

REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_real_evidence_density_trust_maturity_program"
)

REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_INVARIANT: Final[str] = (
    "evidence_density_without_trust_authority_governance_mutation_or_automatic_evidence_acceptance"
)

REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PHASES: Final[tuple[str, ...]] = (
    "phase_1_evidence_registry_inventory",
    "phase_2_evidence_density_analysis",
    "phase_3_evidence_freshness_analysis",
    "phase_4_evidence_provenance_analysis",
    "phase_5_trust_maturity_analysis",
    "phase_6_evidence_gap_registry",
    "phase_7_evidence_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

EVIDENCE_CLASSIFICATION_LEVELS: Final[tuple[str, ...]] = (
    "synthetic",
    "derived",
    "operational",
    "independent",
)

EVIDENCE_DOMAINS: Final[tuple[str, ...]] = (
    "customer",
    "delivery",
    "provider",
    "operational",
    "trust",
    "audit",
    "fix_evidence",
)

EVIDENCE_MATURITY_METRICS: Final[tuple[str, ...]] = (
    "evidence_density_score",
    "evidence_freshness_score",
    "trust_maturity_score",
    "operational_proof_coverage",
    "customer_evidence_coverage",
    "provider_evidence_coverage",
    "audit_evidence_coverage",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 314",
    "FIX 315",
    "FIX 316",
    "FIX 330",
)

HUMAN_EVIDENCE_MATURITY_DECISION_KINDS: Final[tuple[str, ...]] = (
    "evidence_maturity_review_approve",
    "evidence_maturity_review_hold",
    "evidence_maturity_review_reject",
    "evidence_maturity_review_defer",
)

EVIDENCE_MATURITY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "evidence_maturity_note",
    "evidence_domain_entry",
    *HUMAN_EVIDENCE_MATURITY_DECISION_KINDS,
    "evidence_maturity_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_trust_promotion",
    "no_authority_expansion",
    "no_governance_mutation",
    "no_customer_manipulation",
    "no_provider_mutation",
    "no_automatic_evidence_acceptance",
)

FORBIDDEN_EVIDENCE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("trust_authority", "Never grant trust authority from evidence density validation."),
    ("trust_promotion", "Never promote trust states from evidence maturity program."),
    ("governance_mutation", "Never change governance from evidence density validation."),
    ("automatic_evidence_acceptance", "Never auto-accept evidence from density program."),
    ("authority_expansion", "Never expand authority from evidence maturity program."),
    ("customer_manipulation", "Never manipulate customers during evidence validation."),
    ("provider_mutation", "Never mutate providers from evidence maturity program."),
)

MAX_EVIDENCE_MATURITY_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_EVIDENCE_MATURITY_RECORDS: Final[int] = 500
STALE_EVIDENCE_DAYS: Final[int] = 90

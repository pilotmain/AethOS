# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — public product experience contract."""

from __future__ import annotations

from typing import Final

PUBLIC_PRODUCT_EXPERIENCE_SCHEMA_VERSION: Final[str] = "mission_control_public_product_experience_v1"
PUBLIC_PRODUCT_EXPERIENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_public_product_experience_record_v1"
)
PUBLIC_PRODUCT_EXPERIENCE_FIX: Final[str] = "FIX 311"

MUTATION_PERFORMED_FIX_311: Final[bool] = False
EXECUTION_PERFORMED_FIX_311: Final[bool] = False
PUBLIC_PRODUCT_AUTHORITY_FIX_311: Final[bool] = False
AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_311: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_311: Final[bool] = False
TENANT_MUTATION_AUTHORITY_FIX_311: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_311: Final[bool] = False
PUBLIC_PRODUCT_COMPOSES_EVIDENCE_ONLY_FIX_311: Final[bool] = True

PUBLIC_PRODUCT_EXPERIENCE_ROUTE_ID: Final[str] = "mission_control_public_product_experience"

PUBLIC_PRODUCT_EXPERIENCE_INVARIANT: Final[str] = (
    "public_product_experience_without_platform_authority"
)

PUBLIC_EXPERIENCE_DOMAINS: Final[tuple[str, ...]] = (
    "public_landing_experience",
    "capability_explorer",
    "trust_explorer",
    "guided_product_tour",
    "use_case_explorer",
    "customer_journey_explorer",
    "plan_entitlement_explorer",
    "public_readiness_explorer",
    "public_education_center",
    "public_product_dashboard",
)

HUMAN_PUBLIC_EXPERIENCE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "public_experience_review_decision_approve",
    "public_experience_review_decision_hold",
    "public_experience_review_decision_reject",
    "public_experience_review_decision_defer",
)

PUBLIC_PRODUCT_EXPERIENCE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "public_experience_note",
    *HUMAN_PUBLIC_EXPERIENCE_DECISION_KINDS,
    "public_product_experience_record",
)

PUBLIC_PRODUCT_EXPERIENCE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("experience_not_authority", "Public product experience ≠ platform authority."),
    ("explain_guide_onboard", "Public experiences may explain, guide, and onboard."),
    ("no_governance_bypass", "Public experiences may not bypass governance."),
    ("compose_only", "Composes FIX 295–310 evidence without provider execution."),
    ("trust_transparency", "Trust boundaries and evidence visible to new visitors."),
    ("discoverable_product", "Platform understandable without internal documentation."),
    ("human_review", "Public experience review records decisions without provisioning."),
    ("education_first", "FAQ and education center explain what AethOS can and cannot do."),
    ("journey_clarity", "Customer journey paths visible before beta onboarding."),
    ("readiness_honesty", "Public readiness explorer surfaces limitations honestly."),
)

FORBIDDEN_PUBLIC_EXPERIENCE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("provider_mutation", "Public experience never mutates providers."),
    ("governance_bypass", "Public experience never bypasses governance."),
    ("trust_mutation", "Public experience never mutates trust."),
    ("automatic_onboarding", "Public experience never auto-onboards customers."),
    ("customer_provisioning", "Public experience never provisions customers."),
    ("subscription_changes", "Public experience never changes subscriptions."),
    ("hidden_authority_paths", "Public experience never introduces hidden authority paths."),
)

PUBLIC_PRODUCT_EXPERIENCE_EXECUTABLE: Final[bool] = False

MAX_PUBLIC_PRODUCT_EXPERIENCE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PUBLIC_PRODUCT_EXPERIENCE_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G2 / FIX 355 — real usage density & platform adoption program contract."""

from __future__ import annotations

from typing import Final

REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ID: Final[str] = "WORKSTREAM_G2"
REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_FIX: Final[str] = "FIX 355"
REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_real_usage_density_platform_adoption_program_v1"
)
REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_real_usage_density_platform_adoption_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "usage_density_observes_behavior_without_user_authority"
)

MUTATION_PERFORMED_FIX_355: Final[bool] = False
EXECUTION_PERFORMED_FIX_355: Final[bool] = False
USER_AUTHORITY_FIX_355: Final[bool] = False
AUTOMATED_OUTREACH_FIX_355: Final[bool] = False
BEHAVIORAL_MANIPULATION_FIX_355: Final[bool] = False
PLAN_MUTATION_FIX_355: Final[bool] = False
TRUST_MUTATION_FIX_355: Final[bool] = False
AUTHORITY_EXPANSION_FIX_355: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_355: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_355: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_355: Final[bool] = False
LOCAL_USAGE_ADOPTION_EXECUTABLE_FIX_355: Final[bool] = True

REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_real_usage_density_platform_adoption_program"
)

REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_INVARIANT: Final[str] = (
    "usage_density_without_user_authority_outreach_automation_or_plan_mutation"
)

REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_usage_registry_inventory",
    "phase_2_active_usage_analysis",
    "phase_3_workflow_adoption_analysis",
    "phase_4_retained_usage_analysis",
    "phase_5_platform_dependence_analysis",
    "phase_6_adoption_friction_analysis",
    "phase_7_adoption_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

USAGE_MATURITY_LEVELS: Final[tuple[str, ...]] = (
    "observed",
    "active",
    "adopted",
    "dependent",
)

USAGE_SURFACES: Final[tuple[str, ...]] = (
    "mission_control",
    "et_pipeline",
    "provider",
    "governance",
    "dashboard",
)

USAGE_ADOPTION_METRICS: Final[tuple[str, ...]] = (
    "active_users",
    "retained_users",
    "recurring_workflows",
    "workflow_adoption_rate",
    "platform_dependence_score",
    "adoption_friction_score",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 318",
    "FIX 320",
    "FIX 321",
    "FIX 330",
)

HUMAN_PLATFORM_ADOPTION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "platform_adoption_review_approve",
    "platform_adoption_review_hold",
    "platform_adoption_review_reject",
    "platform_adoption_review_defer",
)

PLATFORM_ADOPTION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "platform_adoption_note",
    "usage_session_entry",
    *HUMAN_PLATFORM_ADOPTION_DECISION_KINDS,
    "platform_adoption_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_customer_targeting",
    "no_outreach_automation",
    "no_behavioral_manipulation",
    "no_authority_expansion",
    "no_plan_mutation",
    "no_trust_mutation",
)

FORBIDDEN_USAGE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("user_authority", "Never grant user authority from usage density validation."),
    ("automated_outreach", "Never automate outreach from adoption program."),
    ("behavioral_manipulation", "Never manipulate users during usage measurement."),
    ("plan_mutation", "Never alter plans from adoption validation."),
    ("trust_mutation", "Never mutate trust states from usage program."),
    ("authority_expansion", "Never expand authority from adoption validation."),
)

MAX_PLATFORM_ADOPTION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_PLATFORM_ADOPTION_RECORDS: Final[int] = 500

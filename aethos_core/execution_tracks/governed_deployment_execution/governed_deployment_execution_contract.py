# SPDX-License-Identifier: Apache-2.0
"""FIX 337 / EXECUTION_TRACK_4 — governed deployment execution contract."""

from __future__ import annotations

from typing import Final

EXECUTION_TRACK_4_ID: Final[str] = "EXECUTION_TRACK_4"
GOVERNED_DEPLOYMENT_EXECUTION_FIX: Final[str] = "FIX 337"
GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_deployment_execution_v1"
)
GOVERNED_DEPLOYMENT_EXECUTION_RECORD_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_deployment_execution_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "deployment_execution_runs_under_human_approval_rollback_and_trust_remain_separate"
)

MUTATION_PERFORMED_FIX_337: Final[bool] = False
EXECUTION_PERFORMED_FIX_337: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_337: Final[bool] = False
AUTONOMOUS_DEPLOYMENT_ENABLED_FIX_337: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_337: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_337: Final[bool] = False
PRODUCTION_PROMOTION_AUTHORITY_FIX_337: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_337: Final[bool] = False
LOCAL_DEPLOYMENT_EXECUTION_EXECUTABLE_FIX_337: Final[bool] = True

GOVERNED_DEPLOYMENT_EXECUTION_ROUTE_ID: Final[str] = "execution_track_governed_deployment_execution"

GOVERNED_DEPLOYMENT_EXECUTION_INVARIANT: Final[str] = (
    "governed_deployment_execution_without_rollback_or_trust_authority"
)

EXECUTION_TRACK_4_PHASES: Final[tuple[str, ...]] = (
    "phase_1_deployment_request_intake",
    "phase_2_deployment_planning",
    "phase_3_deployment_readiness",
    "phase_4_deployment_execution",
    "phase_5_post_deploy_verification",
    "phase_6_operational_evidence",
    "phase_7_failure_assessment",
    "phase_8_deployment_dashboard",
    "phase_9_human_review",
)

PHASE_1_PROVIDERS: Final[tuple[str, ...]] = ("Railway", "Vercel")
PHASE_2_PROVIDERS: Final[tuple[str, ...]] = ("AWS", "Kubernetes", "Azure", "GCP")

SUPPORTED_ENVIRONMENTS: Final[tuple[str, ...]] = ("staging", "preview", "production")

HUMAN_DEPLOYMENT_DECISION_KINDS: Final[tuple[str, ...]] = (
    "deployment_decision_approve",
    "deployment_decision_hold",
    "deployment_decision_reject",
    "deployment_decision_defer",
)

REQUIRED_DEPLOYMENT_REVIEW_KINDS: Final[tuple[str, ...]] = (
    "deployment_review_note",
    "deployment_readiness_review_note",
    "deployment_execution_review_note",
)

GOVERNED_DEPLOYMENT_EXECUTION_RECORD_KINDS: Final[tuple[str, ...]] = (
    *REQUIRED_DEPLOYMENT_REVIEW_KINDS,
    *HUMAN_DEPLOYMENT_DECISION_KINDS,
    "deployment_executed_note",
    "governed_deployment_execution_record",
)

GOVERNED_DEPLOYMENT_EXECUTION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("execution_not_authority", "Deployment execution ≠ deployment authority."),
    ("human_mandatory", "Human approval remains mandatory for all deployments."),
    ("trust_separate", "Trust progression remains separate from deployment execution."),
    ("rollback_separate", "Rollback remains separate from deployment execution."),
    ("bounded_providers", "Execution limited to supported Phase 1 providers."),
    ("evidence_first", "Deployment and verification receipts captured as evidence."),
    ("no_autonomous_deployment", "No autonomous or implicit deployment escalation."),
    ("no_production_promotion", "No automatic production promotion."),
    ("no_rollback", "No rollback execution from deployment execution layer."),
    ("no_trust_mutation", "No trust mutation from deployment execution layer."),
)

FORBIDDEN_DEPLOYMENT_EXECUTION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("rollback", "Never rollback from deployment execution layer."),
    ("trust_mutation", "Never mutate trust from deployment execution layer."),
    ("autonomous_deployment", "Never deploy without human deployment decision approve."),
    ("automatic_production_promotion", "Never promote to production automatically."),
    ("unsupported_provider_execution", "Never execute unsupported provider deployments."),
)

TRACK_NON_GOALS: Final[tuple[str, ...]] = (
    "no_rollback_execution",
    "no_trust_mutation",
    "no_autonomous_deployment",
    "no_automatic_production_promotion",
    "no_provider_expansion_beyond_supported",
)

MAX_GOVERNED_DEPLOYMENT_EXECUTION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_GOVERNED_DEPLOYMENT_EXECUTION_RECORDS: Final[int] = 500

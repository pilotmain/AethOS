# SPDX-License-Identifier: Apache-2.0
"""FIX 334 / EXECUTION_TRACK_1 — governed workspace creation and repository bootstrap contract."""

from __future__ import annotations

from typing import Final

EXECUTION_TRACK_1_ID: Final[str] = "EXECUTION_TRACK_1"
GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_FIX: Final[str] = "FIX 334"
GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_workspace_creation_repository_bootstrap_v1"
)
GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_RECORD_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_workspace_creation_repository_bootstrap_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "workspace_creation_prepares_repository_environments_deployment_and_trust_remain_separate"
)

MUTATION_PERFORMED_FIX_334: Final[bool] = False
EXECUTION_PERFORMED_FIX_334: Final[bool] = False
WORKSPACE_CREATION_AUTHORITY_FIX_334: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_334: Final[bool] = False
GIT_PUSH_AUTHORITY_FIX_334: Final[bool] = False
PR_CREATION_AUTHORITY_FIX_334: Final[bool] = False
CLOUD_PROVISIONING_AUTHORITY_FIX_334: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_334: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_334: Final[bool] = False
CODE_GENERATION_AUTHORITY_FIX_334: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_334: Final[bool] = False
LOCAL_BOOTSTRAP_EXECUTABLE_FIX_334: Final[bool] = True

GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_ROUTE_ID: Final[str] = (
    "execution_track_governed_workspace_creation_repository_bootstrap"
)

GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_INVARIANT: Final[str] = (
    "governed_workspace_creation_and_repository_bootstrap_without_deployment_authority"
)

EXECUTION_TRACK_1_PHASES: Final[tuple[str, ...]] = (
    "phase_1_workspace_registry",
    "phase_2_repository_bootstrap",
    "phase_3_project_template_registry",
    "phase_4_workspace_verification",
    "phase_5_bootstrap_evidence",
    "phase_6_workspace_dashboard",
)

PHASE_OUTPUTS: Final[tuple[str, ...]] = (
    "workspace_registry",
    "workspace_health_report",
    "workspace_evidence_registry",
    "repository_bootstrap_report",
    "project_template_registry",
    "template_readiness_report",
    "workspace_verification_report",
    "workspace_creation_evidence_bundle",
    "workspace_creation_dashboard",
)

SUPPORTED_REPOSITORY_TEMPLATES: Final[tuple[str, ...]] = (
    "spring_boot_service",
    "nextjs_web_app",
    "fastapi_service",
    "fullstack_reference",
    "generic_repository",
)

HUMAN_WORKSPACE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "workspace_decision_approve",
    "workspace_decision_hold",
    "workspace_decision_reject",
    "workspace_decision_defer",
)

GOVERNED_WORKSPACE_CREATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "workspace_creation_review_note",
    "workspace_bootstrap_review_note",
    *HUMAN_WORKSPACE_DECISION_KINDS,
    "workspace_bootstrap_executed_note",
    "governed_workspace_creation_record",
)

GOVERNED_WORKSPACE_CREATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("creation_not_deployment", "Workspace creation ≠ deployment authority."),
    ("preparation_allowed", "Repository preparation is allowed under human review."),
    ("trust_separate", "Trust progression remains separate from workspace bootstrap."),
    ("human_decisions", "Humans approve workspace creation and bootstrap execution."),
    ("bounded_bootstrap", "Bootstrap creates folders, base config, README, and governance metadata only."),
    ("no_code_generation", "No application code generation in EXECUTION_TRACK_1."),
    ("no_git_push", "No git push, PR creation, or remote repository mutation."),
    ("no_cloud", "No cloud provisioning or provider mutation."),
    ("verification_before_handoff", "Verification receipts required before handoff."),
    ("evidence_first", "Creation events, approvals, and verification captured as evidence."),
)

FORBIDDEN_WORKSPACE_CREATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("code_generation", "Never generate application implementation code."),
    ("pr_creation", "Never create pull requests from workspace bootstrap."),
    ("git_push", "Never push to remote repositories."),
    ("deployment", "Never deploy from workspace bootstrap."),
    ("cloud_provisioning", "Never provision cloud resources."),
    ("provider_mutation", "Never mutate providers from workspace bootstrap."),
    ("trust_mutation", "Never mutate trust from workspace bootstrap."),
    ("automatic_bootstrap", "Never bootstrap without human workspace decision approve."),
)

TRACK_NON_GOALS: Final[tuple[str, ...]] = (
    "no_code_generation",
    "no_pr_creation",
    "no_git_push",
    "no_deployment",
    "no_cloud_provisioning",
    "no_provider_mutation",
    "no_trust_mutation",
)

MAX_GOVERNED_WORKSPACE_CREATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_GOVERNED_WORKSPACE_CREATION_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 335 / EXECUTION_TRACK_2 — governed code generation and changeset creation contract."""

from __future__ import annotations

from typing import Final

EXECUTION_TRACK_2_ID: Final[str] = "EXECUTION_TRACK_2"
GOVERNED_CODE_GENERATION_CHANGESET_CREATION_FIX: Final[str] = "FIX 335"
GOVERNED_CODE_GENERATION_CHANGESET_CREATION_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_code_generation_changeset_creation_v1"
)
GOVERNED_CODE_GENERATION_CHANGESET_CREATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_code_generation_changeset_creation_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "code_generation_produces_reviewable_changes_repository_and_deployment_authority_remain_separate"
)

MUTATION_PERFORMED_FIX_335: Final[bool] = False
EXECUTION_PERFORMED_FIX_335: Final[bool] = False
REPOSITORY_AUTHORITY_FIX_335: Final[bool] = False
GIT_COMMIT_AUTHORITY_FIX_335: Final[bool] = False
GIT_PUSH_AUTHORITY_FIX_335: Final[bool] = False
PR_CREATION_AUTHORITY_FIX_335: Final[bool] = False
MERGE_AUTHORITY_FIX_335: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_335: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_335: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_335: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_335: Final[bool] = False
LOCAL_CODE_GENERATION_EXECUTABLE_FIX_335: Final[bool] = True

GOVERNED_CODE_GENERATION_CHANGESET_CREATION_ROUTE_ID: Final[str] = (
    "execution_track_governed_code_generation_changeset_creation"
)

GOVERNED_CODE_GENERATION_CHANGESET_CREATION_INVARIANT: Final[str] = (
    "governed_code_generation_and_changeset_creation_without_repository_authority"
)

EXECUTION_TRACK_2_PHASES: Final[tuple[str, ...]] = (
    "phase_1_requirement_intake",
    "phase_2_generation_planning",
    "phase_3_code_generation",
    "phase_4_test_generation",
    "phase_5_documentation_generation",
    "phase_6_changeset_assembly",
    "phase_7_verification",
    "phase_8_evidence",
    "phase_9_dashboard",
)

REQUIREMENT_TYPES: Final[tuple[str, ...]] = ("story", "task", "bug", "enhancement")

SUPPORTED_GENERATION_STACKS: Final[tuple[str, ...]] = (
    "java_spring_boot",
    "python_fastapi",
    "nextjs",
    "typescript",
    "infrastructure_configuration",
)

HUMAN_GENERATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "generation_decision_approve",
    "generation_decision_hold",
    "generation_decision_reject",
    "generation_decision_defer",
)

GOVERNED_CODE_GENERATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "generation_request_review_note",
    "generate_code_review_note",
    *HUMAN_GENERATION_DECISION_KINDS,
    "code_generation_executed_note",
    "governed_code_generation_record",
)

GOVERNED_CODE_GENERATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("generation_not_authority", "Code generation ≠ repository authority."),
    ("advisory_until_reviewed", "Generated code is advisory until human review."),
    ("bounded_workspace", "Changes apply only inside approved EXECUTION_TRACK_1 workspaces."),
    ("human_decisions", "Humans approve generation scope and execution."),
    ("reviewable_changes", "All generated files, tests, and docs are reviewable."),
    ("no_git_commit", "No git commits from code generation layer."),
    ("no_git_push", "No git push or remote repository mutation."),
    ("no_pr_creation", "No PR creation or merge from code generation layer."),
    ("no_deployment", "No deployment or cloud execution."),
    ("evidence_first", "Prompts, generation events, and verification captured as evidence."),
)

FORBIDDEN_CODE_GENERATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("git_commit", "Never commit from code generation layer."),
    ("git_push", "Never push from code generation layer."),
    ("pr_creation", "Never create pull requests from code generation layer."),
    ("merge", "Never merge from code generation layer."),
    ("deployment", "Never deploy from code generation layer."),
    ("provider_mutation", "Never mutate providers from code generation layer."),
    ("trust_mutation", "Never mutate trust from code generation layer."),
    ("automatic_generation", "Never generate without human generation decision approve."),
)

TRACK_NON_GOALS: Final[tuple[str, ...]] = (
    "no_git_commits",
    "no_git_push",
    "no_pr_creation",
    "no_merge",
    "no_deployment",
    "no_provider_mutation",
    "no_trust_mutation",
)

MAX_GOVERNED_CODE_GENERATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_GOVERNED_CODE_GENERATION_RECORDS: Final[int] = 500

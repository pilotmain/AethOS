# SPDX-License-Identifier: Apache-2.0
"""FIX 336 / EXECUTION_TRACK_3 — governed Git delivery contract."""

from __future__ import annotations

from typing import Final

EXECUTION_TRACK_3_ID: Final[str] = "EXECUTION_TRACK_3"
GOVERNED_GIT_DELIVERY_FIX: Final[str] = "FIX 336"
GOVERNED_GIT_DELIVERY_SCHEMA_VERSION: Final[str] = "execution_track_governed_git_delivery_v1"
GOVERNED_GIT_DELIVERY_RECORD_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_git_delivery_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "git_delivery_performs_bounded_repository_operations_merge_and_deployment_remain_separate"
)

MUTATION_PERFORMED_FIX_336: Final[bool] = False
EXECUTION_PERFORMED_FIX_336: Final[bool] = False
GIT_DELIVERY_AUTHORITY_FIX_336: Final[bool] = False
MERGE_AUTHORITY_FIX_336: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_336: Final[bool] = False
CLOUD_PROVISIONING_AUTHORITY_FIX_336: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_336: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_336: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_336: Final[bool] = False
LOCAL_GIT_DELIVERY_EXECUTABLE_FIX_336: Final[bool] = True

GOVERNED_GIT_DELIVERY_ROUTE_ID: Final[str] = "execution_track_governed_git_delivery"

GOVERNED_GIT_DELIVERY_INVARIANT: Final[str] = (
    "governed_git_delivery_without_merge_or_deployment_authority"
)

EXECUTION_TRACK_3_PHASES: Final[tuple[str, ...]] = (
    "phase_1_delivery_request_intake",
    "phase_2_branch_planning",
    "phase_3_commit_assembly",
    "phase_4_commit_creation",
    "phase_5_push_delivery",
    "phase_6_pull_request_creation",
    "phase_7_delivery_verification",
    "phase_8_evidence_collection",
    "phase_9_delivery_dashboard",
)

DELIVERY_BRANCH_PREFIX: Final[str] = "aethos"

HUMAN_GIT_DELIVERY_DECISION_KINDS: Final[tuple[str, ...]] = (
    "git_delivery_decision_approve",
    "git_delivery_decision_hold",
    "git_delivery_decision_reject",
    "git_delivery_decision_defer",
)

REQUIRED_DELIVERY_REVIEW_KINDS: Final[tuple[str, ...]] = (
    "git_delivery_review_note",
    "branch_delivery_review_note",
    "commit_delivery_review_note",
    "pull_request_review_note",
)

GOVERNED_GIT_DELIVERY_RECORD_KINDS: Final[tuple[str, ...]] = (
    *REQUIRED_DELIVERY_REVIEW_KINDS,
    *HUMAN_GIT_DELIVERY_DECISION_KINDS,
    "git_delivery_executed_note",
    "governed_git_delivery_record",
)

GOVERNED_GIT_DELIVERY_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("delivery_not_merge", "Git delivery ≠ merge authority."),
    ("delivery_not_deployment", "Git delivery ≠ deployment authority."),
    ("trust_separate", "Trust progression remains separate from Git delivery."),
    ("human_gates", "Humans approve branch, commit, push, and PR stages."),
    ("bounded_delivery", "Delivery operates on approved workspace changesets only."),
    ("evidence_first", "Branch, commit, push, and PR receipts captured as evidence."),
    ("no_merge", "No merge execution from Git delivery layer."),
    ("no_deployment", "No deployment or cloud provisioning."),
    ("no_rollback", "No rollback execution from Git delivery layer."),
    ("no_implicit_approval", "No automatic escalation or implicit approvals."),
)

FORBIDDEN_GIT_DELIVERY_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("merge", "Never merge from Git delivery layer."),
    ("deployment", "Never deploy from Git delivery layer."),
    ("rollback", "Never rollback from Git delivery layer."),
    ("cloud_provisioning", "Never provision cloud resources."),
    ("trust_mutation", "Never mutate trust from Git delivery layer."),
    ("automatic_delivery", "Never deliver without human git delivery decision approve."),
)

TRACK_NON_GOALS: Final[tuple[str, ...]] = (
    "no_merge_execution",
    "no_deployment",
    "no_cloud_provisioning",
    "no_rollback",
    "no_trust_mutation",
)

MAX_GOVERNED_GIT_DELIVERY_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_GOVERNED_GIT_DELIVERY_RECORDS: Final[int] = 500

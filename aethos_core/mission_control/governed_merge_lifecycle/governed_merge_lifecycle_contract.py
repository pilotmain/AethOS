# SPDX-License-Identifier: Apache-2.0
"""FIX 200 — governed merge lifecycle contract."""

from __future__ import annotations

from typing import Final

GOVERNED_MERGE_LIFECYCLE_SCHEMA_VERSION: Final[str] = "mission_control_governed_merge_lifecycle_v1"
GOVERNED_MERGE_LIFECYCLE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_merge_lifecycle_record_v1"
)
GOVERNED_MERGE_LIFECYCLE_HANDOFF_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_merge_lifecycle_handoff_v1"
)
GOVERNED_MERGE_LIFECYCLE_FIX: Final[str] = "FIX 200"

MUTATION_PERFORMED_FIX_200: Final[bool] = False
EXECUTION_PERFORMED_FIX_200: Final[bool] = False
MERGE_EXECUTION_PERFORMED_FIX_200: Final[bool] = False
MERGE_AUTHORITY_FIX_200: Final[bool] = False
AUTONOMOUS_MERGE_ENABLED_FIX_200: Final[bool] = False
APPROVAL_BYPASS_ENABLED_FIX_200: Final[bool] = False
HIDDEN_MERGE_PATH_ENABLED_FIX_200: Final[bool] = False
DEPLOY_AUTHORITY_FIX_200: Final[bool] = False
RAILWAY_AUTHORITY_FIX_200: Final[bool] = False
PROVIDER_AUTHORITY_FIX_200: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_200: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_200: Final[bool] = False
MERGE_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_200: Final[bool] = True
GOVERNED_MERGE_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_200: Final[bool] = True

GOVERNED_MERGE_LIFECYCLE_ROUTE_ID: Final[str] = "mission_control_governed_merge_lifecycle"
GOVERNED_MERGE_LIFECYCLE_ORIGIN: Final[str] = "mission_control_governed_merge_lifecycle"

GOVERNED_MERGE_LIFECYCLE_INVARIANT: Final[str] = (
    "governed_merge_lifecycle_prepares_review_and_handoff_without_autonomous_merge_or_authority_bypass"
)

MERGE_RECOMMENDATIONS: Final[tuple[str, ...]] = (
    "APPROVE_FOR_REVIEW",
    "CONDITIONAL_APPROVAL",
    "HOLD",
    "REJECT",
)

MERGE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "merge_decision_approve",
    "merge_decision_hold",
    "merge_decision_reject",
)

MERGE_LIFECYCLE_STAGES: Final[tuple[str, ...]] = (
    "pr_open",
    "merge_review",
    "merge_decision",
    "merge_handoff",
    "merge_execution_request",
    "post_merge_audit",
)

REQUIRED_MERGE_EVIDENCE_IDS: Final[tuple[str, ...]] = (
    "issue_reference",
    "plan_reference",
    "verification_evidence",
    "diff_audit_evidence",
    "risk_assessment",
    "human_approval_record",
)

GOVERNED_MERGE_LIFECYCLE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "merge_review_observation",
    "merge_decision_approve",
    "merge_decision_hold",
    "merge_decision_reject",
    "merge_rationale_note",
    "merge_handoff_note",
    "merge_execution_request_note",
    "governed_merge_lifecycle_record",
)

GOVERNED_MERGE_LIFECYCLE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("merge_not_autonomous", "merge_authority ≠ autonomous_merge."),
    ("human_authorizes", "Humans authorize merge; frozen gates decide."),
    ("aethos_prepares", "AethOS prepares review packets and handoff artifacts."),
    ("evidence_required", "No evidence → no merge recommendation."),
    ("compose_delivery_pipeline", "Composes PR open, verification, alignment, and agent receipts."),
    ("recommendation_only", "Merge recommendation is advisory — not merge authority."),
    ("handoff_not_execution", "Handoff artifacts prepare execution requests — AethOS does not merge."),
    ("no_deploy_railway", "Merge lifecycle excludes deploy, Railway, and production mutation."),
)

FORBIDDEN_MERGE_LIFECYCLE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_merge", "Never merge pull requests autonomously."),
    ("hidden_merge_path", "Never use hidden merge execution paths."),
    ("approval_bypass", "Never bypass human merge approval."),
    ("deploy", "Merge lifecycle never deploys."),
    ("railway_mutation", "Merge lifecycle never mutates Railway."),
    ("production_mutation", "Merge lifecycle never mutates production."),
    ("provider_mutation_outside_merge", "Never mutate providers outside scoped handoff preparation."),
    ("gate_bypass", "Never bypass frozen governance gates."),
)

GOVERNED_MERGE_LIFECYCLE_EXECUTABLE: Final[bool] = False
GOVERNED_MERGE_HANDOFF_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_MERGE_LIFECYCLE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GOVERNED_MERGE_LIFECYCLE_RECORDS: Final[int] = 500

SUPPORTED_MERGE_ADAPTERS: Final[tuple[str, ...]] = ("github_pull_request",)

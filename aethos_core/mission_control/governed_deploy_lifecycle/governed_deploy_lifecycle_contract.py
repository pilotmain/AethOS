# SPDX-License-Identifier: Apache-2.0
"""FIX 210 — governed deploy lifecycle contract."""

from __future__ import annotations

from typing import Final

GOVERNED_DEPLOY_LIFECYCLE_SCHEMA_VERSION: Final[str] = "mission_control_governed_deploy_lifecycle_v1"
GOVERNED_DEPLOY_LIFECYCLE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_deploy_lifecycle_record_v1"
)
GOVERNED_DEPLOY_LIFECYCLE_HANDOFF_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_deploy_lifecycle_handoff_v1"
)
GOVERNED_DEPLOY_LIFECYCLE_FIX: Final[str] = "FIX 210"

MUTATION_PERFORMED_FIX_210: Final[bool] = False
EXECUTION_PERFORMED_FIX_210: Final[bool] = False
WORKFLOW_EXECUTION_PERFORMED_FIX_210: Final[bool] = False
DEPLOY_AUTHORITY_FIX_210: Final[bool] = False
AUTONOMOUS_DEPLOY_ENABLED_FIX_210: Final[bool] = False
APPROVAL_BYPASS_ENABLED_FIX_210: Final[bool] = False
HIDDEN_WORKFLOW_EXECUTION_ENABLED_FIX_210: Final[bool] = False
MERGE_AUTHORITY_FIX_210: Final[bool] = False
RAILWAY_AUTHORITY_FIX_210: Final[bool] = False
VERCEL_AUTHORITY_FIX_210: Final[bool] = False
AWS_AUTHORITY_FIX_210: Final[bool] = False
KUBERNETES_AUTHORITY_FIX_210: Final[bool] = False
PROVIDER_AUTHORITY_FIX_210: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_210: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_210: Final[bool] = False
DEPLOY_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_210: Final[bool] = True
GOVERNED_DEPLOY_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_210: Final[bool] = True

GOVERNED_DEPLOY_LIFECYCLE_ROUTE_ID: Final[str] = "mission_control_governed_deploy_lifecycle"
GOVERNED_DEPLOY_LIFECYCLE_ORIGIN: Final[str] = "mission_control_governed_deploy_lifecycle"

GOVERNED_DEPLOY_LIFECYCLE_INVARIANT: Final[str] = (
    "governed_deploy_lifecycle_prepares_github_actions_handoff_without_autonomous_deploy_or_provider_mutation"
)

DEPLOY_RECOMMENDATIONS: Final[tuple[str, ...]] = (
    "APPROVE_FOR_DEPLOY_REVIEW",
    "CONDITIONAL_DEPLOY_APPROVAL",
    "HOLD_DEPLOY",
    "REJECT_DEPLOY",
)

DEPLOY_DECISION_KINDS: Final[tuple[str, ...]] = (
    "deploy_decision_approve",
    "deploy_decision_hold",
    "deploy_decision_reject",
)

PHASE_1_DEPLOY_ENVIRONMENTS: Final[tuple[str, ...]] = ("development", "staging")

DEPLOY_LIFECYCLE_STAGES: Final[tuple[str, ...]] = (
    "merge_complete",
    "deploy_readiness",
    "deploy_review",
    "deploy_decision",
    "deploy_handoff",
    "deploy_execution_request",
    "post_deploy_audit",
)

REQUIRED_DEPLOY_EVIDENCE_IDS: Final[tuple[str, ...]] = (
    "issue_reference",
    "merge_evidence",
    "verification_evidence",
    "risk_assessment",
    "blast_radius_summary",
    "rollback_reference",
    "human_approval_record",
)

GITHUB_ACTIONS_WORKFLOW_TARGETS: Final[tuple[str, ...]] = (
    "deploy.yml",
    "release.yml",
    "production-deploy.yml",
)

GOVERNED_DEPLOY_LIFECYCLE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "deploy_review_observation",
    "deploy_decision_approve",
    "deploy_decision_hold",
    "deploy_decision_reject",
    "deploy_rationale_note",
    "deploy_handoff_note",
    "deploy_execution_request_note",
    "merge_completed_acknowledgment",
    "governed_deploy_lifecycle_record",
)

GOVERNED_DEPLOY_LIFECYCLE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("deploy_not_autonomous", "deploy_authority ≠ autonomous_deploy."),
    ("human_authorizes", "Humans authorize deploy; deployment systems execute."),
    ("aethos_prepares", "AethOS prepares deploy review packets and handoff artifacts."),
    ("github_actions_phase_1", "Phase 1 supports GitHub Actions workflow dispatch only."),
    ("no_railway_vercel_aws", "No Railway, Vercel, AWS, or Kubernetes in phase 1."),
    ("evidence_required", "No evidence → no deploy recommendation."),
    ("compose_merge_and_delivery", "Composes FIX 200 merge evidence and software delivery verification."),
    ("recommendation_only", "Deploy recommendation is advisory — not deploy authority."),
    ("handoff_not_execution", "Handoff artifacts prepare workflow dispatch — AethOS does not deploy."),
    ("staging_before_production", "Production deploy deferred until staging evidence exists."),
)

FORBIDDEN_DEPLOY_LIFECYCLE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_deploy", "Never deploy autonomously."),
    ("railway_deploy", "Never deploy via Railway in FIX 210."),
    ("vercel_deploy", "Never deploy via Vercel in FIX 210."),
    ("aws_deploy", "Never deploy via AWS in FIX 210."),
    ("kubernetes_deploy", "Never deploy via Kubernetes in FIX 210."),
    ("hidden_workflow_execution", "Never use hidden workflow execution paths."),
    ("approval_bypass", "Never bypass human deploy approval."),
    ("production_mutation", "Production deploy blocked in phase 1."),
    ("environment_mutation", "Never mutate environments outside handoff preparation."),
    ("gate_bypass", "Never bypass frozen governance gates."),
)

GOVERNED_DEPLOY_LIFECYCLE_EXECUTABLE: Final[bool] = False
GOVERNED_DEPLOY_HANDOFF_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_DEPLOY_LIFECYCLE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GOVERNED_DEPLOY_LIFECYCLE_RECORDS: Final[int] = 500

SUPPORTED_DEPLOY_ADAPTERS: Final[tuple[str, ...]] = ("github_actions_workflow_dispatch",)

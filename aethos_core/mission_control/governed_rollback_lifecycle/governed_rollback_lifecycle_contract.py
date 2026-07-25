# SPDX-License-Identifier: Apache-2.0
"""FIX 230 — governed rollback lifecycle contract."""

from __future__ import annotations

from typing import Final

GOVERNED_ROLLBACK_LIFECYCLE_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_rollback_lifecycle_v1"
)
GOVERNED_ROLLBACK_LIFECYCLE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_rollback_lifecycle_record_v1"
)
GOVERNED_ROLLBACK_LIFECYCLE_HANDOFF_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_rollback_lifecycle_handoff_v1"
)
GOVERNED_ROLLBACK_LIFECYCLE_FIX: Final[str] = "FIX 230"

MUTATION_PERFORMED_FIX_230: Final[bool] = False
EXECUTION_PERFORMED_FIX_230: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_230: Final[bool] = False
AUTONOMOUS_ROLLBACK_ENABLED_FIX_230: Final[bool] = False
WORKFLOW_EXECUTION_PERFORMED_FIX_230: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_230: Final[bool] = False
DATABASE_MUTATION_AUTHORITY_FIX_230: Final[bool] = False
HIDDEN_RECOVERY_PATH_ENABLED_FIX_230: Final[bool] = False
MONITORING_AUTHORITY_FIX_230: Final[bool] = False
DEPLOY_AUTHORITY_FIX_230: Final[bool] = False
MERGE_AUTHORITY_FIX_230: Final[bool] = False
RAILWAY_AUTHORITY_FIX_230: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_230: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_230: Final[bool] = False
GOVERNED_ROLLBACK_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_230: Final[bool] = True

GOVERNED_ROLLBACK_LIFECYCLE_ROUTE_ID: Final[str] = "mission_control_governed_rollback_lifecycle"
GOVERNED_ROLLBACK_LIFECYCLE_ORIGIN: Final[str] = "mission_control_governed_rollback_lifecycle"

GOVERNED_ROLLBACK_LIFECYCLE_INVARIANT: Final[str] = (
    "governed_rollback_lifecycle_assesses_recovery_and_prepares_handoff_without_autonomous_rollback"
)

ROLLBACK_RECOMMENDATIONS: Final[tuple[str, ...]] = (
    "CONTINUE_MONITORING",
    "INVESTIGATE",
    "PREPARE_ROLLBACK",
    "RECOMMEND_ROLLBACK",
)

ROLLBACK_DECISION_KINDS: Final[tuple[str, ...]] = (
    "rollback_decision_approve",
    "rollback_decision_hold",
    "rollback_decision_reject",
)

ROLLBACK_LIFECYCLE_STAGES: Final[tuple[str, ...]] = (
    "incident_observed",
    "rollback_assessment",
    "rollback_candidate_identification",
    "rollback_risk_analysis",
    "rollback_review",
    "rollback_decision",
    "rollback_handoff",
    "human_rollback_execution",
)

REQUIRED_ROLLBACK_EVIDENCE_IDS: Final[tuple[str, ...]] = (
    "deployment_reference",
    "monitoring_evidence",
    "incident_assessment",
    "risk_assessment",
    "rollback_target",
    "human_decision_record",
)

GITHUB_ACTIONS_ROLLBACK_WORKFLOW_TARGETS: Final[tuple[str, ...]] = (
    "rollback.yml",
    "restore-release.yml",
)

SUPPORTED_ROLLBACK_ADAPTERS: Final[tuple[str, ...]] = (
    "github_actions_rollback_workflow",
)

GOVERNED_ROLLBACK_LIFECYCLE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "rollback_assessment_note",
    "rollback_candidate_note",
    "rollback_risk_note",
    "rollback_decision_approve",
    "rollback_decision_hold",
    "rollback_decision_reject",
    "operator_rollback_review_note",
    "rollback_handoff_note",
    "governed_rollback_lifecycle_record",
)

GOVERNED_ROLLBACK_LIFECYCLE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("rollback_not_autonomous", "rollback_authority ≠ autonomous_rollback."),
    ("aethos_assesses", "AethOS assesses and recommends — humans decide."),
    ("recovery_systems_execute", "Recovery systems execute — AethOS never performs rollbacks."),
    ("compose_monitoring_and_deploy", "Composes FIX 220 monitoring and FIX 210 deploy evidence."),
    ("evidence_required", "No evidence → no rollback recommendation."),
    ("handoff_not_execution", "Handoff artifacts prepare workflow templates — never executed by AethOS."),
    ("no_provider_mutation", "No Railway, AWS, Kubernetes, database, or provider mutation."),
    ("no_hidden_recovery", "No hidden recovery paths."),
    ("recommendation_only", "Rollback recommendation is advisory — not rollback authority."),
    ("human_rollback_execution", "Human rollback execution remains outside AethOS authority."),
)

FORBIDDEN_ROLLBACK_LIFECYCLE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_rollback", "Never perform autonomous rollback."),
    ("workflow_execution", "Never dispatch rollback workflows from AethOS."),
    ("redeploy_execution", "Never redeploy from rollback layer."),
    ("provider_mutation", "Never mutate providers from rollback layer."),
    ("database_mutation", "Never mutate databases from rollback layer."),
    ("railway_mutation", "Never mutate Railway from rollback layer."),
    ("aws_mutation", "Never mutate AWS from rollback layer."),
    ("kubernetes_mutation", "Never mutate Kubernetes from rollback layer."),
    ("environment_mutation", "Never mutate environments from rollback layer."),
    ("hidden_recovery_path", "Never use hidden recovery execution paths."),
)

GOVERNED_ROLLBACK_LIFECYCLE_EXECUTABLE: Final[bool] = False
GOVERNED_ROLLBACK_HANDOFF_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_ROLLBACK_LIFECYCLE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GOVERNED_ROLLBACK_LIFECYCLE_RECORDS: Final[int] = 500

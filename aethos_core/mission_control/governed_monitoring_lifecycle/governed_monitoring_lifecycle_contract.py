# SPDX-License-Identifier: Apache-2.0
"""FIX 220 — governed monitoring lifecycle contract."""

from __future__ import annotations

from typing import Final

GOVERNED_MONITORING_LIFECYCLE_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_monitoring_lifecycle_v1"
)
GOVERNED_MONITORING_LIFECYCLE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_monitoring_lifecycle_record_v1"
)
GOVERNED_MONITORING_LIFECYCLE_ESCALATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_monitoring_lifecycle_escalation_v1"
)
GOVERNED_MONITORING_LIFECYCLE_FIX: Final[str] = "FIX 220"

MUTATION_PERFORMED_FIX_220: Final[bool] = False
EXECUTION_PERFORMED_FIX_220: Final[bool] = False
OBSERVATION_PERFORMED_FIX_220: Final[bool] = False
MONITORING_AUTHORITY_FIX_220: Final[bool] = False
INCIDENT_RESPONSE_AUTHORITY_FIX_220: Final[bool] = False
AUTONOMOUS_REMEDIATION_ENABLED_FIX_220: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_220: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_220: Final[bool] = False
WORKFLOW_EXECUTION_AUTHORITY_FIX_220: Final[bool] = False
DEPLOY_AUTHORITY_FIX_220: Final[bool] = False
MERGE_AUTHORITY_FIX_220: Final[bool] = False
RAILWAY_AUTHORITY_FIX_220: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_220: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_220: Final[bool] = False
MONITORING_COMPOSES_EVIDENCE_ONLY_FIX_220: Final[bool] = True
GOVERNED_MONITORING_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_220: Final[bool] = True

GOVERNED_MONITORING_LIFECYCLE_ROUTE_ID: Final[str] = "mission_control_governed_monitoring_lifecycle"
GOVERNED_MONITORING_LIFECYCLE_ORIGIN: Final[str] = "mission_control_governed_monitoring_lifecycle"

GOVERNED_MONITORING_LIFECYCLE_INVARIANT: Final[str] = (
    "governed_monitoring_lifecycle_observes_deployments_and_builds_incident_packets_without_operational_authority"
)

INCIDENT_CLASSIFICATIONS: Final[tuple[str, ...]] = (
    "HEALTHY",
    "WARNING",
    "DEGRADED",
    "INCIDENT",
    "UNKNOWN",
)

MONITORING_RECOMMENDATIONS: Final[tuple[str, ...]] = (
    "CONTINUE_OBSERVATION",
    "REVIEW_REQUIRED",
    "INVESTIGATE",
    "ESCALATE",
)

OPERATIONAL_DECISION_KINDS: Final[tuple[str, ...]] = (
    "operational_decision_continue",
    "operational_decision_investigate",
    "operational_decision_escalate",
    "operational_decision_ignore",
)

MONITORING_LIFECYCLE_STAGES: Final[tuple[str, ...]] = (
    "deploy_complete",
    "monitoring_observation",
    "health_assessment",
    "incident_detection",
    "operational_decision",
    "incident_escalation",
    "post_incident_review",
)

REQUIRED_MONITORING_EVIDENCE_IDS: Final[tuple[str, ...]] = (
    "deployment_reference",
    "verification_evidence",
    "workflow_evidence",
    "operational_timeline",
    "risk_summary",
    "operator_review_record",
)

MONITORING_SOURCES_PHASE_1: Final[tuple[str, ...]] = (
    "github_actions_workflow_results",
    "mission_control_evidence",
    "software_delivery_audits",
    "verification_history",
    "deployment_handoff_records",
)

GOVERNED_MONITORING_LIFECYCLE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "monitoring_observation",
    "workflow_result_note",
    "health_assessment_note",
    "incident_signal_note",
    "operational_decision_continue",
    "operational_decision_investigate",
    "operational_decision_escalate",
    "operational_decision_ignore",
    "operator_review_note",
    "governed_monitoring_lifecycle_record",
)

GOVERNED_MONITORING_LIFECYCLE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("monitoring_not_operational_authority", "monitoring_authority ≠ operational_authority."),
    ("aethos_observes", "AethOS observes — humans decide."),
    ("systems_source_of_truth", "Deployment systems remain the source of operational truth."),
    ("observation_only_phase_1", "Phase 1 observes GitHub Actions and Mission Control evidence only."),
    ("no_provider_mutation", "No Railway, AWS, Kubernetes, or provider mutation."),
    ("evidence_required", "No evidence → no monitoring recommendation."),
    ("compose_deploy_and_delivery", "Composes FIX 210 deploy handoff and software delivery verification."),
    ("recommendation_only", "Monitoring recommendation is advisory — not incident response authority."),
    ("escalation_not_remediation", "Escalation artifacts prepare human review — no autonomous remediation."),
    ("observe_before_respond", "Know what happened after deploy before changing anything in response."),
)

FORBIDDEN_MONITORING_LIFECYCLE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("rollback_execution", "Never execute rollbacks from monitoring layer."),
    ("redeploy_execution", "Never redeploy from monitoring layer."),
    ("provider_mutation", "Never mutate providers from monitoring layer."),
    ("environment_mutation", "Never mutate environments from monitoring layer."),
    ("workflow_execution", "Never dispatch workflows from monitoring layer."),
    ("infrastructure_modification", "Never modify infrastructure from monitoring layer."),
    ("autonomous_remediation", "Never perform autonomous remediation."),
    ("hidden_operational_path", "Never use hidden operational execution paths."),
    ("approval_bypass", "Never bypass human operational decisions."),
    ("gate_bypass", "Never bypass frozen governance gates."),
)

GOVERNED_MONITORING_LIFECYCLE_EXECUTABLE: Final[bool] = False
GOVERNED_MONITORING_ESCALATION_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_MONITORING_LIFECYCLE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GOVERNED_MONITORING_LIFECYCLE_RECORDS: Final[int] = 500

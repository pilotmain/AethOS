# SPDX-License-Identifier: Apache-2.0
"""FIX 220 — governed monitoring lifecycle service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_220_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
    deploy_target_environment,
    list_governed_deploy_lifecycle_records,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_contract import (
    AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
    DEPLOY_AUTHORITY_FIX_220,
    EXECUTION_PERFORMED_FIX_220,
    FORBIDDEN_MONITORING_LIFECYCLE_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_220,
    GOVERNANCE_MUTATION_PERFORMED_FIX_220,
    GOVERNED_MONITORING_ESCALATION_EXECUTABLE,
    GOVERNED_MONITORING_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_220,
    GOVERNED_MONITORING_LIFECYCLE_ESCALATION_SCHEMA_VERSION,
    GOVERNED_MONITORING_LIFECYCLE_FIX,
    GOVERNED_MONITORING_LIFECYCLE_INVARIANT,
    GOVERNED_MONITORING_LIFECYCLE_PRINCIPLES,
    GOVERNED_MONITORING_LIFECYCLE_SCHEMA_VERSION,
    INCIDENT_CLASSIFICATIONS,
    INCIDENT_RESPONSE_AUTHORITY_FIX_220,
    MERGE_AUTHORITY_FIX_220,
    MONITORING_AUTHORITY_FIX_220,
    MONITORING_LIFECYCLE_STAGES,
    MONITORING_RECOMMENDATIONS,
    MONITORING_SOURCES_PHASE_1,
    MUTATION_PERFORMED_FIX_220,
    OBSERVATION_PERFORMED_FIX_220,
    OPERATIONAL_DECISION_KINDS,
    PROVIDER_MUTATION_AUTHORITY_FIX_220,
    RAILWAY_AUTHORITY_FIX_220,
    REQUIRED_MONITORING_EVIDENCE_IDS,
    ROLLBACK_AUTHORITY_FIX_220,
    WORKFLOW_EXECUTION_AUTHORITY_FIX_220,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_store import (
    list_governed_monitoring_lifecycle_records,
    operational_decision_status,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import replay_link_key, timeline_link_ref
from aethos_core.software_delivery.github_pr_open_store import load_github_pr_open_for_plan
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.workspace_verification_store import (
    load_workspace_verification_for_plan,
    workspace_verification_passed,
)


@dataclass(frozen=True)
class GovernedMonitoringLifecycleResult:
    ok: bool
    session_id: str
    governed_monitoring_lifecycle: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class GovernedMonitoringEscalationResult:
    ok: bool
    session_id: str
    incident_escalation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _workflow_evidence(*, session_id: str, plan_id: str) -> dict[str, Any]:
    deploy_records = list_governed_deploy_lifecycle_records(session_id=session_id, plan_id=plan_id)
    monitoring_records = list_governed_monitoring_lifecycle_records(session_id=session_id, plan_id=plan_id)

    workflow_records = [
        r
        for r in deploy_records + monitoring_records
        if str(r.get("kind") or "")
        in {"deploy_execution_request_note", "deploy_handoff_note", "workflow_result_note"}
    ]
    latest = workflow_records[-1] if workflow_records else None
    meta = dict((latest or {}).get("metadata") or {})
    status = str(meta.get("workflow_status") or meta.get("deployment_status") or "unknown").lower()

    return {
        "workflow_record_count": len(workflow_records),
        "latest_record_id": (latest or {}).get("record_id"),
        "workflow_status": status,
        "workflow_run_id": meta.get("workflow_run_id"),
        "workflow_run_url": meta.get("workflow_run_url"),
        "deployment_success": status == "success",
        "present": bool(workflow_records),
        "read_only": True,
    }


def _deployment_reference(*, plan: dict[str, Any] | None, plan_id: str, session_id: str) -> dict[str, Any]:
    env = deploy_target_environment(session_id=session_id, plan_id=plan_id)
    deploy_records = list_governed_deploy_lifecycle_records(session_id=session_id, plan_id=plan_id)
    handoff_notes = [r for r in deploy_records if str(r.get("kind") or "") == "deploy_handoff_note"]
    execution_notes = [
        r for r in deploy_records if str(r.get("kind") or "") == "deploy_execution_request_note"
    ]
    return {
        "deployment_id": f"deploy-{plan_id}",
        "plan_id": plan_id,
        "issue_reference": (plan or {}).get("issue_reference"),
        "environment": env,
        "handoff_record_count": len(handoff_notes),
        "execution_request_count": len(execution_notes),
        "present": bool(handoff_notes or execution_notes or env),
        "read_only": True,
    }


def _operational_timeline(
    *,
    session_id: str,
    plan_id: str,
    plan: dict[str, Any] | None,
    workflow: dict[str, Any],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if plan:
        events.append(
            {
                "event_id": "issue-plan",
                "stage": "plan",
                "label": str(plan.get("issue_reference") or plan_id),
                "read_only": True,
            }
        )
    if workspace_verification_passed(plan_id=plan_id):
        events.append({"event_id": "verification", "stage": "verify", "label": "passed", "read_only": True})

    for record in list_governed_deploy_lifecycle_records(session_id=session_id, plan_id=plan_id):
        events.append(
            {
                "event_id": str(record.get("record_id") or ""),
                "stage": "deploy",
                "kind": record.get("kind"),
                "recorded_at": record.get("recorded_at"),
                "read_only": True,
            }
        )

    for record in list_governed_monitoring_lifecycle_records(session_id=session_id, plan_id=plan_id):
        events.append(
            {
                "event_id": str(record.get("record_id") or ""),
                "stage": "monitoring",
                "kind": record.get("kind"),
                "recorded_at": record.get("recorded_at"),
                "read_only": True,
            }
        )

    if workflow.get("present"):
        events.append(
            {
                "event_id": "workflow-result",
                "stage": "observe",
                "label": workflow.get("workflow_status"),
                "read_only": True,
            }
        )
    return events


def _required_evidence(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    session_id: str,
    verification: dict[str, Any] | None,
    deployment: dict[str, Any],
    workflow: dict[str, Any],
    timeline: list[dict[str, Any]],
    human_decision: str | None,
) -> dict[str, Any]:
    risk = dict((plan or {}).get("risk_assessment") or {})
    operator_reviews = [
        r
        for r in list_governed_monitoring_lifecycle_records(session_id=session_id, plan_id=plan_id)
        if str(r.get("kind") or "") in {"operator_review_note", "monitoring_observation"}
        or str(r.get("kind") or "") in OPERATIONAL_DECISION_KINDS
    ]
    items = {
        "deployment_reference": {
            "present": bool(deployment.get("present")),
            "deployment_id": deployment.get("deployment_id"),
            "environment": deployment.get("environment"),
        },
        "verification_evidence": {
            "present": workspace_verification_passed(plan_id=plan_id),
            "verification_id": (verification or {}).get("verification_id"),
        },
        "workflow_evidence": {
            "present": bool(workflow.get("present")),
            "workflow_status": workflow.get("workflow_status"),
        },
        "operational_timeline": {
            "present": len(timeline) >= 3,
            "event_count": len(timeline),
        },
        "risk_summary": {
            "present": bool(risk),
            "risk_tier": risk.get("risk_tier"),
            "blast_radius": risk.get("blast_radius"),
        },
        "operator_review_record": {
            "present": bool(operator_reviews) or human_decision is not None,
            "decision": human_decision,
            "review_count": len(operator_reviews),
        },
    }
    missing_all = [key for key in REQUIRED_MONITORING_EVIDENCE_IDS if not items[key]["present"]]
    missing_for_recommendation = [
        key for key in missing_all if key != "operator_review_record"
    ]
    return {
        "evidence_id": "required-monitoring-evidence",
        "items": items,
        "missing_evidence": missing_all,
        "missing_evidence_for_recommendation": missing_for_recommendation,
        "evidence_complete_for_recommendation": len(missing_for_recommendation) == 0,
        "evidence_complete_for_escalation": len(missing_all) == 0,
        "read_only": True,
    }


def _incident_classification(*, workflow: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    if not workflow.get("present"):
        classification = "UNKNOWN"
        rationale = "No workflow evidence observed yet."
    elif workflow.get("deployment_success"):
        classification = "HEALTHY"
        rationale = "GitHub Actions workflow reported success."
    elif workflow.get("workflow_status") in {"failure", "failed", "error"}:
        classification = "INCIDENT"
        rationale = "GitHub Actions workflow reported failure."
    elif workflow.get("workflow_status") in {"cancelled", "timeout", "degraded"}:
        classification = "DEGRADED"
        rationale = f"Workflow status: {workflow.get('workflow_status')}."
    elif evidence.get("missing_evidence_for_recommendation"):
        classification = "WARNING"
        rationale = "Operational evidence incomplete."
    else:
        classification = "WARNING"
        rationale = "Workflow completed with advisory signals."

    return {
        "classification_id": "incident-detection",
        "classification": classification,
        "valid_classifications": list(INCIDENT_CLASSIFICATIONS),
        "rationale": rationale,
        "advisory_only": True,
        "incident_response_authority": False,
        "read_only": True,
    }


def _monitoring_health_assessment(
    *,
    plan_id: str,
    workflow: dict[str, Any],
    deployment: dict[str, Any],
    evidence: dict[str, Any],
    incident: dict[str, Any],
    human_decision: str | None,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not deployment.get("present"):
        blockers.append("no_deployment_reference")
    if not workflow.get("present"):
        blockers.append("no_workflow_evidence")
    if evidence.get("missing_evidence_for_recommendation"):
        blockers.append("monitoring_evidence_incomplete")
    if incident.get("classification") == "INCIDENT" and human_decision not in {"investigate", "escalate"}:
        blockers.append("incident_requires_human_review")

    score = 100
    score -= len(blockers) * 12
    if incident.get("classification") == "INCIDENT":
        score -= 25
    elif incident.get("classification") == "DEGRADED":
        score -= 15
    elif incident.get("classification") == "WARNING":
        score -= 8
    score = max(0, min(100, score))

    return {
        "assessment_id": "monitoring-health",
        "health_score": score,
        "deployment_success": workflow.get("deployment_success"),
        "workflow_completion_observed": workflow.get("present"),
        "verification_status": evidence.get("items", {}).get("verification_evidence"),
        "evidence_completeness": {
            "complete_for_recommendation": evidence.get("evidence_complete_for_recommendation"),
            "missing": evidence.get("missing_evidence_for_recommendation"),
        },
        "operational_anomalies": [incident.get("classification")] if incident.get("classification") != "HEALTHY" else [],
        "outstanding_blockers": blockers,
        "required_evidence": evidence,
        "read_only": True,
    }


def _monitoring_review_package(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    deployment: dict[str, Any],
    workflow: dict[str, Any],
    health: dict[str, Any],
    incident: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    risk = dict((plan or {}).get("risk_assessment") or {})
    return {
        "packet_id": "monitoring-review-packet",
        "deployment_summary": deployment,
        "health_assessment": health,
        "incident_signals": incident,
        "verification_linkage": health.get("required_evidence", {}).get("items", {}).get("verification_evidence"),
        "evidence_linkage": health.get("required_evidence"),
        "risk_summary": {
            "risk_tier": risk.get("risk_tier"),
            "blast_radius": risk.get("blast_radius"),
        },
        "operational_timeline_preview": timeline[-5:],
        "read_only": True,
    }


def _monitoring_recommendation(
    *,
    incident: dict[str, Any],
    health: dict[str, Any],
    human_decision: str | None,
) -> dict[str, Any]:
    classification = str(incident.get("classification") or "UNKNOWN")
    blockers = list(health.get("outstanding_blockers") or [])

    if human_decision == "ignore":
        recommendation = "CONTINUE_OBSERVATION"
        rationale = "Human recorded ignore — continue passive observation."
    elif human_decision == "escalate":
        recommendation = "ESCALATE"
        rationale = "Human operational decision recorded as escalate."
    elif human_decision == "investigate":
        recommendation = "INVESTIGATE"
        rationale = "Human operational decision recorded as investigate."
    elif classification == "INCIDENT":
        recommendation = "ESCALATE"
        rationale = "Incident classification requires human escalation review."
    elif classification == "DEGRADED":
        recommendation = "INVESTIGATE"
        rationale = "Degraded workflow status — investigation recommended."
    elif classification == "WARNING" or blockers:
        recommendation = "REVIEW_REQUIRED"
        rationale = "Advisory signals or blockers require operator review."
    elif classification == "HEALTHY":
        recommendation = "CONTINUE_OBSERVATION"
        rationale = "Deployment healthy — continue observation."
    else:
        recommendation = "REVIEW_REQUIRED"
        rationale = "Insufficient operational evidence for confident observation."

    return {
        "recommendation_id": "monitoring-recommendation",
        "recommendation": recommendation,
        "valid_recommendations": list(MONITORING_RECOMMENDATIONS),
        "rationale": rationale,
        "recommendation_only": True,
        "monitoring_authority": False,
        "read_only": True,
    }


def _deployment_health_registry(*, session_id: str, plan_id: str, incident: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any]:
    env = deploy_target_environment(session_id=session_id, plan_id=plan_id)
    return {
        "registry_id": f"deployment-health-{plan_id}",
        "plan_id": plan_id,
        "session_id": session_id,
        "environment": env,
        "classification": incident.get("classification"),
        "workflow_status": workflow.get("workflow_status"),
        "last_observed_at": _exported_at(),
        "read_only": True,
    }


def _incident_escalation_artifact(
    *,
    plan_id: str,
    session_id: str,
    health: dict[str, Any],
    recommendation: dict[str, Any],
    review_packet: dict[str, Any],
    timeline: list[dict[str, Any]],
    human_decision: str | None,
    deployment: dict[str, Any],
) -> dict[str, Any] | None:
    if human_decision not in {"escalate", "investigate"} and recommendation.get("recommendation") != "ESCALATE":
        return None
    if not health.get("required_evidence", {}).get("evidence_complete_for_escalation"):
        if recommendation.get("recommendation") != "ESCALATE":
            return None

    return {
        "escalation_id": f"incident-escalation-{plan_id}",
        "plan_id": plan_id,
        "session_id": session_id,
        "incident_summary": review_packet.get("incident_signals"),
        "timeline": timeline,
        "evidence_references": health.get("required_evidence"),
        "audit_linkage": {
            "timeline_ref": timeline_link_ref(
                lane="governed_monitoring_lifecycle",
                action="incident_escalation",
                timestamp=plan_id,
            ),
            "replay_key": replay_link_key(
                source="governed_monitoring_lifecycle",
                lane="incident_escalation",
                action=plan_id,
            ),
        },
        "affected_deployment_references": [deployment],
        "escalation_executable": False,
        "incident_response_performed": False,
        "detail": "Incident escalation artifact — human review required; no autonomous remediation.",
        "read_only": True,
    }


def build_governed_monitoring_lifecycle(*, session_id: str) -> GovernedMonitoringLifecycleResult:
    sid = (session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "")
    verification = load_workspace_verification_for_plan(plan_id=plan_id) if plan_id else None
    pr_open = load_github_pr_open_for_plan(plan_id=plan_id) if plan_id else None
    human_decision = operational_decision_status(session_id=sid, plan_id=plan_id or None)
    operator_records = list_governed_monitoring_lifecycle_records(session_id=sid, plan_id=plan_id or None)

    blockers: list[str] = []
    if not plan:
        blockers.append("no_issue_plan_for_session")
    if plan_id and not deploy_target_environment(session_id=sid, plan_id=plan_id):
        blockers.append("no_deploy_target_environment")

    deployment = _deployment_reference(plan=plan, plan_id=plan_id, session_id=sid) if plan_id else {"present": False}
    workflow = _workflow_evidence(session_id=sid, plan_id=plan_id) if plan_id else {"present": False}
    timeline = _operational_timeline(session_id=sid, plan_id=plan_id, plan=plan, workflow=workflow) if plan_id else []
    evidence = _required_evidence(
        plan=plan,
        plan_id=plan_id,
        session_id=sid,
        verification=verification,
        deployment=deployment,
        workflow=workflow,
        timeline=timeline,
        human_decision=human_decision,
    )
    incident = _incident_classification(workflow=workflow, evidence=evidence)
    health = _monitoring_health_assessment(
        plan_id=plan_id,
        workflow=workflow,
        deployment=deployment,
        evidence=evidence,
        incident=incident,
        human_decision=human_decision,
    )
    review_packet = _monitoring_review_package(
        plan=plan,
        plan_id=plan_id,
        deployment=deployment,
        workflow=workflow,
        health=health,
        incident=incident,
        timeline=timeline,
    )
    recommendation = _monitoring_recommendation(
        incident=incident, health=health, human_decision=human_decision
    )
    escalation = _incident_escalation_artifact(
        plan_id=plan_id,
        session_id=sid,
        health=health,
        recommendation=recommendation,
        review_packet=review_packet,
        timeline=timeline,
        human_decision=human_decision,
        deployment=deployment,
    )
    health_registry = _deployment_health_registry(
        session_id=sid, plan_id=plan_id, incident=incident, workflow=workflow
    ) if plan_id else {}

    current_stage = "monitoring_observation"
    if escalation:
        current_stage = "incident_escalation"
    elif human_decision:
        current_stage = "operational_decision"
    elif incident.get("classification") != "UNKNOWN":
        current_stage = "incident_detection"

    sections = {
        "monitoring_health_assessment": [health],
        "incident_detection": [incident],
        "monitoring_review_package": [review_packet],
        "monitoring_recommendation": [recommendation],
        "human_operational_decisions": [
            {**r, "read_only": True}
            for r in operator_records
            if str(r.get("kind") or "") in OPERATIONAL_DECISION_KINDS
        ],
        "incident_escalation_artifact": [escalation] if escalation else [],
        "operational_timeline": timeline,
        "deployment_health_registry": [health_registry] if health_registry else [],
        "monitoring_sources": [
            {"source_id": src, "phase_1": True, "read_only": True} for src in MONITORING_SOURCES_PHASE_1
        ],
        "forbidden_monitoring_lifecycle_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_MONITORING_LIFECYCLE_ACTIONS
        ],
        "operator_monitoring_records": [{**r, "read_only": True} for r in operator_records],
    }

    payload: dict[str, Any] = {
        "schema_version": GOVERNED_MONITORING_LIFECYCLE_SCHEMA_VERSION,
        "fix": GOVERNED_MONITORING_LIFECYCLE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_220,
        "execution_performed": EXECUTION_PERFORMED_FIX_220,
        "observation_performed": OBSERVATION_PERFORMED_FIX_220,
        "monitoring_compose_evidence_only": GOVERNED_MONITORING_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_220,
        "monitoring_authority": MONITORING_AUTHORITY_FIX_220,
        "incident_response_authority": INCIDENT_RESPONSE_AUTHORITY_FIX_220,
        "autonomous_remediation_enabled": AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_220,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_220,
        "workflow_execution_authority": WORKFLOW_EXECUTION_AUTHORITY_FIX_220,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_220,
        "merge_authority": MERGE_AUTHORITY_FIX_220,
        "railway_authority": RAILWAY_AUTHORITY_FIX_220,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_220,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_220,
        "invariant": GOVERNED_MONITORING_LIFECYCLE_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id or None,
        "pr_url": (pr_open or {}).get("pr_url"),
        "lifecycle_stages": list(MONITORING_LIFECYCLE_STAGES),
        "current_stage": current_stage,
        "human_operational_decision": human_decision,
        "incident_classification": incident.get("classification"),
        "sections": sections,
        "monitoring_record_count": len(operator_records),
        "fix_220_certification_requirements": list(FIX_220_CERTIFICATION_REQUIREMENTS),
        "governed_monitoring_lifecycle_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_MONITORING_LIFECYCLE_PRINCIPLES
        ],
        "sources": {
            "composes_fix_210_deploy_evidence": True,
            "composes_software_delivery_verification": True,
            "github_actions_observation_only": True,
            "autonomous_remediation_performed": False,
        },
    }

    return GovernedMonitoringLifecycleResult(
        ok=True,
        session_id=sid,
        governed_monitoring_lifecycle=payload,
        blockers=blockers,
        detail="Governed monitoring lifecycle assembled (monitoring_authority ≠ operational_authority).",
    )


def prepare_governed_monitoring_escalation(*, session_id: str) -> GovernedMonitoringEscalationResult:
    lifecycle = build_governed_monitoring_lifecycle(session_id=session_id)
    board = lifecycle.governed_monitoring_lifecycle
    escalation_rows = (board.get("sections") or {}).get("incident_escalation_artifact") or []
    blockers: list[str] = list(lifecycle.blockers)

    if not escalation_rows:
        blockers.append("incident_escalation_not_ready")
        recommendation = ((board.get("sections") or {}).get("monitoring_recommendation") or [{}])[0]
        if recommendation.get("recommendation") not in {"ESCALATE", "INVESTIGATE"}:
            blockers.append("escalation_not_recommended")
        if board.get("human_operational_decision") not in {"escalate", "investigate"}:
            blockers.append("human_operational_decision_required")
        return GovernedMonitoringEscalationResult(
            ok=False,
            session_id=lifecycle.session_id,
            blockers=blockers,
            detail="Incident escalation blocked — evidence and human decision required.",
        )

    escalation = dict(escalation_rows[0])
    escalation["schema_version"] = GOVERNED_MONITORING_LIFECYCLE_ESCALATION_SCHEMA_VERSION
    escalation["executable"] = GOVERNED_MONITORING_ESCALATION_EXECUTABLE
    escalation["monitoring_authority"] = MONITORING_AUTHORITY_FIX_220
    escalation["incident_response_authority"] = INCIDENT_RESPONSE_AUTHORITY_FIX_220

    return GovernedMonitoringEscalationResult(
        ok=True,
        session_id=lifecycle.session_id,
        incident_escalation=escalation,
        detail="Incident escalation artifact prepared — human review required; no remediation performed.",
    )

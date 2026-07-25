# SPDX-License-Identifier: Apache-2.0
"""FIX 230 — governed rollback lifecycle service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_230_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
    deploy_target_environment,
    list_governed_deploy_lifecycle_records,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
    build_governed_monitoring_lifecycle,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_store import (
    list_governed_monitoring_lifecycle_records,
    operational_decision_status,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_contract import (
    AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
    DATABASE_MUTATION_AUTHORITY_FIX_230,
    DEPLOY_AUTHORITY_FIX_230,
    EXECUTION_PERFORMED_FIX_230,
    FORBIDDEN_ROLLBACK_LIFECYCLE_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_230,
    GITHUB_ACTIONS_ROLLBACK_WORKFLOW_TARGETS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_230,
    GOVERNED_ROLLBACK_HANDOFF_EXECUTABLE,
    GOVERNED_ROLLBACK_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_230,
    GOVERNED_ROLLBACK_LIFECYCLE_FIX,
    GOVERNED_ROLLBACK_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
    GOVERNED_ROLLBACK_LIFECYCLE_INVARIANT,
    GOVERNED_ROLLBACK_LIFECYCLE_PRINCIPLES,
    GOVERNED_ROLLBACK_LIFECYCLE_SCHEMA_VERSION,
    HIDDEN_RECOVERY_PATH_ENABLED_FIX_230,
    MERGE_AUTHORITY_FIX_230,
    MONITORING_AUTHORITY_FIX_230,
    MUTATION_PERFORMED_FIX_230,
    PROVIDER_MUTATION_AUTHORITY_FIX_230,
    RAILWAY_AUTHORITY_FIX_230,
    REQUIRED_ROLLBACK_EVIDENCE_IDS,
    ROLLBACK_AUTHORITY_FIX_230,
    ROLLBACK_DECISION_KINDS,
    ROLLBACK_LIFECYCLE_STAGES,
    ROLLBACK_RECOMMENDATIONS,
    SUPPORTED_ROLLBACK_ADAPTERS,
    WORKFLOW_EXECUTION_PERFORMED_FIX_230,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_store import (
    list_governed_rollback_lifecycle_records,
    rollback_decision_status,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import replay_link_key, timeline_link_ref
from aethos_core.software_delivery.github_pr_open_store import load_github_pr_open_for_plan
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.workspace_verification_store import (
    load_workspace_verification_for_plan,
    workspace_verification_passed,
)


@dataclass(frozen=True)
class GovernedRollbackLifecycleResult:
    ok: bool
    session_id: str
    governed_rollback_lifecycle: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class GovernedRollbackHandoffResult:
    ok: bool
    session_id: str
    rollback_handoff: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _deployment_reference(*, plan: dict[str, Any] | None, plan_id: str, session_id: str) -> dict[str, Any]:
    env = deploy_target_environment(session_id=session_id, plan_id=plan_id)
    deploy_records = list_governed_deploy_lifecycle_records(session_id=session_id, plan_id=plan_id)
    return {
        "deployment_id": f"deploy-{plan_id}",
        "plan_id": plan_id,
        "issue_reference": (plan or {}).get("issue_reference"),
        "environment": env,
        "deploy_record_count": len(deploy_records),
        "present": bool(deploy_records or env),
        "read_only": True,
    }


def _monitoring_snapshot(*, session_id: str) -> dict[str, Any]:
    result = build_governed_monitoring_lifecycle(session_id=session_id)
    board = result.governed_monitoring_lifecycle
    sections = board.get("sections") or {}
    incident = (sections.get("incident_detection") or [{}])[0]
    health = (sections.get("monitoring_health_assessment") or [{}])[0]
    return {
        "present": bool(board.get("plan_id")),
        "incident_classification": board.get("incident_classification"),
        "human_operational_decision": board.get("human_operational_decision"),
        "health_score": health.get("health_score"),
        "incident": incident,
        "health": health,
        "operational_timeline": sections.get("operational_timeline") or [],
        "read_only": True,
    }


def _deployment_history(*, session_id: str, plan_id: str) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for record in list_governed_deploy_lifecycle_records(session_id=session_id, plan_id=plan_id):
        meta = dict(record.get("metadata") or {})
        history.append(
            {
                "record_id": record.get("record_id"),
                "kind": record.get("kind"),
                "recorded_at": record.get("recorded_at"),
                "workflow_status": meta.get("workflow_status") or meta.get("deployment_status"),
                "environment": meta.get("environment"),
                "read_only": True,
            }
        )
    return history


def _rollback_candidate_registry(
    *,
    session_id: str,
    plan_id: str,
    deployment_history: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_records = [
        r
        for r in list_governed_rollback_lifecycle_records(session_id=session_id, plan_id=plan_id)
        if str(r.get("kind") or "") == "rollback_candidate_note"
    ]
    explicit = candidate_records[-1] if candidate_records else None
    explicit_meta = dict((explicit or {}).get("metadata") or {})

    successful_deploys = [
        h
        for h in deployment_history
        if str(h.get("workflow_status") or "").lower() == "success"
        and str(h.get("kind") or "") in {"deploy_execution_request_note", "deploy_handoff_note"}
    ]
    prior_success = successful_deploys[-1] if successful_deploys else None

    target_release = explicit_meta.get("target_release") or explicit_meta.get("rollback_target")
    if not target_release and prior_success:
        target_release = f"prior-deploy-{prior_success.get('record_id')}"

    candidates: list[dict[str, Any]] = []
    if target_release:
        candidates.append(
            {
                "candidate_id": f"rollback-target-{plan_id}",
                "target_release": target_release,
                "source": "operator_note" if explicit else "prior_successful_deploy",
                "verified": workspace_verification_passed(plan_id=plan_id),
                "read_only": True,
            }
        )
    if prior_success and not explicit:
        candidates.append(
            {
                "candidate_id": f"prior-success-{prior_success.get('record_id')}",
                "target_release": f"prior-deploy-{prior_success.get('record_id')}",
                "source": "last_known_good_deployment",
                "record_id": prior_success.get("record_id"),
                "read_only": True,
            }
        )

    return {
        "registry_id": f"rollback-candidates-{plan_id}",
        "candidates": candidates,
        "last_known_good": candidates[0] if candidates else None,
        "prior_successful_release": prior_success,
        "explicit_candidate_record": explicit,
        "present": bool(candidates),
        "read_only": True,
    }


def _rollback_risk_summary(*, plan: dict[str, Any] | None, plan_id: str, session_id: str) -> dict[str, Any]:
    risk = dict((plan or {}).get("risk_assessment") or {})
    risk_notes = [
        r
        for r in list_governed_rollback_lifecycle_records(session_id=session_id, plan_id=plan_id)
        if str(r.get("kind") or "") == "rollback_risk_note"
    ]
    return {
        "risk_id": f"rollback-risk-{plan_id}",
        "blast_radius": risk.get("blast_radius"),
        "dependency_impact": risk.get("dependency_impact") or risk.get("affected_systems"),
        "configuration_drift": risk.get("configuration_drift") or "unknown",
        "data_migration_risk": risk.get("data_migration_risk") or "unknown",
        "operational_uncertainty": risk.get("operational_uncertainty") or "elevated_during_incident",
        "risk_tier": risk.get("risk_tier"),
        "operator_risk_notes": len(risk_notes),
        "present": bool(risk) or bool(risk_notes),
        "read_only": True,
    }


def _required_evidence(
    *,
    plan_id: str,
    session_id: str,
    deployment: dict[str, Any],
    monitoring: dict[str, Any],
    candidates: dict[str, Any],
    risk: dict[str, Any],
    human_decision: str | None,
) -> dict[str, Any]:
    incident = monitoring.get("incident") or {}
    items = {
        "deployment_reference": {
            "present": bool(deployment.get("present")),
            "deployment_id": deployment.get("deployment_id"),
        },
        "monitoring_evidence": {
            "present": bool(monitoring.get("present")),
            "incident_classification": monitoring.get("incident_classification"),
        },
        "incident_assessment": {
            "present": bool(incident.get("classification")),
            "classification": incident.get("classification"),
        },
        "risk_assessment": {
            "present": bool(risk.get("present")),
            "risk_tier": risk.get("risk_tier"),
        },
        "rollback_target": {
            "present": bool(candidates.get("present")),
            "target": (candidates.get("last_known_good") or {}).get("target_release"),
        },
        "human_decision_record": {
            "present": human_decision is not None,
            "decision": human_decision,
        },
    }
    missing_all = [key for key in REQUIRED_ROLLBACK_EVIDENCE_IDS if not items[key]["present"]]
    return {
        "evidence_id": "required-rollback-evidence",
        "items": items,
        "missing_evidence": missing_all,
        "evidence_complete_for_recommendation": len(missing_all) == 0,
        "evidence_complete_for_handoff": len(missing_all) == 0 and human_decision == "approve",
        "read_only": True,
    }


def _rollback_assessment(
    *,
    plan_id: str,
    monitoring: dict[str, Any],
    deployment: dict[str, Any],
    deployment_history: list[dict[str, Any]],
    evidence: dict[str, Any],
    human_operational_decision: str | None,
) -> dict[str, Any]:
    incident_class = monitoring.get("incident_classification")
    blockers: list[str] = []
    if incident_class not in {"INCIDENT", "DEGRADED", "WARNING"}:
        if human_operational_decision not in {"escalate", "investigate"}:
            blockers.append("no_incident_or_escalation_signal")
    if not deployment.get("present"):
        blockers.append("no_deployment_reference")
    if evidence.get("missing_evidence"):
        blockers.extend([f"missing_{m}" for m in evidence.get("missing_evidence", [])])

    score = 100
    score -= len(blockers) * 10
    if incident_class == "INCIDENT":
        score -= 20
    elif incident_class == "DEGRADED":
        score -= 12
    score = max(0, min(100, score))

    return {
        "assessment_id": "rollback-assessment",
        "readiness_score": score,
        "deployment_health": monitoring.get("health_score"),
        "incident_severity": incident_class,
        "deployment_history_count": len(deployment_history),
        "verification_status": workspace_verification_passed(plan_id=plan_id),
        "evidence_completeness": {
            "complete": evidence.get("evidence_complete_for_recommendation"),
            "missing": evidence.get("missing_evidence"),
        },
        "outstanding_blockers": blockers,
        "required_evidence": evidence,
        "read_only": True,
    }


def _rollback_review_package(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    monitoring: dict[str, Any],
    deployment: dict[str, Any],
    deployment_history: list[dict[str, Any]],
    candidates: dict[str, Any],
    risk: dict[str, Any],
    assessment: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "packet_id": "rollback-review-packet",
        "incident_summary": monitoring.get("incident"),
        "deployment_history": deployment_history[-5:],
        "candidate_rollback_target": candidates.get("last_known_good"),
        "risk_assessment": risk,
        "verification_references": {
            "verification_passed": workspace_verification_passed(plan_id=plan_id),
            "plan_id": plan_id,
        },
        "evidence_linkage": assessment.get("required_evidence"),
        "deployment_summary": deployment,
        "issue_reference": (plan or {}).get("issue_reference"),
        "timeline_preview": timeline[-6:],
        "read_only": True,
    }


def _rollback_recommendation(
    *,
    monitoring: dict[str, Any],
    assessment: dict[str, Any],
    human_decision: str | None,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    if not evidence.get("evidence_complete_for_recommendation"):
        return {
            "recommendation_id": "rollback-recommendation",
            "recommendation": "INVESTIGATE",
            "valid_recommendations": list(ROLLBACK_RECOMMENDATIONS),
            "rationale": "Rollback evidence incomplete — investigation required before recommendation.",
            "recommendation_only": True,
            "rollback_authority": False,
            "blocked": True,
            "read_only": True,
        }

    incident = str(monitoring.get("incident_classification") or "UNKNOWN")
    blockers = list(assessment.get("outstanding_blockers") or [])

    if human_decision == "reject":
        recommendation = "CONTINUE_MONITORING"
        rationale = "Human rollback decision recorded as reject — continue monitoring."
    elif human_decision == "hold":
        recommendation = "INVESTIGATE"
        rationale = "Human rollback decision recorded as hold — continue investigation."
    elif human_decision == "approve":
        recommendation = "RECOMMEND_ROLLBACK"
        rationale = "Human rollback approval recorded — recommend rollback handoff for human execution."
    elif incident == "INCIDENT":
        recommendation = "RECOMMEND_ROLLBACK"
        rationale = "Incident classification with complete evidence — rollback review recommended."
    elif incident == "DEGRADED":
        recommendation = "PREPARE_ROLLBACK"
        rationale = "Degraded deployment — prepare rollback review packet."
    elif incident == "WARNING" or blockers:
        recommendation = "INVESTIGATE"
        rationale = "Advisory signals require investigation before rollback preparation."
    elif incident == "HEALTHY":
        recommendation = "CONTINUE_MONITORING"
        rationale = "Deployment healthy — continue monitoring; rollback not indicated."
    else:
        recommendation = "INVESTIGATE"
        rationale = "Operational uncertainty — investigate before rollback recommendation."

    return {
        "recommendation_id": "rollback-recommendation",
        "recommendation": recommendation,
        "valid_recommendations": list(ROLLBACK_RECOMMENDATIONS),
        "rationale": rationale,
        "recommendation_only": True,
        "rollback_authority": False,
        "read_only": True,
    }


def _github_actions_rollback_adapter(
    *,
    environment: str,
    plan_id: str,
    repository: str,
    target_release: str,
) -> dict[str, Any]:
    ref = "main"
    templates = [
        f"gh workflow run {wf} --ref {ref} -f environment={environment} -f target_release={target_release}"
        for wf in GITHUB_ACTIONS_ROLLBACK_WORKFLOW_TARGETS
    ]
    primary = templates[0]
    return {
        "adapter_id": "github-actions-rollback-workflow",
        "provider": "github_actions",
        "supported_adapters": list(SUPPORTED_ROLLBACK_ADAPTERS),
        "repository": repository,
        "plan_id": plan_id,
        "environment": environment,
        "target_release": target_release,
        "workflow_targets": list(GITHUB_ACTIONS_ROLLBACK_WORKFLOW_TARGETS),
        "command_template": primary,
        "alternative_templates": templates[1:],
        "api_operation": "workflow_dispatch",
        "executable": False,
        "rollback_authority": False,
        "workflow_execution_performed": False,
        "autonomous_rollback_enabled": False,
        "requires_human_execution": True,
        "read_only": True,
    }


def _rollback_handoff_artifact(
    *,
    plan_id: str,
    session_id: str,
    assessment: dict[str, Any],
    recommendation: dict[str, Any],
    adapter: dict[str, Any],
    human_decision: str | None,
    candidates: dict[str, Any],
    target_env: str | None,
) -> dict[str, Any] | None:
    if human_decision != "approve" or not target_env:
        return None
    if not assessment.get("required_evidence", {}).get("evidence_complete_for_handoff"):
        return None
    if recommendation.get("recommendation") not in {"PREPARE_ROLLBACK", "RECOMMEND_ROLLBACK"}:
        return None

    target = (candidates.get("last_known_good") or {}).get("target_release") or adapter.get("target_release")
    return {
        "handoff_id": f"rollback-handoff-{plan_id}-{target_env}",
        "plan_id": plan_id,
        "session_id": session_id,
        "environment_target": target_env,
        "rollback_request_id": f"rollback-req-{plan_id}-{target_env}",
        "target_release": target,
        "approval_linkage": {
            "rollback_decision": human_decision,
            "environment": target_env,
        },
        "audit_linkage": {
            "timeline_ref": timeline_link_ref(
                lane="governed_rollback_lifecycle",
                action="rollback_handoff",
                timestamp=plan_id,
            ),
            "replay_key": replay_link_key(
                source="governed_rollback_lifecycle",
                lane="rollback_handoff",
                action=f"{plan_id}:{target_env}",
            ),
        },
        "evidence_references": assessment.get("required_evidence"),
        "github_actions_rollback_adapter": adapter,
        "handoff_executable": False,
        "workflow_execution_performed": False,
        "detail": "Rollback execution request — human must dispatch GitHub Actions rollback workflow.",
        "read_only": True,
    }


def _recovery_timeline(
    *,
    session_id: str,
    plan_id: str,
    monitoring_timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = list(monitoring_timeline)
    for record in list_governed_rollback_lifecycle_records(session_id=session_id, plan_id=plan_id):
        events.append(
            {
                "event_id": str(record.get("record_id") or ""),
                "stage": "rollback",
                "kind": record.get("kind"),
                "recorded_at": record.get("recorded_at"),
                "read_only": True,
            }
        )
    return events


def build_governed_rollback_lifecycle(*, session_id: str) -> GovernedRollbackLifecycleResult:
    sid = (session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "")
    verification = load_workspace_verification_for_plan(plan_id=plan_id) if plan_id else None
    pr_open = load_github_pr_open_for_plan(plan_id=plan_id) if plan_id else None
    human_decision = rollback_decision_status(session_id=sid, plan_id=plan_id or None)
    human_operational_decision = operational_decision_status(session_id=sid, plan_id=plan_id or None)
    operator_records = list_governed_rollback_lifecycle_records(session_id=sid, plan_id=plan_id or None)
    target_env = deploy_target_environment(session_id=sid, plan_id=plan_id or None) if plan_id else None

    blockers: list[str] = []
    if not plan:
        blockers.append("no_issue_plan_for_session")

    deployment = _deployment_reference(plan=plan, plan_id=plan_id, session_id=sid) if plan_id else {"present": False}
    monitoring = _monitoring_snapshot(session_id=sid) if plan_id else {"present": False}
    deployment_history = _deployment_history(session_id=sid, plan_id=plan_id) if plan_id else []
    candidates = (
        _rollback_candidate_registry(
            session_id=sid, plan_id=plan_id, deployment_history=deployment_history
        )
        if plan_id
        else {"present": False}
    )
    risk = _rollback_risk_summary(plan=plan, plan_id=plan_id, session_id=sid) if plan_id else {"present": False}
    evidence = _required_evidence(
        plan_id=plan_id,
        session_id=sid,
        deployment=deployment,
        monitoring=monitoring,
        candidates=candidates,
        risk=risk,
        human_decision=human_decision,
    )
    assessment = _rollback_assessment(
        plan_id=plan_id,
        monitoring=monitoring,
        deployment=deployment,
        deployment_history=deployment_history,
        evidence=evidence,
        human_operational_decision=human_operational_decision,
    )
    review_packet = _rollback_review_package(
        plan=plan,
        plan_id=plan_id,
        monitoring=monitoring,
        deployment=deployment,
        deployment_history=deployment_history,
        candidates=candidates,
        risk=risk,
        assessment=assessment,
        timeline=_recovery_timeline(
            session_id=sid,
            plan_id=plan_id,
            monitoring_timeline=monitoring.get("operational_timeline") or [],
        )
        if plan_id
        else [],
    )
    recommendation = _rollback_recommendation(
        monitoring=monitoring,
        assessment=assessment,
        human_decision=human_decision,
        evidence=evidence,
    )
    repository = str((pr_open or {}).get("repository") or (plan or {}).get("issue_reference") or "")
    target_release = str((candidates.get("last_known_good") or {}).get("target_release") or f"prior-{plan_id}")
    adapter = _github_actions_rollback_adapter(
        environment=target_env or "staging",
        plan_id=plan_id,
        repository=repository,
        target_release=target_release,
    ) if plan_id else {}
    handoff = _rollback_handoff_artifact(
        plan_id=plan_id,
        session_id=sid,
        assessment=assessment,
        recommendation=recommendation,
        adapter=adapter,
        human_decision=human_decision,
        candidates=candidates,
        target_env=target_env,
    ) if plan_id else None
    recovery_timeline = _recovery_timeline(
        session_id=sid,
        plan_id=plan_id,
        monitoring_timeline=monitoring.get("operational_timeline") or [],
    ) if plan_id else []

    current_stage = "rollback_assessment"
    if handoff:
        current_stage = "rollback_handoff"
    elif human_decision:
        current_stage = "rollback_decision"
    elif recommendation.get("recommendation") in {"PREPARE_ROLLBACK", "RECOMMEND_ROLLBACK"}:
        current_stage = "rollback_review"
    elif monitoring.get("incident_classification") not in {None, "HEALTHY", "UNKNOWN"}:
        current_stage = "incident_observed"

    sections = {
        "rollback_assessment": [assessment],
        "rollback_candidate_registry": [candidates],
        "rollback_risk_summary": [risk],
        "rollback_review_package": [review_packet],
        "rollback_recommendation": [recommendation],
        "human_rollback_decisions": [
            {**r, "read_only": True}
            for r in operator_records
            if str(r.get("kind") or "") in ROLLBACK_DECISION_KINDS
        ],
        "rollback_handoff_artifact": [handoff] if handoff else [],
        "recovery_timeline": recovery_timeline,
        "forbidden_rollback_lifecycle_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_ROLLBACK_LIFECYCLE_ACTIONS
        ],
        "operator_rollback_records": [{**r, "read_only": True} for r in operator_records],
    }

    payload: dict[str, Any] = {
        "schema_version": GOVERNED_ROLLBACK_LIFECYCLE_SCHEMA_VERSION,
        "fix": GOVERNED_ROLLBACK_LIFECYCLE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_230,
        "execution_performed": EXECUTION_PERFORMED_FIX_230,
        "rollback_compose_evidence_only": GOVERNED_ROLLBACK_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_230,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_230,
        "autonomous_rollback_enabled": AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
        "workflow_execution_performed": WORKFLOW_EXECUTION_PERFORMED_FIX_230,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_230,
        "database_mutation_authority": DATABASE_MUTATION_AUTHORITY_FIX_230,
        "hidden_recovery_path_enabled": HIDDEN_RECOVERY_PATH_ENABLED_FIX_230,
        "monitoring_authority": MONITORING_AUTHORITY_FIX_230,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_230,
        "merge_authority": MERGE_AUTHORITY_FIX_230,
        "railway_authority": RAILWAY_AUTHORITY_FIX_230,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_230,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_230,
        "invariant": GOVERNED_ROLLBACK_LIFECYCLE_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id or None,
        "pr_url": (pr_open or {}).get("pr_url"),
        "verification_id": (verification or {}).get("verification_id"),
        "lifecycle_stages": list(ROLLBACK_LIFECYCLE_STAGES),
        "current_stage": current_stage,
        "human_rollback_decision": human_decision,
        "human_operational_decision": human_operational_decision,
        "incident_classification": monitoring.get("incident_classification"),
        "sections": sections,
        "rollback_record_count": len(operator_records),
        "fix_230_certification_requirements": list(FIX_230_CERTIFICATION_REQUIREMENTS),
        "governed_rollback_lifecycle_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_ROLLBACK_LIFECYCLE_PRINCIPLES
        ],
        "sources": {
            "composes_fix_220_monitoring_evidence": True,
            "composes_fix_210_deploy_evidence": True,
            "github_actions_rollback_templates_only": True,
            "autonomous_rollback_performed": False,
        },
    }

    return GovernedRollbackLifecycleResult(
        ok=True,
        session_id=sid,
        governed_rollback_lifecycle=payload,
        blockers=blockers,
        detail="Governed rollback lifecycle assembled (rollback_authority ≠ autonomous_rollback).",
    )


def prepare_governed_rollback_handoff(*, session_id: str) -> GovernedRollbackHandoffResult:
    lifecycle = build_governed_rollback_lifecycle(session_id=session_id)
    board = lifecycle.governed_rollback_lifecycle
    handoff_rows = (board.get("sections") or {}).get("rollback_handoff_artifact") or []
    blockers: list[str] = list(lifecycle.blockers)

    if not handoff_rows:
        blockers.append("rollback_handoff_not_ready")
        recommendation = ((board.get("sections") or {}).get("rollback_recommendation") or [{}])[0]
        if board.get("human_rollback_decision") != "approve":
            blockers.append("human_rollback_approval_required")
        if recommendation.get("recommendation") not in {"PREPARE_ROLLBACK", "RECOMMEND_ROLLBACK"}:
            blockers.append("rollback_not_recommended")
        return GovernedRollbackHandoffResult(
            ok=False,
            session_id=lifecycle.session_id,
            blockers=blockers,
            detail="Rollback handoff blocked — evidence, recommendation, and human approval required.",
        )

    handoff = dict(handoff_rows[0])
    handoff["schema_version"] = GOVERNED_ROLLBACK_LIFECYCLE_HANDOFF_SCHEMA_VERSION
    handoff["executable"] = GOVERNED_ROLLBACK_HANDOFF_EXECUTABLE
    handoff["rollback_authority"] = ROLLBACK_AUTHORITY_FIX_230
    handoff["autonomous_rollback_enabled"] = AUTONOMOUS_ROLLBACK_ENABLED_FIX_230
    handoff["workflow_execution_performed"] = WORKFLOW_EXECUTION_PERFORMED_FIX_230

    return GovernedRollbackHandoffResult(
        ok=True,
        session_id=lifecycle.session_id,
        rollback_handoff=handoff,
        detail="Rollback execution request prepared — human must dispatch GitHub Actions workflow.",
    )

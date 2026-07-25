# SPDX-License-Identifier: Apache-2.0
"""FIX 210 — governed deploy lifecycle service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_210_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_contract import (
    APPROVAL_BYPASS_ENABLED_FIX_210,
    AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
    AWS_AUTHORITY_FIX_210,
    DEPLOY_AUTHORITY_FIX_210,
    DEPLOY_LIFECYCLE_STAGES,
    DEPLOY_RECOMMENDATIONS,
    EXECUTION_PERFORMED_FIX_210,
    FORBIDDEN_DEPLOY_LIFECYCLE_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_210,
    GITHUB_ACTIONS_WORKFLOW_TARGETS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_210,
    GOVERNED_DEPLOY_HANDOFF_EXECUTABLE,
    GOVERNED_DEPLOY_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_210,
    GOVERNED_DEPLOY_LIFECYCLE_FIX,
    GOVERNED_DEPLOY_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
    GOVERNED_DEPLOY_LIFECYCLE_INVARIANT,
    GOVERNED_DEPLOY_LIFECYCLE_PRINCIPLES,
    GOVERNED_DEPLOY_LIFECYCLE_SCHEMA_VERSION,
    HIDDEN_WORKFLOW_EXECUTION_ENABLED_FIX_210,
    KUBERNETES_AUTHORITY_FIX_210,
    MERGE_AUTHORITY_FIX_210,
    MUTATION_PERFORMED_FIX_210,
    PHASE_1_DEPLOY_ENVIRONMENTS,
    PROVIDER_AUTHORITY_FIX_210,
    RAILWAY_AUTHORITY_FIX_210,
    REQUIRED_DEPLOY_EVIDENCE_IDS,
    SUPPORTED_DEPLOY_ADAPTERS,
    VERCEL_AUTHORITY_FIX_210,
    WORKFLOW_EXECUTION_PERFORMED_FIX_210,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
    deploy_decision_status,
    deploy_target_environment,
    list_governed_deploy_lifecycle_records,
    merge_completed_acknowledged,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_store import (
    list_governed_merge_lifecycle_records,
    merge_decision_status,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import replay_link_key, timeline_link_ref
from aethos_core.software_delivery.github_pr_open_store import (
    github_pr_open_completed_for_plan,
    load_github_pr_open_for_plan,
)
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.workspace_verification_store import (
    load_workspace_verification_for_plan,
    workspace_verification_passed,
)


@dataclass(frozen=True)
class GovernedDeployLifecycleResult:
    ok: bool
    session_id: str
    governed_deploy_lifecycle: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class GovernedDeployHandoffResult:
    ok: bool
    session_id: str
    deploy_handoff: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _merge_evidence(*, session_id: str, plan_id: str) -> dict[str, Any]:
    merge_decision = merge_decision_status(session_id=session_id, plan_id=plan_id)
    merge_records = list_governed_merge_lifecycle_records(session_id=session_id, plan_id=plan_id)
    merge_approved = merge_decision == "approve"
    merge_completed = merge_completed_acknowledged(session_id=session_id, plan_id=plan_id)
    handoff_notes = [
        r for r in merge_records if str(r.get("kind") or "") in {"merge_handoff_note", "merge_execution_request_note"}
    ]
    return {
        "merge_decision": merge_decision,
        "merge_approved": merge_approved,
        "merge_completed_acknowledged": merge_completed,
        "merge_handoff_record_count": len(handoff_notes),
        "present": merge_approved and merge_completed,
        "read_only": True,
    }


def _rollback_reference(*, plan: dict[str, Any] | None, plan_id: str) -> dict[str, Any]:
    risk = dict((plan or {}).get("risk_assessment") or {})
    return {
        "rollback_id": f"rollback-ref-{plan_id}",
        "blast_radius": risk.get("blast_radius"),
        "affected_files": list((plan or {}).get("affected_files") or []),
        "rollback_strategy": "revert_merge_and_redeploy_previous",
        "staging_required_before_production": True,
        "present": bool(plan_id and risk),
        "read_only": True,
    }


def _required_evidence(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    session_id: str,
    verification: dict[str, Any] | None,
    merge: dict[str, Any],
    rollback: dict[str, Any],
    human_decision: str | None,
) -> dict[str, Any]:
    risk = dict((plan or {}).get("risk_assessment") or {})
    items = {
        "issue_reference": {
            "present": bool(plan and plan.get("issue_reference")),
            "value": (plan or {}).get("issue_reference"),
        },
        "merge_evidence": {
            "present": bool(merge.get("present")),
            "merge_decision": merge.get("merge_decision"),
            "merge_completed_acknowledged": merge.get("merge_completed_acknowledged"),
        },
        "verification_evidence": {
            "present": workspace_verification_passed(plan_id=plan_id),
            "verification_id": (verification or {}).get("verification_id"),
            "status": (verification or {}).get("status"),
        },
        "risk_assessment": {
            "present": bool(risk),
            "risk_tier": risk.get("risk_tier"),
        },
        "blast_radius_summary": {
            "present": bool(risk.get("blast_radius") or (plan or {}).get("affected_files")),
            "blast_radius": risk.get("blast_radius"),
        },
        "rollback_reference": {
            "present": bool(rollback.get("present")),
            "rollback_id": rollback.get("rollback_id"),
        },
        "human_approval_record": {
            "present": human_decision == "approve",
            "decision": human_decision,
        },
    }
    missing_all = [key for key in REQUIRED_DEPLOY_EVIDENCE_IDS if not items[key]["present"]]
    missing_for_recommendation = [
        key for key in missing_all if key != "human_approval_record"
    ]
    return {
        "evidence_id": "required-deploy-evidence",
        "items": items,
        "missing_evidence": missing_all,
        "missing_evidence_for_recommendation": missing_for_recommendation,
        "evidence_complete_for_recommendation": len(missing_for_recommendation) == 0,
        "evidence_complete_for_handoff": len(missing_all) == 0,
        "read_only": True,
    }


def _environment_eligibility(*, target_env: str | None) -> dict[str, Any]:
    if not target_env:
        return {
            "eligible": False,
            "phase_1_environments": list(PHASE_1_DEPLOY_ENVIRONMENTS),
            "production_blocked": True,
            "read_only": True,
        }
    return {
        "eligible": target_env in PHASE_1_DEPLOY_ENVIRONMENTS,
        "target_environment": target_env,
        "phase_1_environments": list(PHASE_1_DEPLOY_ENVIRONMENTS),
        "production_blocked": True,
        "read_only": True,
    }


def _deploy_readiness_assessment(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    session_id: str,
    verification: dict[str, Any] | None,
    pr_open: dict[str, Any] | None,
    merge: dict[str, Any],
    rollback: dict[str, Any],
    human_decision: str | None,
    target_env: str | None,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not plan:
        blockers.append("no_issue_plan")
    if not github_pr_open_completed_for_plan(plan_id=plan_id):
        blockers.append("pr_open_not_complete")
    if not merge.get("merge_approved"):
        blockers.append("merge_not_approved")
    if not merge.get("merge_completed_acknowledged"):
        blockers.append("merge_not_completed")
    if not workspace_verification_passed(plan_id=plan_id):
        blockers.append("verification_not_passed")

    evidence = _required_evidence(
        plan=plan,
        plan_id=plan_id,
        session_id=session_id,
        verification=verification,
        merge=merge,
        rollback=rollback,
        human_decision=human_decision,
    )
    if evidence["missing_evidence_for_recommendation"]:
        blockers.append("required_evidence_incomplete")

    env_eligibility = _environment_eligibility(target_env=target_env)
    if human_decision == "approve" and target_env and not env_eligibility["eligible"]:
        blockers.append("environment_not_eligible")
    if human_decision == "reject":
        blockers.append("human_deploy_rejected")
    elif human_decision == "hold":
        blockers.append("human_deploy_on_hold")

    readiness_score = 100
    readiness_score -= len(blockers) * 10
    readiness_score = max(0, min(100, readiness_score))

    return {
        "assessment_id": "deploy-readiness",
        "readiness_score": readiness_score,
        "repository_state": {
            "issue_reference": (plan or {}).get("issue_reference"),
            "plan_id": plan_id,
            "pr_url": (pr_open or {}).get("pr_url"),
        },
        "merge_status": merge,
        "required_checks": {
            "verification_passed": workspace_verification_passed(plan_id=plan_id),
            "pr_open_complete": github_pr_open_completed_for_plan(plan_id=plan_id),
            "merge_approved": merge.get("merge_approved"),
            "merge_completed": merge.get("merge_completed_acknowledged"),
        },
        "environment_eligibility": env_eligibility,
        "outstanding_blockers": blockers,
        "required_evidence": evidence,
        "deploy_ready_for_review": not blockers or (
            len(blockers) == 1 and blockers[0] == "human_deploy_on_hold"
        ),
        "read_only": True,
    }


def _deploy_review_package(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    merge: dict[str, Any],
    rollback: dict[str, Any],
    readiness: dict[str, Any],
    target_env: str | None,
) -> dict[str, Any]:
    risk = dict((plan or {}).get("risk_assessment") or {})
    return {
        "packet_id": "deploy-review-packet",
        "change_summary": {
            "issue_reference": (plan or {}).get("issue_reference"),
            "plan_id": plan_id,
            "summary": (plan or {}).get("implementation_summary") or (plan or {}).get("title"),
        },
        "verification_evidence": readiness.get("required_evidence", {}).get("items", {}).get(
            "verification_evidence"
        ),
        "merge_evidence": merge,
        "risk_summary": {
            "risk_tier": risk.get("risk_tier"),
            "blast_radius": risk.get("blast_radius"),
        },
        "blast_radius_summary": rollback,
        "environment_target": target_env or "pending_human_selection",
        "rollback_references": rollback,
        "read_only": True,
    }


def _deploy_recommendation(
    *,
    readiness: dict[str, Any],
    human_decision: str | None,
) -> dict[str, Any]:
    blockers = list(readiness.get("outstanding_blockers") or [])
    evidence = readiness.get("required_evidence") or {}
    missing_for_recommendation = list(evidence.get("missing_evidence_for_recommendation") or [])

    if human_decision == "reject":
        recommendation = "REJECT_DEPLOY"
        rationale = "Human deploy decision recorded as reject."
    elif human_decision == "hold":
        recommendation = "HOLD_DEPLOY"
        rationale = "Human deploy decision recorded as hold."
    elif missing_for_recommendation:
        recommendation = "HOLD_DEPLOY"
        rationale = f"Required evidence missing: {', '.join(missing_for_recommendation)}"
    elif blockers:
        recommendation = "CONDITIONAL_DEPLOY_APPROVAL" if len(blockers) <= 2 else "HOLD_DEPLOY"
        rationale = f"Outstanding blockers: {', '.join(blockers)}"
    elif human_decision == "approve":
        recommendation = "APPROVE_FOR_DEPLOY_REVIEW"
        rationale = "Evidence complete and human deploy approval recorded — ready for handoff."
    else:
        recommendation = (
            "APPROVE_FOR_DEPLOY_REVIEW" if readiness.get("deploy_ready_for_review") else "HOLD_DEPLOY"
        )
        rationale = "Automated readiness assessment — human deploy decision still required for handoff."

    return {
        "recommendation_id": "deploy-recommendation",
        "recommendation": recommendation,
        "valid_recommendations": list(DEPLOY_RECOMMENDATIONS),
        "rationale": rationale,
        "recommendation_only": True,
        "deploy_authority": False,
        "read_only": True,
    }


def _github_actions_adapter(
    *,
    environment: str,
    plan_id: str,
    repository: str,
    workflow: str = "deploy.yml",
    ref: str = "main",
) -> dict[str, Any]:
    templates = [
        f"gh workflow run {wf} --ref {ref} -f environment={environment}"
        for wf in GITHUB_ACTIONS_WORKFLOW_TARGETS
    ]
    primary = f"gh workflow run {workflow} --ref {ref} -f environment={environment}"
    return {
        "adapter_id": "github-actions-workflow-dispatch",
        "provider": "github_actions",
        "supported_adapters": list(SUPPORTED_DEPLOY_ADAPTERS),
        "repository": repository,
        "plan_id": plan_id,
        "environment": environment,
        "workflow_file": workflow,
        "workflow_targets": list(GITHUB_ACTIONS_WORKFLOW_TARGETS),
        "command_template": primary,
        "alternative_templates": templates,
        "api_operation": "workflow_dispatch",
        "executable": False,
        "deploy_authority": False,
        "workflow_execution_performed": False,
        "autonomous_deploy_enabled": False,
        "railway_authority": False,
        "vercel_authority": False,
        "aws_authority": False,
        "kubernetes_authority": False,
        "requires_human_execution": True,
        "read_only": True,
    }


def _deploy_handoff_artifact(
    *,
    plan_id: str,
    session_id: str,
    readiness: dict[str, Any],
    recommendation: dict[str, Any],
    adapter: dict[str, Any],
    human_decision: str | None,
    target_env: str | None,
) -> dict[str, Any] | None:
    if human_decision != "approve" or not target_env:
        return None
    if not readiness.get("required_evidence", {}).get("evidence_complete_for_handoff"):
        return None
    if recommendation.get("recommendation") not in {
        "APPROVE_FOR_DEPLOY_REVIEW",
        "CONDITIONAL_DEPLOY_APPROVAL",
    }:
        return None

    return {
        "handoff_id": f"deploy-handoff-{plan_id}-{target_env}",
        "plan_id": plan_id,
        "session_id": session_id,
        "environment_target": target_env,
        "deployment_request_id": f"deploy-req-{plan_id}-{target_env}",
        "approval_linkage": {
            "deploy_decision": human_decision,
            "environment": target_env,
        },
        "audit_linkage": {
            "timeline_ref": timeline_link_ref(
                lane="governed_deploy_lifecycle",
                action="deploy_handoff",
                timestamp=plan_id,
            ),
            "replay_key": replay_link_key(
                source="governed_deploy_lifecycle",
                lane="deploy_handoff",
                action=f"{plan_id}:{target_env}",
            ),
        },
        "evidence_references": readiness.get("required_evidence"),
        "github_actions_deployment_adapter": adapter,
        "handoff_executable": False,
        "workflow_execution_performed": False,
        "detail": "Deploy handoff artifact — human must dispatch GitHub Actions workflow.",
        "read_only": True,
    }


def build_governed_deploy_lifecycle(*, session_id: str) -> GovernedDeployLifecycleResult:
    sid = (session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "")
    verification = load_workspace_verification_for_plan(plan_id=plan_id) if plan_id else None
    pr_open = load_github_pr_open_for_plan(plan_id=plan_id) if plan_id else None
    human_decision = deploy_decision_status(session_id=sid, plan_id=plan_id or None)
    target_env = deploy_target_environment(session_id=sid, plan_id=plan_id or None)
    operator_records = list_governed_deploy_lifecycle_records(session_id=sid, plan_id=plan_id or None)

    blockers: list[str] = []
    if not plan:
        blockers.append("no_issue_plan_for_session")

    merge = _merge_evidence(session_id=sid, plan_id=plan_id) if plan_id else {"present": False}
    rollback = _rollback_reference(plan=plan, plan_id=plan_id) if plan_id else {"present": False}

    readiness = _deploy_readiness_assessment(
        plan=plan,
        plan_id=plan_id,
        session_id=sid,
        verification=verification,
        pr_open=pr_open,
        merge=merge,
        rollback=rollback,
        human_decision=human_decision,
        target_env=target_env,
    )
    review_packet = _deploy_review_package(
        plan=plan,
        plan_id=plan_id,
        merge=merge,
        rollback=rollback,
        readiness=readiness,
        target_env=target_env,
    )
    recommendation = _deploy_recommendation(readiness=readiness, human_decision=human_decision)
    repository = str((pr_open or {}).get("repository") or (plan or {}).get("issue_reference") or "")
    adapter = _github_actions_adapter(
        environment=target_env or "staging",
        plan_id=plan_id,
        repository=repository,
    )
    handoff = _deploy_handoff_artifact(
        plan_id=plan_id,
        session_id=sid,
        readiness=readiness,
        recommendation=recommendation,
        adapter=adapter,
        human_decision=human_decision,
        target_env=target_env,
    )

    current_stage = "deploy_readiness"
    if handoff:
        current_stage = "deploy_handoff"
    elif human_decision:
        current_stage = "deploy_decision"
    elif merge.get("merge_completed_acknowledged"):
        current_stage = "deploy_review"

    sections = {
        "deploy_readiness_assessment": [readiness],
        "deploy_review_package": [review_packet],
        "deploy_recommendation": [recommendation],
        "human_deploy_decisions": [
            {**r, "read_only": True}
            for r in operator_records
            if str(r.get("kind") or "").startswith("deploy_decision_")
        ],
        "deploy_handoff_artifact": [handoff] if handoff else [],
        "github_actions_deployment_adapter": [adapter],
        "post_deploy_audit": [
            {
                "audit_id": "post-deploy-audit-placeholder",
                "performed": False,
                "detail": "Post-deploy audit available after human workflow dispatch — AethOS does not deploy autonomously.",
                "read_only": True,
            }
        ],
        "forbidden_deploy_lifecycle_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_DEPLOY_LIFECYCLE_ACTIONS
        ],
        "operator_deploy_records": [{**r, "read_only": True} for r in operator_records],
    }

    payload: dict[str, Any] = {
        "schema_version": GOVERNED_DEPLOY_LIFECYCLE_SCHEMA_VERSION,
        "fix": GOVERNED_DEPLOY_LIFECYCLE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_210,
        "execution_performed": EXECUTION_PERFORMED_FIX_210,
        "workflow_execution_performed": WORKFLOW_EXECUTION_PERFORMED_FIX_210,
        "deploy_lifecycle_compose_evidence_only": GOVERNED_DEPLOY_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_210,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_210,
        "autonomous_deploy_enabled": AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
        "approval_bypass_enabled": APPROVAL_BYPASS_ENABLED_FIX_210,
        "hidden_workflow_execution_enabled": HIDDEN_WORKFLOW_EXECUTION_ENABLED_FIX_210,
        "merge_authority": MERGE_AUTHORITY_FIX_210,
        "railway_authority": RAILWAY_AUTHORITY_FIX_210,
        "vercel_authority": VERCEL_AUTHORITY_FIX_210,
        "aws_authority": AWS_AUTHORITY_FIX_210,
        "kubernetes_authority": KUBERNETES_AUTHORITY_FIX_210,
        "provider_authority": PROVIDER_AUTHORITY_FIX_210,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_210,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_210,
        "invariant": GOVERNED_DEPLOY_LIFECYCLE_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id or None,
        "lifecycle_stages": list(DEPLOY_LIFECYCLE_STAGES),
        "phase_1_environments": list(PHASE_1_DEPLOY_ENVIRONMENTS),
        "current_stage": current_stage,
        "human_deploy_decision": human_decision,
        "deploy_target_environment": target_env,
        "sections": sections,
        "deploy_record_count": len(operator_records),
        "fix_210_certification_requirements": list(FIX_210_CERTIFICATION_REQUIREMENTS),
        "governed_deploy_lifecycle_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_DEPLOY_LIFECYCLE_PRINCIPLES
        ],
        "sources": {
            "composes_fix_200_merge_evidence": True,
            "composes_software_delivery_verification": True,
            "github_actions_only_phase_1": True,
            "autonomous_deploy_performed": False,
        },
    }

    return GovernedDeployLifecycleResult(
        ok=True,
        session_id=sid,
        governed_deploy_lifecycle=payload,
        blockers=blockers,
        detail="Governed deploy lifecycle assembled (deploy_authority ≠ autonomous_deploy).",
    )


def prepare_governed_deploy_handoff(*, session_id: str) -> GovernedDeployHandoffResult:
    lifecycle = build_governed_deploy_lifecycle(session_id=session_id)
    board = lifecycle.governed_deploy_lifecycle
    handoff_rows = (board.get("sections") or {}).get("deploy_handoff_artifact") or []
    blockers: list[str] = list(lifecycle.blockers)

    if not handoff_rows:
        blockers.append("deploy_handoff_not_ready")
        if board.get("human_deploy_decision") != "approve":
            blockers.append("human_deploy_approval_required")
        if not board.get("deploy_target_environment"):
            blockers.append("deploy_environment_required")
        return GovernedDeployHandoffResult(
            ok=False,
            session_id=lifecycle.session_id,
            blockers=blockers,
            detail="Deploy handoff blocked — human approval, environment, and complete evidence required.",
        )

    handoff = dict(handoff_rows[0])
    handoff["schema_version"] = GOVERNED_DEPLOY_LIFECYCLE_HANDOFF_SCHEMA_VERSION
    handoff["executable"] = GOVERNED_DEPLOY_HANDOFF_EXECUTABLE
    handoff["deploy_authority"] = DEPLOY_AUTHORITY_FIX_210
    handoff["autonomous_deploy_enabled"] = AUTONOMOUS_DEPLOY_ENABLED_FIX_210
    handoff["workflow_execution_performed"] = WORKFLOW_EXECUTION_PERFORMED_FIX_210

    return GovernedDeployHandoffResult(
        ok=True,
        session_id=lifecycle.session_id,
        deploy_handoff=handoff,
        detail="GitHub Actions deployment request artifact prepared — human must dispatch workflow.",
    )

# SPDX-License-Identifier: Apache-2.0
"""FIX 200 — governed merge lifecycle service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_200_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_contract import (
    APPROVAL_BYPASS_ENABLED_FIX_200,
    AUTONOMOUS_MERGE_ENABLED_FIX_200,
    DEPLOY_AUTHORITY_FIX_200,
    EXECUTION_PERFORMED_FIX_200,
    FORBIDDEN_MERGE_LIFECYCLE_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_200,
    GOVERNANCE_MUTATION_PERFORMED_FIX_200,
    GOVERNED_MERGE_HANDOFF_EXECUTABLE,
    GOVERNED_MERGE_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_200,
    GOVERNED_MERGE_LIFECYCLE_FIX,
    GOVERNED_MERGE_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
    GOVERNED_MERGE_LIFECYCLE_INVARIANT,
    GOVERNED_MERGE_LIFECYCLE_PRINCIPLES,
    GOVERNED_MERGE_LIFECYCLE_SCHEMA_VERSION,
    HIDDEN_MERGE_PATH_ENABLED_FIX_200,
    MERGE_AUTHORITY_FIX_200,
    MERGE_DECISION_KINDS,
    MERGE_EXECUTION_PERFORMED_FIX_200,
    MERGE_LIFECYCLE_STAGES,
    MERGE_RECOMMENDATIONS,
    MUTATION_PERFORMED_FIX_200,
    PROVIDER_AUTHORITY_FIX_200,
    RAILWAY_AUTHORITY_FIX_200,
    REQUIRED_MERGE_EVIDENCE_IDS,
    SUPPORTED_MERGE_ADAPTERS,
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
from aethos_core.software_delivery.github_pr_preflight_store import github_pr_creation_approved_for_plan
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.workspace_verification_store import (
    load_workspace_verification_for_plan,
    workspace_verification_passed,
)


@dataclass(frozen=True)
class GovernedMergeLifecycleResult:
    ok: bool
    session_id: str
    governed_merge_lifecycle: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class GovernedMergeHandoffResult:
    ok: bool
    session_id: str
    merge_handoff: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _agent_receipts(*, session_id: str, plan_id: str) -> list[dict[str, Any]]:
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        list_agent_execution_receipts,
    )

    return list_agent_execution_receipts(session_id=session_id, plan_id=plan_id) or list_agent_execution_receipts(
        session_id=session_id, plan_id=None
    )


def _receipt_for_role(receipts: list[dict[str, Any]], role_id: str) -> dict[str, Any] | None:
    for receipt in receipts:
        meta = dict(receipt.get("metadata") or {})
        if str(meta.get("agent_role_id") or "") == role_id:
            return receipt
    return None


def _alignment_evidence(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
        list_issue_intent_alignment_records,
    )

    records = list_issue_intent_alignment_records(session_id=session_id)
    score = None
    for record in records:
        meta = record.get("metadata") or {}
        if meta.get("alignment_score") is not None:
            score = int(meta.get("alignment_score"))
        elif record.get("alignment_score") is not None:
            score = int(record.get("alignment_score"))
    return {
        "alignment_record_count": len(records),
        "alignment_score": score,
        "alignment_ok": bool(records) or score is not None,
        "read_only": True,
    }


def _required_evidence(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    session_id: str,
    verification: dict[str, Any] | None,
    pr_open: dict[str, Any] | None,
    human_decision: str | None,
) -> dict[str, Any]:
    receipts = _agent_receipts(session_id=session_id, plan_id=plan_id)
    diff_audit = _receipt_for_role(receipts, "diff_audit_agent")
    verification_agent = _receipt_for_role(receipts, "verification_agent")
    risk_agent = _receipt_for_role(receipts, "risk_agent")
    risk_assessment = dict((plan or {}).get("risk_assessment") or {})

    items = {
        "issue_reference": {
            "present": bool(plan and plan.get("issue_reference")),
            "value": (plan or {}).get("issue_reference"),
        },
        "plan_reference": {
            "present": bool(plan_id),
            "value": plan_id,
        },
        "verification_evidence": {
            "present": workspace_verification_passed(plan_id=plan_id),
            "verification_id": (verification or {}).get("verification_id"),
            "status": (verification or {}).get("status"),
        },
        "diff_audit_evidence": {
            "present": diff_audit is not None,
            "receipt_id": diff_audit.get("record_id") if diff_audit else None,
        },
        "risk_assessment": {
            "present": bool(risk_assessment or risk_agent),
            "risk_tier": risk_assessment.get("risk_tier"),
            "risk_agent_receipt": risk_agent.get("record_id") if risk_agent else None,
        },
        "human_approval_record": {
            "present": human_decision == "approve",
            "decision": human_decision,
        },
    }
    missing_all = [key for key in REQUIRED_MERGE_EVIDENCE_IDS if not items[key]["present"]]
    missing_for_recommendation = [
        key for key in missing_all if key != "human_approval_record"
    ]
    return {
        "evidence_id": "required-merge-evidence",
        "items": items,
        "missing_evidence": missing_all,
        "missing_evidence_for_recommendation": missing_for_recommendation,
        "evidence_complete_for_recommendation": len(missing_for_recommendation) == 0,
        "evidence_complete_for_handoff": len(missing_all) == 0,
        "verification_agent_receipt": verification_agent.get("record_id") if verification_agent else None,
        "read_only": True,
    }


def _merge_readiness_assessment(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    session_id: str,
    verification: dict[str, Any] | None,
    pr_open: dict[str, Any] | None,
    human_decision: str | None,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not plan:
        blockers.append("no_issue_plan")
    if not github_pr_open_completed_for_plan(plan_id=plan_id):
        blockers.append("pr_open_not_complete")
    if not workspace_verification_passed(plan_id=plan_id):
        blockers.append("verification_not_passed")
    if not github_pr_creation_approved_for_plan(plan_id=plan_id):
        blockers.append("pr_preflight_not_approved")

    alignment = _alignment_evidence(session_id=session_id)
    if not alignment["alignment_ok"]:
        blockers.append("alignment_evidence_missing")

    evidence = _required_evidence(
        plan=plan,
        plan_id=plan_id,
        session_id=session_id,
        verification=verification,
        pr_open=pr_open,
        human_decision=human_decision,
    )
    if evidence["missing_evidence_for_recommendation"]:
        blockers.append("required_evidence_incomplete")

    if human_decision == "reject":
        blockers.append("human_merge_rejected")
    elif human_decision == "hold":
        blockers.append("human_merge_on_hold")

    readiness_score = 100
    readiness_score -= len(blockers) * 12
    readiness_score = max(0, min(100, readiness_score))

    return {
        "assessment_id": "merge-readiness",
        "readiness_score": readiness_score,
        "pr_open_complete": github_pr_open_completed_for_plan(plan_id=plan_id),
        "pr_url": (pr_open or {}).get("pr_url"),
        "pr_number": (pr_open or {}).get("pr_number"),
        "verification_passed": workspace_verification_passed(plan_id=plan_id),
        "alignment_status": alignment,
        "approval_status": {
            "pr_preflight_approved": github_pr_creation_approved_for_plan(plan_id=plan_id),
            "human_merge_decision": human_decision,
        },
        "outstanding_blockers": blockers,
        "required_evidence": evidence,
        "merge_ready_for_review": not blockers or (
            len(blockers) == 1 and blockers[0] == "human_merge_on_hold"
        ),
        "read_only": True,
    }


def _merge_review_package(
    *,
    plan: dict[str, Any] | None,
    plan_id: str,
    session_id: str,
    readiness: dict[str, Any],
) -> dict[str, Any]:
    receipts = _agent_receipts(session_id=session_id, plan_id=plan_id)
    risk = dict((plan or {}).get("risk_assessment") or {})
    return {
        "packet_id": "merge-review-packet",
        "change_summary": {
            "issue_reference": (plan or {}).get("issue_reference"),
            "plan_id": plan_id,
            "summary": (plan or {}).get("implementation_summary") or (plan or {}).get("title"),
        },
        "risk_summary": {
            "risk_tier": risk.get("risk_tier"),
            "blast_radius": risk.get("blast_radius"),
        },
        "blast_radius_summary": {
            "affected_files": list((plan or {}).get("affected_files") or []),
            "blast_radius": risk.get("blast_radius"),
        },
        "verification_evidence": readiness.get("required_evidence", {}).get("items", {}).get(
            "verification_evidence"
        ),
        "agent_execution_evidence": {
            "receipt_count": len(receipts),
            "roles_present": sorted(
                {
                    str((r.get("metadata") or {}).get("agent_role_id") or "")
                    for r in receipts
                    if (r.get("metadata") or {}).get("agent_role_id")
                }
            ),
        },
        "alignment_evidence": readiness.get("alignment_status"),
        "read_only": True,
    }


def _merge_recommendation(
    *,
    readiness: dict[str, Any],
    human_decision: str | None,
) -> dict[str, Any]:
    blockers = list(readiness.get("outstanding_blockers") or [])
    evidence = readiness.get("required_evidence") or {}
    missing = list(evidence.get("missing_evidence") or [])

    if human_decision == "reject":
        recommendation = "REJECT"
        rationale = "Human merge decision recorded as reject."
    elif human_decision == "hold":
        recommendation = "HOLD"
        rationale = "Human merge decision recorded as hold."
    elif missing_for_recommendation := list(evidence.get("missing_evidence_for_recommendation") or []):
        recommendation = "HOLD"
        rationale = f"Required evidence missing: {', '.join(missing_for_recommendation)}"
    elif blockers:
        recommendation = "CONDITIONAL_APPROVAL" if len(blockers) <= 2 else "HOLD"
        rationale = f"Outstanding blockers: {', '.join(blockers)}"
    elif human_decision == "approve":
        recommendation = "APPROVE_FOR_REVIEW"
        rationale = "Evidence complete and human merge approval recorded — ready for handoff preparation."
    else:
        recommendation = "APPROVE_FOR_REVIEW" if readiness.get("merge_ready_for_review") else "HOLD"
        rationale = "Automated readiness assessment — human merge decision still required for handoff."

    return {
        "recommendation_id": "merge-recommendation",
        "recommendation": recommendation,
        "valid_recommendations": list(MERGE_RECOMMENDATIONS),
        "rationale": rationale,
        "recommendation_only": True,
        "merge_authority": False,
        "read_only": True,
    }


def _merge_execution_adapter(*, pr_open: dict[str, Any] | None, plan_id: str) -> dict[str, Any]:
    pr_number = (pr_open or {}).get("pr_number")
    pr_url = (pr_open or {}).get("pr_url")
    repo = str((pr_open or {}).get("repository") or (pr_open or {}).get("repo") or "")
    return {
        "adapter_id": "github-pull-request-merge",
        "provider": "github",
        "supported_adapters": list(SUPPORTED_MERGE_ADAPTERS),
        "repository": repo,
        "plan_id": plan_id,
        "pr_number": pr_number,
        "pr_url": pr_url,
        "command_template": f"gh pr merge {pr_number} --merge" if pr_number else None,
        "api_operation": "merge_pull_request",
        "executable": False,
        "merge_authority": False,
        "requires_human_execution": True,
        "autonomous_merge_enabled": False,
        "read_only": True,
    }


def _merge_handoff_artifact(
    *,
    plan_id: str,
    session_id: str,
    readiness: dict[str, Any],
    recommendation: dict[str, Any],
    adapter: dict[str, Any],
    human_decision: str | None,
) -> dict[str, Any] | None:
    if human_decision != "approve":
        return None
    if not readiness.get("required_evidence", {}).get("evidence_complete_for_handoff"):
        return None
    if recommendation.get("recommendation") not in {"APPROVE_FOR_REVIEW", "CONDITIONAL_APPROVAL"}:
        return None

    return {
        "handoff_id": f"merge-handoff-{plan_id}",
        "plan_id": plan_id,
        "session_id": session_id,
        "audit_linkage": {
            "timeline_ref": timeline_link_ref(
                lane="software_delivery",
                action="merge_handoff",
                timestamp=plan_id,
            ),
            "replay_key": replay_link_key(
                source="governed_merge_lifecycle",
                lane="merge_handoff",
                action=plan_id,
            ),
        },
        "evidence_references": readiness.get("required_evidence"),
        "merge_execution_adapter": adapter,
        "handoff_executable": False,
        "merge_execution_performed": False,
        "detail": "Merge handoff artifact — human must execute merge outside autonomous path.",
        "read_only": True,
    }


def build_governed_merge_lifecycle(*, session_id: str) -> GovernedMergeLifecycleResult:
    sid = (session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "")
    verification = load_workspace_verification_for_plan(plan_id=plan_id) if plan_id else None
    pr_open = load_github_pr_open_for_plan(plan_id=plan_id) if plan_id else None
    human_decision = merge_decision_status(session_id=sid, plan_id=plan_id or None)
    operator_records = list_governed_merge_lifecycle_records(session_id=sid, plan_id=plan_id or None)

    blockers: list[str] = []
    if not plan:
        blockers.append("no_issue_plan_for_session")
    if plan_id and not github_pr_open_completed_for_plan(plan_id=plan_id):
        blockers.append("pr_open_not_complete")

    readiness = _merge_readiness_assessment(
        plan=plan,
        plan_id=plan_id,
        session_id=sid,
        verification=verification,
        pr_open=pr_open,
        human_decision=human_decision,
    )
    review_packet = _merge_review_package(
        plan=plan,
        plan_id=plan_id,
        session_id=sid,
        readiness=readiness,
    )
    recommendation = _merge_recommendation(readiness=readiness, human_decision=human_decision)
    adapter = _merge_execution_adapter(pr_open=pr_open, plan_id=plan_id)
    handoff = _merge_handoff_artifact(
        plan_id=plan_id,
        session_id=sid,
        readiness=readiness,
        recommendation=recommendation,
        adapter=adapter,
        human_decision=human_decision,
    )

    sections = {
        "merge_readiness_assessment": [readiness],
        "merge_review_package": [review_packet],
        "merge_recommendation": [recommendation],
        "human_merge_decisions": [
            {**r, "read_only": True}
            for r in operator_records
            if str(r.get("kind") or "") in MERGE_DECISION_KINDS
        ],
        "merge_handoff_artifact": [handoff] if handoff else [],
        "merge_execution_adapter": [adapter],
        "post_merge_audit": [
            {
                "audit_id": "post-merge-audit-placeholder",
                "performed": False,
                "detail": "Post-merge audit available after human merge execution — AethOS does not merge autonomously.",
                "read_only": True,
            }
        ],
        "forbidden_merge_lifecycle_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_MERGE_LIFECYCLE_ACTIONS
        ],
        "operator_merge_records": [{**r, "read_only": True} for r in operator_records],
    }

    payload: dict[str, Any] = {
        "schema_version": GOVERNED_MERGE_LIFECYCLE_SCHEMA_VERSION,
        "fix": GOVERNED_MERGE_LIFECYCLE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_200,
        "execution_performed": EXECUTION_PERFORMED_FIX_200,
        "merge_execution_performed": MERGE_EXECUTION_PERFORMED_FIX_200,
        "merge_lifecycle_compose_evidence_only": GOVERNED_MERGE_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_200,
        "merge_authority": MERGE_AUTHORITY_FIX_200,
        "autonomous_merge_enabled": AUTONOMOUS_MERGE_ENABLED_FIX_200,
        "approval_bypass_enabled": APPROVAL_BYPASS_ENABLED_FIX_200,
        "hidden_merge_path_enabled": HIDDEN_MERGE_PATH_ENABLED_FIX_200,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_200,
        "railway_authority": RAILWAY_AUTHORITY_FIX_200,
        "provider_authority": PROVIDER_AUTHORITY_FIX_200,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_200,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_200,
        "invariant": GOVERNED_MERGE_LIFECYCLE_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id or None,
        "lifecycle_stages": list(MERGE_LIFECYCLE_STAGES),
        "current_stage": "merge_review" if github_pr_open_completed_for_plan(plan_id=plan_id) else "pr_open",
        "human_merge_decision": human_decision,
        "sections": sections,
        "merge_record_count": len(operator_records),
        "fix_200_certification_requirements": list(FIX_200_CERTIFICATION_REQUIREMENTS),
        "governed_merge_lifecycle_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_MERGE_LIFECYCLE_PRINCIPLES
        ],
        "sources": {
            "composes_software_delivery_pr_open": True,
            "composes_verification_and_alignment": True,
            "composes_fix_189_agent_receipts": True,
            "autonomous_merge_performed": False,
        },
    }

    return GovernedMergeLifecycleResult(
        ok=True,
        session_id=sid,
        governed_merge_lifecycle=payload,
        blockers=blockers,
        detail="Governed merge lifecycle assembled (merge_authority ≠ autonomous_merge).",
    )


def prepare_governed_merge_handoff(*, session_id: str) -> GovernedMergeHandoffResult:
    lifecycle = build_governed_merge_lifecycle(session_id=session_id)
    board = lifecycle.governed_merge_lifecycle
    handoff_rows = (board.get("sections") or {}).get("merge_handoff_artifact") or []
    blockers: list[str] = list(lifecycle.blockers)

    if not handoff_rows:
        blockers.append("merge_handoff_not_ready")
        if board.get("human_merge_decision") != "approve":
            blockers.append("human_merge_approval_required")
        return GovernedMergeHandoffResult(
            ok=False,
            session_id=lifecycle.session_id,
            blockers=blockers,
            detail="Merge handoff blocked — human approval and complete evidence required.",
        )

    handoff = dict(handoff_rows[0])
    handoff["schema_version"] = GOVERNED_MERGE_LIFECYCLE_HANDOFF_SCHEMA_VERSION
    handoff["executable"] = GOVERNED_MERGE_HANDOFF_EXECUTABLE
    handoff["merge_authority"] = MERGE_AUTHORITY_FIX_200
    handoff["autonomous_merge_enabled"] = AUTONOMOUS_MERGE_ENABLED_FIX_200

    return GovernedMergeHandoffResult(
        ok=True,
        session_id=lifecycle.session_id,
        merge_handoff=handoff,
        detail="Merge execution request artifact prepared — human must execute merge.",
    )

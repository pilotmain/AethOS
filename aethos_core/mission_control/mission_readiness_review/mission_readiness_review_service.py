# SPDX-License-Identifier: Apache-2.0
"""FIX 147 — structured mission readiness review from orchestration cognition."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload
from aethos_core.mission_control.governance_insights.governance_insights_service import build_governance_insights
from aethos_core.mission_control.mission_orchestration.mission_orchestration_service import build_mission_orchestration
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_contract import (
    AUTONOMOUS_GO_NO_GO_EXECUTION_ENABLED_FIX_147,
    AUTONOMOUS_READINESS_DECISION_ENABLED_FIX_147,
    EXECUTION_AUTHORITY_DELEGATED_FIX_147,
    HUMAN_REVIEW_REQUIRED_FIX_147,
    MISSION_READINESS_REVIEW_FIX,
    MISSION_READINESS_REVIEW_INVARIANT,
    MISSION_READINESS_REVIEW_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_147,
    READINESS_RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.rerun_planning.rerun_plan_service import build_governed_rerun_plan


@dataclass(frozen=True)
class MissionReadinessReviewResult:
    ok: bool
    session_id: str
    review: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _decision_rec(*, kind: str, decision: str, rationale: str = "", **extra: Any) -> dict[str, Any]:
    return {
        "kind": kind,
        "decision": decision,
        "rationale": rationale,
        "executable": READINESS_RECOMMENDATION_EXECUTABLE,
        "human_review_required": HUMAN_REVIEW_REQUIRED_FIX_147,
        "read_only": True,
        **extra,
    }


def _readiness_score_summary(*, orchestration: dict[str, Any]) -> dict[str, Any]:
    readiness = ((orchestration.get("sections") or {}).get("orchestration_readiness_scoring") or {})
    health = ((orchestration.get("sections") or {}).get("cross_lane_mission_health") or {})
    return {
        "readiness_score": readiness.get("readiness_score"),
        "readiness_label": readiness.get("readiness_label"),
        "factors": readiness.get("factors", {}),
        "cross_lane_overall": health.get("overall"),
        "pending_gates": health.get("pending_gates", 0),
        "open_incidents": health.get("open_incidents", 0),
        "read_only": True,
    }


def _list_blockers(*, orchestration: dict[str, Any]) -> list[dict[str, Any]]:
    blocked = list((orchestration.get("sections") or {}).get("blocked_by_relationships") or [])
    return [
        {
            "blocker_id": f"blocker-{idx + 1}",
            "blocked_entity": row.get("blocked_entity"),
            "blocked_by": row.get("blocked_by"),
            "priority": row.get("priority", "medium"),
            "read_only": True,
        }
        for idx, row in enumerate(blocked)
    ]


def _list_pending_approvals(*, inbox: dict[str, Any]) -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    for item in inbox.get("items") or []:
        if item.get("status") != "pending":
            continue
        pending.append(
            {
                "inbox_id": item.get("inbox_id"),
                "gate_id": item.get("gate_id"),
                "severity": item.get("severity"),
                "ui_approval_eligible": item.get("ui_approval_eligible"),
                "required_phrases": item.get("required_phrases") or [],
                "human_review_required": True,
                "read_only": True,
            }
        )
    return pending


def _list_evidence_gaps(*, insights: dict[str, Any], orchestration: dict[str, Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for row in ((insights.get("insights") or {}).get("verification_gaps") or []):
        gaps.append(
            {
                "gap": row.get("insight"),
                "severity": row.get("severity", "medium"),
                "source": "governance_insights",
                "read_only": True,
            }
        )

    sources = orchestration.get("sources") or {}
    if not sources.get("rerun_plan"):
        gaps.append(
            {
                "gap": "Governed rerun plan unavailable — replay-derived evidence incomplete for readiness review.",
                "severity": "medium",
                "source": "orchestration",
                "read_only": True,
            }
        )
    if int(sources.get("operational_graph_node_count") or 0) < 3:
        gaps.append(
            {
                "gap": "Thin operational memory graph — export evidence bundle to enrich review context.",
                "severity": "low",
                "source": "operational_memory",
                "read_only": True,
            }
        )
    return gaps[:15]


def _list_rollback_posture(*, rerun_plan: dict[str, Any], insights: dict[str, Any]) -> dict[str, Any]:
    posture = dict(rerun_plan.get("rollback_posture") or {})
    rollback_signals = list(((insights.get("insights") or {}).get("rollback_patterns") or []))
    return {
        "workspace_rollback": posture.get("workspace_rollback", "governed chat phrase required (FIX 125D)"),
        "autonomous_rollback": posture.get("autonomous_rollback", "forbidden"),
        "snapshot_required": posture.get("snapshot_required", "mandatory per phase 2 freeze"),
        "rollback_escalation_signals": len(rollback_signals),
        "rollback_patterns": [
            {"insight": r.get("insight"), "severity": r.get("severity"), "read_only": True}
            for r in rollback_signals[:5]
        ],
        "live_rollback_from_mission_control": False,
        "read_only": True,
    }


def _list_incident_exposure(*, orchestration: dict[str, Any]) -> dict[str, Any]:
    health = ((orchestration.get("sections") or {}).get("cross_lane_mission_health") or {})
    open_incidents = int(health.get("open_incidents") or 0)
    incident_lane = ((health.get("lanes") or {}).get("incident_command") or {})
    return {
        "open_incidents": open_incidents,
        "exposure_label": "elevated" if open_incidents else "none_observed",
        "incident_lane_status": incident_lane.get("status"),
        "production_impact_risk": "high" if open_incidents >= 1 else "low",
        "read_only": True,
    }


def _recommended_operator_decisions(
    *,
    orchestration: dict[str, Any],
    pending_approvals: list[dict[str, Any]],
    evidence_gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []

    for rec in (orchestration.get("orchestration_recommendations") or [])[:6]:
        decisions.append(
            _decision_rec(
                kind="operator_decision",
                decision=str(rec.get("recommendation") or ""),
                rationale=str(rec.get("rationale") or "From FIX 146 orchestration cognition."),
                priority=rec.get("priority", "medium"),
            )
        )

    for approval in pending_approvals[:4]:
        gate = approval.get("gate_id")
        decisions.append(
            _decision_rec(
                kind="approval_decision",
                decision=f"Human review required: approve or defer gate `{gate}` via governed chat.",
                rationale="Pending approval blocks downstream orchestration readiness.",
                priority=approval.get("severity", "medium"),
                gate_id=gate,
            )
        )

    high_gaps = [g for g in evidence_gaps if g.get("severity") in {"high", "critical"}]
    if high_gaps:
        decisions.append(
            _decision_rec(
                kind="evidence_decision",
                decision="Collect missing verification evidence before advancing mission stages.",
                rationale=f"{len(high_gaps)} high-severity evidence gap(s) identified.",
                priority="high",
            )
        )

    return decisions[:12]


def _go_no_go_hold_recommendation(
    *,
    score_summary: dict[str, Any],
    blockers: list[dict[str, Any]],
    pending_approvals: list[dict[str, Any]],
    incident_exposure: dict[str, Any],
    evidence_gaps: list[dict[str, Any]],
) -> dict[str, Any]:
    score = float(score_summary.get("readiness_score") or 0)
    critical_blocks = len([b for b in blockers if b.get("priority") == "critical"])
    open_incidents = int(incident_exposure.get("open_incidents") or 0)
    high_gaps = len([g for g in evidence_gaps if g.get("severity") in {"high", "critical"}])

    if open_incidents >= 1 or critical_blocks >= 1 or score < 0.45:
        recommendation = "no-go"
        rationale = "Open incident(s), critical blocker(s), or low readiness score — defer advancement."
    elif score >= 0.75 and not pending_approvals and high_gaps == 0:
        recommendation = "go"
        rationale = "Readiness score elevated with no pending approvals or high-severity evidence gaps."
    else:
        recommendation = "hold"
        rationale = "Mission partially ready — resolve pending approvals, blockers, or evidence gaps before proceeding."

    return {
        "recommendation": recommendation,
        "rationale": rationale,
        "readiness_score": score,
        "pending_approval_count": len(pending_approvals),
        "blocker_count": len(blockers),
        "open_incidents": open_incidents,
        "executable": READINESS_RECOMMENDATION_EXECUTABLE,
        "human_review_required": HUMAN_REVIEW_REQUIRED_FIX_147,
        "advisory_only": True,
        "read_only": True,
    }


def build_mission_readiness_review(*, session_id: str) -> MissionReadinessReviewResult:
    sid = (session_id or "default").strip()[:64] or "default"

    orchestration_result = build_mission_orchestration(session_id=sid)
    orchestration = orchestration_result.orchestration if orchestration_result.ok else {}

    inbox = approval_inbox_payload(session_id=sid)

    insights_result = build_governance_insights(session_id=sid)
    insights = insights_result.insights if insights_result.ok else {}

    rerun_result = build_governed_rerun_plan(session_id=sid)
    rerun_plan = rerun_result.plan if rerun_result.ok else {}

    score_summary = _readiness_score_summary(orchestration=orchestration)
    blockers = _list_blockers(orchestration=orchestration)
    pending_approvals = _list_pending_approvals(inbox=inbox)
    evidence_gaps = _list_evidence_gaps(insights=insights, orchestration=orchestration)
    rollback_posture = _list_rollback_posture(rerun_plan=rerun_plan, insights=insights)
    incident_exposure = _list_incident_exposure(orchestration=orchestration)
    operator_decisions = _recommended_operator_decisions(
        orchestration=orchestration,
        pending_approvals=pending_approvals,
        evidence_gaps=evidence_gaps,
    )
    go_recommendation = _go_no_go_hold_recommendation(
        score_summary=score_summary,
        blockers=blockers,
        pending_approvals=pending_approvals,
        incident_exposure=incident_exposure,
        evidence_gaps=evidence_gaps,
    )

    sections = {
        "readiness_score_summary": score_summary,
        "blockers": blockers,
        "pending_approvals": pending_approvals,
        "evidence_gaps": evidence_gaps,
        "rollback_posture": rollback_posture,
        "incident_exposure": incident_exposure,
        "recommended_operator_decisions": operator_decisions,
        "go_no_go_hold_recommendation": go_recommendation,
    }

    review: dict[str, Any] = {
        "schema_version": MISSION_READINESS_REVIEW_SCHEMA_VERSION,
        "fix": MISSION_READINESS_REVIEW_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_147,
        "human_review_required": HUMAN_REVIEW_REQUIRED_FIX_147,
        "autonomous_go_no_go_execution_enabled": AUTONOMOUS_GO_NO_GO_EXECUTION_ENABLED_FIX_147,
        "autonomous_readiness_decision_enabled": AUTONOMOUS_READINESS_DECISION_ENABLED_FIX_147,
        "execution_authority_delegated": EXECUTION_AUTHORITY_DELEGATED_FIX_147,
        "invariant": MISSION_READINESS_REVIEW_INVARIANT,
        "session_id": sid,
        "plan_id": orchestration.get("plan_id"),
        "correlation_id": orchestration.get("correlation_id"),
        "sections": sections,
        "go_no_go_hold": go_recommendation.get("recommendation"),
        "recommendation_count": len(operator_decisions),
        "all_recommendations_executable": False,
        "sources": {
            "mission_orchestration": orchestration_result.ok,
            "approval_inbox": bool(inbox),
            "governance_insights": insights_result.ok,
            "rerun_plan": rerun_result.ok,
        },
    }
    return MissionReadinessReviewResult(
        ok=True,
        session_id=sid,
        review=review,
        detail="Mission readiness review board assembled (advisory only — human review required).",
    )

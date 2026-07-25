# SPDX-License-Identifier: Apache-2.0
"""FIX 146 — mission-level orchestration cognition across lanes (read-only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload
from aethos_core.mission_control.cross_lane.cross_lane_contract import OBSERVED_LANES
from aethos_core.mission_control.cross_lane.snapshot_service import build_mission_control_snapshot
from aethos_core.mission_control.governance_insights.governance_insights_service import build_governance_insights
from aethos_core.mission_control.mission_orchestration.mission_orchestration_contract import (
    AUTONOMOUS_APPROVAL_BATCHING_ENABLED_FIX_146,
    AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146,
    AUTONOMOUS_PROMOTION_DEPLOY_ENABLED_FIX_146,
    AUTONOMOUS_SEQUENCING_EXECUTION_ENABLED_FIX_146,
    MISSION_ORCHESTRATION_FIX,
    MISSION_ORCHESTRATION_INVARIANT,
    MISSION_ORCHESTRATION_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_146,
    ORCHESTRATION_RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.mission_strategy.mission_strategy_service import build_mission_strategy
from aethos_core.mission_control.operational_memory.operational_memory_service import build_operational_memory_graph
from aethos_core.mission_control.rerun_planning.rerun_plan_service import build_governed_rerun_plan
from aethos_core.software_delivery.software_delivery_phase_2_contract import SOFTWARE_DELIVERY_LOOP_ORDER

_GATE_TO_STAGE: dict[str, str] = {
    "issue_plan": "issue_intake",
    "planning_approved": "implementation_plan",
    "workspace_verification": "workspace_verify",
    "github_preflight_approved": "github_pr_preflight",
    "branch_push_completed": "branch_push",
    "github_pr_opened": "pr_open",
}


@dataclass(frozen=True)
class MissionOrchestrationResult:
    ok: bool
    session_id: str
    orchestration: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _rec(*, kind: str, recommendation: str, rationale: str = "", priority: str = "medium", **extra: Any) -> dict[str, Any]:
    return {
        "kind": kind,
        "recommendation": recommendation,
        "rationale": rationale,
        "priority": priority,
        "executable": ORCHESTRATION_RECOMMENDATION_EXECUTABLE,
        "read_only": True,
        **extra,
    }


def _mission_dependency_graph(*, snapshot: dict[str, Any], rerun_plan: dict[str, Any]) -> dict[str, Any]:
    plan_id = str(snapshot.get("plan_id") or "")
    correlation_id = str(snapshot.get("correlation_id") or "")
    nodes: list[dict[str, Any]] = [
        {"id": "mission_root", "kind": "mission", "plan_id": plan_id, "correlation_id": correlation_id},
    ]
    edges: list[dict[str, Any]] = []

    for lane in OBSERVED_LANES:
        lane_data = ((snapshot.get("lanes") or {}).get(lane) or {})
        nodes.append(
            {
                "id": f"lane:{lane}",
                "kind": "lane",
                "lane": lane,
                "ok": lane_data.get("ok"),
                "read_only": True,
            }
        )
        edges.append({"from": "mission_root", "to": f"lane:{lane}", "kind": "observes", "read_only": True})

    sd = ((snapshot.get("lanes") or {}).get("software_delivery") or {})
    for gate in sd.get("governance_gates") or []:
        gate_id = str(gate.get("gate") or "")
        node_id = f"gate:{gate_id}"
        nodes.append(
            {
                "id": node_id,
                "kind": "gate",
                "gate": gate_id,
                "passed": gate.get("passed"),
                "stage": _GATE_TO_STAGE.get(gate_id),
                "read_only": True,
            }
        )
        edges.append({"from": "lane:software_delivery", "to": node_id, "kind": "governs", "read_only": True})

    prev_stage: str | None = None
    for stage in SOFTWARE_DELIVERY_LOOP_ORDER:
        stage_id = f"stage:{stage}"
        nodes.append({"id": stage_id, "kind": "stage", "stage": stage, "read_only": True})
        if prev_stage:
            edges.append(
                {
                    "from": f"stage:{prev_stage}",
                    "to": stage_id,
                    "kind": "precedes",
                    "read_only": True,
                }
            )
        prev_stage = stage

    for step in (rerun_plan.get("steps") or [])[:8]:
        step_id = str(step.get("step_id") or step.get("action") or "")
        if step_id:
            nodes.append(
                {
                    "id": f"replay:{step_id}",
                    "kind": "replay_step",
                    "action": step.get("action"),
                    "read_only": True,
                }
            )

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes[:40],
        "edges": edges[:40],
        "read_only": True,
    }


def _governed_stage_orchestration(*, snapshot: dict[str, Any], rerun_plan: dict[str, Any]) -> dict[str, Any]:
    sd = ((snapshot.get("lanes") or {}).get("software_delivery") or {})
    passed_gates = {str(g.get("gate")) for g in (sd.get("governance_gates") or []) if g.get("passed")}
    current_stage = "issue_intake"
    for gate, stage in _GATE_TO_STAGE.items():
        if gate in passed_gates:
            current_stage = stage

    stage_index = SOFTWARE_DELIVERY_LOOP_ORDER.index(current_stage) if current_stage in SOFTWARE_DELIVERY_LOOP_ORDER else 0
    upcoming = list(SOFTWARE_DELIVERY_LOOP_ORDER[stage_index : stage_index + 4])
    rerun_stage = str((rerun_plan.get("target") or {}).get("stage") or "")

    return {
        "current_stage": current_stage,
        "upcoming_stages": upcoming,
        "rerun_target_stage": rerun_stage or None,
        "plan_status": sd.get("plan_status"),
        "pending_gates": sd.get("pending_gates") or [],
        "governed_only": True,
        "read_only": True,
    }


def _lane_synchronization_visibility(*, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    lanes = snapshot.get("lanes") or {}
    sd_ok = bool((lanes.get("software_delivery") or {}).get("ok"))
    plan_id = str(snapshot.get("plan_id") or "")
    visibility: list[dict[str, Any]] = []

    for lane in OBSERVED_LANES:
        lane_data = lanes.get(lane) or {}
        synced = bool(lane_data.get("ok"))
        if lane == "software_delivery":
            sync_label = "active" if sd_ok else "idle"
        elif lane in {"multi_agent_collaboration", "route_diagnostics"}:
            sync_label = "linked" if sd_ok else "dormant"
        elif lane == "production_governance":
            sync_label = "aligned" if sd_ok and not (lanes.get("incident_command") or {}).get("open_incidents") else "watch"
        elif lane == "incident_command":
            open_inc = int(lane_data.get("open_incidents") or 0)
            sync_label = "blocked" if open_inc else "clear"
            synced = open_inc == 0
        elif lane == "railway_orchestration":
            sync_label = "posture_observed" if lane_data.get("ok") else "no_journal"
        else:
            sync_label = "observed" if synced else "partial"

        visibility.append(
            {
                "lane": lane,
                "synchronized": synced,
                "sync_label": sync_label,
                "plan_id": plan_id if lane in {"software_delivery", "multi_agent_collaboration"} else None,
                "read_only": True,
            }
        )
    return visibility


def _blocked_by_relationships(*, snapshot: dict[str, Any], inbox: dict[str, Any]) -> list[dict[str, Any]]:
    blocked: list[dict[str, Any]] = []
    for item in snapshot.get("attention_queue") or []:
        blocked.append(
            {
                "blocked_entity": f"lane:{item.get('lane')}",
                "blocked_by": str(item.get("gate") or "unknown_gate"),
                "priority": item.get("priority", "medium"),
                "read_only": True,
            }
        )

    sd = ((snapshot.get("lanes") or {}).get("software_delivery") or {})
    for gate in sd.get("pending_gates") or []:
        blocked.append(
            {
                "blocked_entity": "stage:software_delivery",
                "blocked_by": f"gate:{gate}",
                "priority": "high" if gate in {"workspace_verification", "github_preflight_approved"} else "medium",
                "read_only": True,
            }
        )

    open_incidents = int(((snapshot.get("lanes") or {}).get("incident_command") or {}).get("open_incidents") or 0)
    if open_incidents:
        blocked.append(
            {
                "blocked_entity": "mission:rollout_posture",
                "blocked_by": "incident_command:open_incidents",
                "priority": "critical",
                "count": open_incidents,
                "read_only": True,
            }
        )

    for item in inbox.get("items") or []:
        if item.get("status") == "pending":
            blocked.append(
                {
                    "blocked_entity": f"approval:{item.get('inbox_id')}",
                    "blocked_by": f"gate:{item.get('gate_id')}",
                    "priority": item.get("severity", "medium"),
                    "ui_approval_eligible": item.get("ui_approval_eligible"),
                    "read_only": True,
                }
            )
    return blocked[:20]


def _upstream_downstream_effects(*, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    effects: list[dict[str, Any]] = []
    sd_pending = list(((snapshot.get("lanes") or {}).get("software_delivery") or {}).get("pending_gates") or [])

    if sd_pending:
        effects.append(
            {
                "upstream": "software_delivery",
                "downstream": "production_governance",
                "effect": "pending_delivery_gates_delay_rollout_visibility",
                "detail": f"{len(sd_pending)} pending gate(s) upstream.",
                "read_only": True,
            }
        )
        effects.append(
            {
                "upstream": "software_delivery",
                "downstream": "railway_orchestration",
                "effect": "infra_orchestration_waits_for_human_review_boundary",
                "detail": "Software delivery must reach human_review before infra lane advances.",
                "read_only": True,
            }
        )

    if (snapshot.get("lanes") or {}).get("incident_command", {}).get("open_incidents"):
        effects.append(
            {
                "upstream": "incident_command",
                "downstream": "production_governance",
                "effect": "open_incident_supersedes_promotion_posture",
                "detail": "Incident command signals should be resolved before rollout advance.",
                "read_only": True,
            }
        )

    agents = (snapshot.get("lanes") or {}).get("multi_agent_collaboration") or {}
    if agents.get("active_agents"):
        effects.append(
            {
                "upstream": "multi_agent_collaboration",
                "downstream": "software_delivery",
                "effect": "agent_collaboration_accelerates_plan_stages",
                "detail": f"{agents.get('active_agents')} active agent(s) linked to plan.",
                "read_only": True,
            }
        )

    if not effects:
        effects.append(
            {
                "upstream": "mission_root",
                "downstream": "all_lanes",
                "effect": "no_blocking_upstream_effects",
                "detail": "No critical upstream/downstream blockers detected.",
                "read_only": True,
            }
        )
    return effects


def _orchestration_readiness_score(
    *,
    snapshot: dict[str, Any],
    blocked: list[dict[str, Any]],
    strategy: dict[str, Any],
) -> dict[str, Any]:
    health = snapshot.get("execution_health") or {}
    pending_gates = int(health.get("software_delivery_pending_gates") or 0)
    open_incidents = int(health.get("open_incidents") or 0)
    critical_blocks = len([b for b in blocked if b.get("priority") == "critical"])
    risk = ((strategy.get("sections") or {}).get("organizational_risk_concentration") or {})
    risk_score = float(risk.get("concentration_score") or 0)

    base = 1.0
    base -= min(0.35, pending_gates * 0.07)
    base -= min(0.25, open_incidents * 0.12)
    base -= min(0.2, critical_blocks * 0.1)
    base -= min(0.15, risk_score * 0.2)
    score = round(max(0.0, min(1.0, base)), 3)
    label = "ready" if score >= 0.75 else "partial" if score >= 0.45 else "constrained"

    return {
        "readiness_score": score,
        "readiness_label": label,
        "factors": {
            "pending_gates": pending_gates,
            "open_incidents": open_incidents,
            "critical_blocks": critical_blocks,
            "risk_concentration": risk_score,
        },
        "read_only": True,
    }


def _operator_sequencing_recommendations(
    *,
    stage_orchestration: dict[str, Any],
    blocked: list[dict[str, Any]],
    insights: dict[str, Any],
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    for gate in stage_orchestration.get("pending_gates") or []:
        recs.append(
            _rec(
                kind="sequencing",
                recommendation=f"Sequence governed approval for gate `{gate}` before advancing to next delivery stage.",
                rationale="Stage orchestration shows this gate as pending upstream.",
                priority="high" if gate in {"workspace_verification", "github_preflight_approved"} else "medium",
                gate_id=gate,
            )
        )

    critical = [b for b in blocked if b.get("priority") == "critical"]
    if critical:
        recs.append(
            _rec(
                kind="sequencing",
                recommendation="Resolve open production incident(s) before sequencing rollout or promotion steps.",
                rationale=f"{len(critical)} critical blocked-by relationship(s).",
                priority="critical",
            )
        )

    for item in ((insights.get("insights") or {}).get("approval_bottlenecks") or [])[:3]:
        recs.append(
            _rec(
                kind="sequencing",
                recommendation=f"Prioritize operator attention on approval bottleneck: {item.get('insight')}",
                rationale="Meta-governance insight from FIX 143.",
                priority=item.get("severity", "medium"),
            )
        )

    upcoming = stage_orchestration.get("upcoming_stages") or []
    if upcoming and len(recs) < 4:
        recs.append(
            _rec(
                kind="sequencing",
                recommendation=f"Prepare evidence for upcoming stage `{upcoming[0]}` — review replay and rerun plan first.",
                rationale="Governed stage orchestration projects next loop stage.",
                priority="medium",
                stage=upcoming[0],
            )
        )

    return recs[:12]


def _coordinated_approval_batching_recommendations(*, inbox: dict[str, Any]) -> list[dict[str, Any]]:
    pending = [i for i in (inbox.get("items") or []) if i.get("status") == "pending" and i.get("ui_approval_eligible")]
    if len(pending) < 2:
        return []

    batch_id = f"batch-{len(pending)}-gates"
    gate_ids = [str(i.get("gate_id") or "") for i in pending]
    return [
        _rec(
            kind="approval_batching",
            recommendation=(
                f"Consider reviewing {len(pending)} eligible approvals as a coordinated batch "
                f"(`{batch_id}`) — operator must still approve each gate individually via chat governance."
            ),
            rationale="Multiple UI-eligible gates pending; batching is a review convenience only.",
            priority="medium",
            batch_id=batch_id,
            gate_ids=gate_ids,
            autonomous_batching=False,
        )
    ]


def _cross_lane_mission_health(*, snapshot: dict[str, Any], lane_sync: list[dict[str, Any]]) -> dict[str, Any]:
    lanes = snapshot.get("lanes") or {}
    health = snapshot.get("execution_health") or {}
    per_lane: dict[str, Any] = {}

    for row in lane_sync:
        lane = str(row.get("lane") or "")
        lane_data = lanes.get(lane) or {}
        status = "healthy"
        if row.get("sync_label") == "blocked":
            status = "critical"
        elif not row.get("synchronized"):
            status = "attention"
        per_lane[lane] = {
            "status": status,
            "sync_label": row.get("sync_label"),
            "ok": lane_data.get("ok"),
            "read_only": True,
        }

    return {
        "overall": health.get("overall", "unknown"),
        "lanes": per_lane,
        "open_incidents": health.get("open_incidents", 0),
        "pending_gates": health.get("software_delivery_pending_gates", 0),
        "read_only": True,
    }


def build_mission_orchestration(*, session_id: str) -> MissionOrchestrationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    snapshot_result = build_mission_control_snapshot(session_id=sid)
    snapshot = snapshot_result.snapshot if snapshot_result.ok else {}

    rerun_result = build_governed_rerun_plan(session_id=sid)
    rerun_plan = rerun_result.plan if rerun_result.ok else {}

    inbox = approval_inbox_payload(session_id=sid)

    graph_result = build_operational_memory_graph(session_id=sid)
    graph = graph_result.graph if graph_result.ok else {}

    insights_result = build_governance_insights(session_id=sid)
    insights = insights_result.insights if insights_result.ok else {}

    strategy_result = build_mission_strategy(session_id=sid)
    strategy = strategy_result.strategy if strategy_result.ok else {}

    dependency_graph = _mission_dependency_graph(snapshot=snapshot, rerun_plan=rerun_plan)
    stage_orchestration = _governed_stage_orchestration(snapshot=snapshot, rerun_plan=rerun_plan)
    lane_sync = _lane_synchronization_visibility(snapshot=snapshot)
    blocked = _blocked_by_relationships(snapshot=snapshot, inbox=inbox)
    effects = _upstream_downstream_effects(snapshot=snapshot)
    readiness = _orchestration_readiness_score(snapshot=snapshot, blocked=blocked, strategy=strategy)
    sequencing = _operator_sequencing_recommendations(
        stage_orchestration=stage_orchestration,
        blocked=blocked,
        insights=insights,
    )
    batching = _coordinated_approval_batching_recommendations(inbox=inbox)
    cross_lane_health = _cross_lane_mission_health(snapshot=snapshot, lane_sync=lane_sync)

    sections = {
        "mission_dependency_graph": dependency_graph,
        "governed_stage_orchestration": stage_orchestration,
        "lane_synchronization_visibility": lane_sync,
        "blocked_by_relationships": blocked,
        "upstream_downstream_mission_effects": effects,
        "orchestration_readiness_scoring": readiness,
        "operator_sequencing_recommendations": sequencing,
        "coordinated_approval_batching_recommendations": batching,
        "cross_lane_mission_health": cross_lane_health,
    }

    recs = list(sequencing) + list(batching)

    orchestration: dict[str, Any] = {
        "schema_version": MISSION_ORCHESTRATION_SCHEMA_VERSION,
        "fix": MISSION_ORCHESTRATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_146,
        "autonomous_orchestration_enabled": AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146,
        "autonomous_sequencing_execution_enabled": AUTONOMOUS_SEQUENCING_EXECUTION_ENABLED_FIX_146,
        "autonomous_approval_batching_enabled": AUTONOMOUS_APPROVAL_BATCHING_ENABLED_FIX_146,
        "autonomous_promotion_deploy_enabled": AUTONOMOUS_PROMOTION_DEPLOY_ENABLED_FIX_146,
        "invariant": MISSION_ORCHESTRATION_INVARIANT,
        "session_id": sid,
        "correlation_id": snapshot.get("correlation_id"),
        "plan_id": snapshot.get("plan_id"),
        "sections": sections,
        "orchestration_recommendations": recs,
        "recommendation_count": len(recs),
        "all_recommendations_executable": False,
        "sources": {
            "cross_lane_snapshot": snapshot_result.ok,
            "rerun_plan": rerun_result.ok,
            "approval_inbox": bool(inbox),
            "operational_memory": graph_result.ok,
            "governance_insights": insights_result.ok,
            "mission_strategy": strategy_result.ok,
            "operational_graph_node_count": int((graph.get("graph") or {}).get("stats", {}).get("node_count") or 0),
        },
    }
    return MissionOrchestrationResult(
        ok=True,
        session_id=sid,
        orchestration=orchestration,
        detail="Mission orchestration analysis complete (read-only coordination cognition).",
    )

# SPDX-License-Identifier: Apache-2.0
"""FIX 165 — mission planning multi-agent deliberation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.mission_planning.mission_planning_service import build_mission_planning
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_165,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_165,
    AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165,
    AUTONOMOUS_MERGE_ENABLED_FIX_165,
    AUTONOMOUS_PR_CREATION_ENABLED_FIX_165,
    AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_165,
    BOUNDED_DELIBERATION_AGENT_ROLE_IDS,
    DELIBERATION_AGENT_CATALOG,
    DELIBERATION_PRINCIPLES,
    DELIBERATION_RECOMMENDATION_EXECUTABLE,
    GOVERNANCE_MUTATION_PERFORMED_FIX_165,
    MISSION_PLANNING_DELIBERATION_FIX,
    MISSION_PLANNING_DELIBERATION_INVARIANT,
    MISSION_PLANNING_DELIBERATION_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_165,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_roles import (
    ROLE_RUNNERS,
    run_synthesis_agent,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_store import (
    list_mission_planning_deliberation_records,
)


@dataclass(frozen=True)
class MissionPlanningDeliberationResult:
    ok: bool
    session_id: str
    mission_planning_deliberation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _run_agent_analyses(*, mission_planning: dict[str, Any]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for role_id in BOUNDED_DELIBERATION_AGENT_ROLE_IDS:
        if role_id == "synthesis_agent":
            continue
        runner = ROLE_RUNNERS.get(role_id)
        if not runner:
            continue
        outputs.append(runner(mission_planning=mission_planning))
    outputs.append(run_synthesis_agent(agent_outputs=outputs))
    return outputs


def _section_from_agents(
    *,
    records: list[dict[str, Any]],
    record_kind: str,
    section_key: str,
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, record_kind)]
    role_id = section_key.replace("_analysis", "_agent").replace("_summary", "_agent")
    if section_key == "synthesis_agent_summary":
        role_id = "synthesis_agent"
    agent = next((o for o in agent_outputs if o.get("agent_role_id") == role_id), None)
    if not agent:
        return stored
    generated = {
        "agent_role_id": agent.get("agent_role_id"),
        "title": agent.get("title"),
        "focus": agent.get("focus"),
        "findings": agent.get("findings") or [],
        "recommendations": agent.get("recommendations") or [],
        "executable": False,
        "read_only": True,
    }
    return stored + [generated]


def _multi_agent_deliberation_map(*, agent_outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "role_id": role_id,
            "display_name": display,
            "focus": focus,
            "status": "completed",
            "analysis_only": True,
            "read_only": True,
        }
        for role_id, display, focus in DELIBERATION_AGENT_CATALOG
    ] + [
        {
            "map_id": "deliberation-completeness",
            "agent_output_count": len(agent_outputs),
            "bounded_roles": list(BOUNDED_DELIBERATION_AGENT_ROLE_IDS),
            "executor_agent_enabled": False,
            "read_only": True,
        }
    ]


def _consolidated_recommendation(
    *,
    records: list[dict[str, Any]],
    agent_outputs: list[dict[str, Any]],
    mission_planning: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "deliberation_record")]
    synthesis = next((o for o in agent_outputs if o.get("agent_role_id") == "synthesis_agent"), {})
    artifact = (mission_planning.get("sections") or {}).get("mission_action_plan_artifact") or []
    return stored + [
        {
            "recommendation_id": "consolidated-institutional-deliberation",
            "summary": "; ".join(synthesis.get("findings") or [])[:500] or "Multi-agent deliberation complete.",
            "action_option_count": artifact[0].get("action_option_count") if artifact else 0,
            "human_selection_required": True,
            "auto_path_selected": False,
            "autonomous_execution": False,
            "detail": "Consolidated recommendation for human institutional path selection — not executable.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def _deliberation_integrity_scoring(*, records: list[dict[str, Any]], agent_outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    role_count = len(agent_outputs)
    density = min(len(records) * 2, 10)
    score = max(0, min(100, 70 + role_count * 4 + density))
    label = "deliberated" if score >= 85 else "review_required" if score >= 55 else "fragmented"
    return [
        {
            "score_id": "deliberation-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "agent_roles_completed": role_count,
            "execution_authority": False,
            "detail": "Deliberation integrity scoring is advisory — agents analyze only.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def build_mission_planning_deliberation(*, session_id: str) -> MissionPlanningDeliberationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    planning_result = build_mission_planning(session_id=sid)
    mission_planning = planning_result.mission_planning if planning_result.ok else {}
    plan_id = str(mission_planning.get("plan_id") or "") or None
    correlation_id = str(mission_planning.get("correlation_id") or "") or None

    records = list_mission_planning_deliberation_records(session_id=sid, plan_id=plan_id)
    agent_outputs = _run_agent_analyses(mission_planning=mission_planning)

    sections = {
        "planner_agent_analysis": _section_from_agents(
            records=records,
            record_kind="planner_analysis_note",
            section_key="planner_agent_analysis",
            agent_outputs=agent_outputs,
        ),
        "risk_agent_analysis": _section_from_agents(
            records=records,
            record_kind="risk_analysis_note",
            section_key="risk_agent_analysis",
            agent_outputs=agent_outputs,
        ),
        "constitutional_agent_analysis": _section_from_agents(
            records=records,
            record_kind="constitutional_analysis_note",
            section_key="constitutional_agent_analysis",
            agent_outputs=agent_outputs,
        ),
        "delivery_agent_analysis": _section_from_agents(
            records=records,
            record_kind="delivery_analysis_note",
            section_key="delivery_agent_analysis",
            agent_outputs=agent_outputs,
        ),
        "verification_agent_analysis": _section_from_agents(
            records=records,
            record_kind="verification_analysis_note",
            section_key="verification_agent_analysis",
            agent_outputs=agent_outputs,
        ),
        "synthesis_agent_summary": _section_from_agents(
            records=records,
            record_kind="synthesis_summary_note",
            section_key="synthesis_agent_summary",
            agent_outputs=agent_outputs,
        ),
        "multi_agent_deliberation_map": _multi_agent_deliberation_map(agent_outputs=agent_outputs),
        "consolidated_recommendation": _consolidated_recommendation(
            records=records,
            agent_outputs=agent_outputs,
            mission_planning=mission_planning,
        ),
        "deliberation_integrity_scoring": _deliberation_integrity_scoring(
            records=records, agent_outputs=agent_outputs
        ),
    }

    mission_planning_deliberation: dict[str, Any] = {
        "schema_version": MISSION_PLANNING_DELIBERATION_SCHEMA_VERSION,
        "fix": MISSION_PLANNING_DELIBERATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_165,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_165,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_165,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_165,
        "autonomous_lane_selection_enabled": AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165,
        "autonomous_pr_creation_enabled": AUTONOMOUS_PR_CREATION_ENABLED_FIX_165,
        "autonomous_railway_mutation_enabled": AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_165,
        "autonomous_merge_enabled": AUTONOMOUS_MERGE_ENABLED_FIX_165,
        "invariant": MISSION_PLANNING_DELIBERATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "agent_outputs": agent_outputs,
        "deliberation_record_count": len(records),
        "agent_role_count": len(agent_outputs),
        "all_recommendations_executable": False,
        "mission_planning_deliberation_cognition": True,
        "bounded_multi_agent_deliberation": True,
        "deliberation_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in DELIBERATION_PRINCIPLES
        ],
        "sources": {
            "mission_planning": planning_result.ok,
            "planning_record_count": mission_planning.get("planning_record_count", 0),
            "deliberation_records": len(records),
            "bounded_agent_roles": len(BOUNDED_DELIBERATION_AGENT_ROLE_IDS),
        },
    }
    return MissionPlanningDeliberationResult(
        ok=True,
        session_id=sid,
        mission_planning_deliberation=mission_planning_deliberation,
        detail="Mission planning deliberation assembled (analysis-only — no execution authority).",
    )

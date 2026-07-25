# SPDX-License-Identifier: Apache-2.0
"""FIX 165 — bounded deliberation agent role runners (analysis only)."""

from __future__ import annotations

from typing import Any, Callable

from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_contract import (
    BOUNDED_DELIBERATION_AGENT_ROLE_IDS,
    DELIBERATION_RECOMMENDATION_EXECUTABLE,
)

RoleRunner = Callable[..., dict[str, Any]]


def _base_result(
    *,
    role_id: str,
    title: str,
    focus: str,
    findings: list[str],
    recommendations: list[str],
) -> dict[str, Any]:
    return {
        "agent_role_id": role_id,
        "title": title,
        "focus": focus,
        "status": "completed",
        "findings": findings,
        "recommendations": recommendations,
        "executable": DELIBERATION_RECOMMENDATION_EXECUTABLE,
        "autonomous_execution": False,
        "autonomous_approval": False,
        "read_only": True,
    }


def _planning_sections(mission_planning: dict[str, Any]) -> dict[str, Any]:
    return mission_planning.get("sections") or {}


def run_planner_agent(*, mission_planning: dict[str, Any]) -> dict[str, Any]:
    options = _planning_sections(mission_planning).get("action_option_generation") or []
    option_labels = [
        str(o.get("label") or o.get("option_id") or "")
        for o in options
        if o.get("label") or o.get("option_id")
    ]
    return _base_result(
        role_id="planner_agent",
        title="PlannerAgent — institutional paths",
        focus="What paths exist?",
        findings=[
            f"Action options available: **{len(options)}**",
            f"Paths: {', '.join(option_labels[:4]) or 'none cataloged'}",
        ],
        recommendations=[
            "Compare options against orchestration readiness before human lane selection.",
            "Hold path remains valid when blockers or constitutional tradeoffs are unresolved.",
        ],
    )


def run_risk_agent(*, mission_planning: dict[str, Any]) -> dict[str, Any]:
    risks = _planning_sections(mission_planning).get("risks_and_blockers") or []
    do_not = _planning_sections(mission_planning).get("do_not_do_paths") or []
    return _base_result(
        role_id="risk_agent",
        title="RiskAgent — institutional risk",
        focus="What can go wrong?",
        findings=[
            f"Risk and blocker signals: **{len(risks)}**",
            f"Explicit do-not-do paths: **{len(do_not)}**",
        ],
        recommendations=[
            "Review orchestration and readiness blockers before proceeding.",
            "Never bypass do-not-do paths from mission planning cognition.",
        ],
    )


def run_constitutional_agent(*, mission_planning: dict[str, Any]) -> dict[str, Any]:
    tradeoffs = _planning_sections(mission_planning).get("constitutional_tradeoffs") or []
    return _base_result(
        role_id="constitutional_agent",
        title="ConstitutionalAgent — constitutional tensions",
        focus="What constitutional tensions exist?",
        findings=[
            f"Constitutional tradeoff signals: **{len(tradeoffs)}**",
            "Tensions surfaced from synthesis — not resolved by agents.",
        ],
        recommendations=[
            "Human constitutional stewardship required before lane execution.",
            "Do not collapse plural perspectives into a single agent recommendation.",
        ],
    )


def run_delivery_agent(*, mission_planning: dict[str, Any]) -> dict[str, Any]:
    mappings = _planning_sections(mission_planning).get("lane_touch_mapping") or []
    lanes: set[str] = set()
    for row in mappings:
        for lane in row.get("lanes_touched") or []:
            lanes.add(str(lane))
    return _base_result(
        role_id="delivery_agent",
        title="DeliveryAgent — execution lane touches",
        focus="What execution lanes would be touched?",
        findings=[
            f"Lane mapping entries: **{len(mappings)}**",
            f"Distinct lanes referenced: **{', '.join(sorted(lanes)) or 'none'}**",
        ],
        recommendations=[
            "Lane mapping is advisory — agents do not mutate software delivery or Railway lanes.",
            "Confirm required approvals for each touched lane before execution.",
        ],
    )


def run_verification_agent(*, mission_planning: dict[str, Any]) -> dict[str, Any]:
    approvals = _planning_sections(mission_planning).get("required_approvals") or []
    artifact = _planning_sections(mission_planning).get("mission_action_plan_artifact") or []
    risk_count = (artifact[0].get("risk_blocker_count") if artifact else 0) or 0
    return _base_result(
        role_id="verification_agent",
        title="VerificationAgent — evidence gaps",
        focus="What evidence is missing?",
        findings=[
            f"Required approval entries: **{len(approvals)}**",
            f"Planning artifact risk/blocker count: **{risk_count}**",
        ],
        recommendations=[
            "Gather cross-lane evidence and replay artifacts before institutional action.",
            "Verification remains read-only — agents do not run workspace or deploy verification.",
        ],
    )


def run_synthesis_agent(*, agent_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    roles_completed = [str(o.get("agent_role_id") or "") for o in agent_outputs if o.get("agent_role_id")]
    finding_count = sum(len(o.get("findings") or []) for o in agent_outputs)
    return _base_result(
        role_id="synthesis_agent",
        title="SynthesisAgent — consolidated deliberation summary",
        focus="Summarize findings",
        findings=[
            f"Agent roles completed: **{len(roles_completed)}** ({', '.join(roles_completed)})",
            f"Total findings across agents: **{finding_count}**",
        ],
        recommendations=[
            "Consolidated recommendation is advisory — human selects institutional path.",
            "No autonomous execution, approval, lane selection, PR creation, Railway mutation, or merge.",
        ],
    )


ROLE_RUNNERS: dict[str, RoleRunner] = {
    "planner_agent": run_planner_agent,
    "risk_agent": run_risk_agent,
    "constitutional_agent": run_constitutional_agent,
    "delivery_agent": run_delivery_agent,
    "verification_agent": run_verification_agent,
}

assert set(ROLE_RUNNERS.keys()).issubset(set(BOUNDED_DELIBERATION_AGENT_ROLE_IDS))

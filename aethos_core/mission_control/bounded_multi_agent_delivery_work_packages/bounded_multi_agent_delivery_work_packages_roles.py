# SPDX-License-Identifier: Apache-2.0
"""FIX 168 — bounded delivery agent work package generators (scope only)."""

from __future__ import annotations

from typing import Any, Callable

from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_contract import (
    BOUNDED_DELIVERY_AGENT_ROLE_IDS,
    WORK_PACKAGES_RECOMMENDATION_EXECUTABLE,
)

PackageRunner = Callable[..., dict[str, Any]]


def _base_package(
    *,
    role_id: str,
    title: str,
    focus: str,
    inputs: list[str],
    outputs: list[str],
    gates: list[str],
    forbidden: list[str],
) -> dict[str, Any]:
    return {
        "package_id": f"{role_id}-work-package",
        "agent_role_id": role_id,
        "title": title,
        "focus": focus,
        "inputs": inputs,
        "outputs": outputs,
        "required_gates": gates,
        "forbidden_actions": forbidden,
        "executable": WORK_PACKAGES_RECOMMENDATION_EXECUTABLE,
        "autonomous_execution": False,
        "code_write": False,
        "read_only": True,
    }


def _handoff_sections(handoff: dict[str, Any]) -> dict[str, Any]:
    return handoff.get("sections") or {}


def _lanes(handoff: dict[str, Any]) -> list[str]:
    mapping = _handoff_sections(handoff).get("eligible_lane_mapping") or []
    for row in mapping:
        lanes = row.get("eligible_lanes") or []
        if lanes:
            return list(lanes)
    return []


def build_planner_package(*, handoff: dict[str, Any], plan_id: str | None) -> dict[str, Any]:
    path_id = handoff.get("selected_path_id") or "pending"
    lanes = _lanes(handoff)
    return _base_package(
        role_id="planner_agent",
        title="PlannerAgent — delivery work package",
        focus="Scope delivery stages and work sequencing",
        inputs=[
            f"handoff artifact for path `{path_id}`",
            f"plan_id `{plan_id or 'pending'}`",
            "governed software delivery loop order",
        ],
        outputs=[
            "scoped stage sequence (advisory)",
            "bounded work items per stage",
            "human approval checkpoints",
        ],
        gates=["issue_intake", "implementation_plan", "workspace_verification"],
        forbidden=["code_write", "pr_open", "autonomous_execution"],
    ) | {"eligible_lanes": lanes}


def build_risk_package(*, handoff: dict[str, Any], plan_id: str | None) -> dict[str, Any]:
    blockers = _handoff_sections(handoff).get("remaining_blockers") or []
    return _base_package(
        role_id="risk_agent",
        title="RiskAgent — delivery work package",
        focus="Assess delivery risk and blast radius",
        inputs=[
            f"plan_id `{plan_id or 'pending'}`",
            f"handoff blocker count: {len(blockers)}",
            "issue plan risk assessment",
        ],
        outputs=[
            "risk tier confirmation (advisory)",
            "blast radius review checklist",
            "hold/continue recommendation for human",
        ],
        gates=["planning_approved", "patch_proposal_approved"],
        forbidden=["code_write", "merge_deploy", "railway_mutation"],
    )


def build_verification_package(*, handoff: dict[str, Any], plan_id: str | None) -> dict[str, Any]:
    gates = _handoff_sections(handoff).get("required_lane_gates") or []
    pending = [g.get("gate_id") for g in gates if g.get("status") == "pending"][:4]
    return _base_package(
        role_id="verification_agent",
        title="VerificationAgent — delivery work package",
        focus="Define verification inputs and evidence gaps",
        inputs=[
            f"plan_id `{plan_id or 'pending'}`",
            "workspace verification status",
            "evidence bundle and replay artifacts",
        ],
        outputs=[
            "verification checklist (advisory)",
            "evidence gap report",
            "preflight readiness summary",
        ],
        gates=["workspace_verification", "github_preflight_approved", *pending[:2]],
        forbidden=["code_write", "pr_open", "autonomous_approval"],
    )


def build_delivery_package(*, handoff: dict[str, Any], plan_id: str | None) -> dict[str, Any]:
    lanes = _lanes(handoff)
    return _base_package(
        role_id="delivery_agent",
        title="DeliveryAgent — delivery work package",
        focus="Map governed lane touches without execution",
        inputs=[
            f"handoff eligible lanes: {', '.join(lanes) or 'none'}",
            f"plan_id `{plan_id or 'pending'}`",
            "software delivery loop position",
        ],
        outputs=[
            "lane touch map (advisory)",
            "governed stage entry checklist",
            "human approval requirements per lane",
        ],
        gates=[f"{lane}-governance-boundary" for lane in lanes[:3]] or ["software_delivery-stage"],
        forbidden=["autonomous_lane_entry", "railway_mutation", "merge_deploy"],
    ) | {"lanes_touched": lanes}


def build_diff_audit_package(*, handoff: dict[str, Any], plan_id: str | None) -> dict[str, Any]:
    return _base_package(
        role_id="diff_audit_agent",
        title="DiffAuditAgent — delivery work package",
        focus="Audit patch proposals and diff scope",
        inputs=[
            f"plan_id `{plan_id or 'pending'}`",
            "patch proposal artifact",
            "unified diff preview",
        ],
        outputs=[
            "diff scope audit (advisory)",
            "file change inventory",
            "human review briefing for patch apply",
        ],
        gates=["patch_proposal_approved", "workspace_apply_approved"],
        forbidden=["code_write", "workspace_write", "pr_open"],
    )


PACKAGE_RUNNERS: dict[str, PackageRunner] = {
    "planner_agent": build_planner_package,
    "risk_agent": build_risk_package,
    "verification_agent": build_verification_package,
    "delivery_agent": build_delivery_package,
    "diff_audit_agent": build_diff_audit_package,
}

assert set(PACKAGE_RUNNERS.keys()) == set(BOUNDED_DELIVERY_AGENT_ROLE_IDS)

# SPDX-License-Identifier: Apache-2.0
"""FIX 167 — governed execution handoff coordination service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_167,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_167,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167,
    EXECUTION_HANDOFF_COORDINATION_FIX,
    EXECUTION_HANDOFF_COORDINATION_INVARIANT,
    EXECUTION_HANDOFF_COORDINATION_SCHEMA_VERSION,
    FORBIDDEN_HANDOFF_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_167,
    HANDOFF_PRINCIPLES,
    HANDOFF_RECOMMENDATION_EXECUTABLE,
    LANE_NEXT_STEP_HINTS,
    MERGE_DEPLOY_ENABLED_FIX_167,
    MUTATION_PERFORMED_FIX_167,
    PATH_LANE_MAP,
    PR_OPEN_ENABLED_FIX_167,
    RAILWAY_MUTATION_ENABLED_FIX_167,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
    list_execution_handoff_coordination_records,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_service import build_human_decision_board
from aethos_core.mission_control.mission_orchestration.mission_orchestration_service import build_mission_orchestration
from aethos_core.mission_control.mission_planning.mission_planning_contract import ACTION_OPTION_CATALOG
from aethos_core.software_delivery.software_delivery_phase_2_contract import SOFTWARE_DELIVERY_LOOP_ORDER


@dataclass(frozen=True)
class ExecutionHandoffCoordinationResult:
    ok: bool
    session_id: str
    execution_handoff_coordination: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _resolve_selected_path(human_decision_board: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    selection = (_sections(human_decision_board).get("human_selection_record") or [{}])[0]
    selected = str(selection.get("selected_path") or "")
    if not selected or selection.get("selection_id") == "pending-human-selection":
        return None, selection
    for oid, _, _, _ in ACTION_OPTION_CATALOG:
        if oid in selected:
            return oid, selection
    return selected, selection


def _lanes_for_path(path_id: str | None) -> list[str]:
    if not path_id:
        return []
    for oid, lanes in PATH_LANE_MAP:
        if oid == path_id:
            return list(lanes)
    for oid, _, _, lanes in ACTION_OPTION_CATALOG:
        if oid == path_id:
            return list(lanes)
    return []


def _selected_human_decision_read(*, human_decision_board: dict[str, Any]) -> list[dict[str, Any]]:
    path_id, selection = _resolve_selected_path(human_decision_board)
    if not path_id:
        return [
            {
                "read_id": "pending-human-decision",
                "detail": "No human selection recorded — handoff requires FIX 166 decision select record.",
                "handoff_ready": False,
                "read_only": True,
            }
        ]
    return [
        {
            "read_id": "selected-human-decision",
            "selected_path_id": path_id,
            "selected_path": selection.get("selected_path") if selection else path_id,
            "selected_by": selection.get("selected_by") if selection else None,
            "selected_at": selection.get("selected_at") if selection else None,
            "handoff_ready": True,
            "autonomous_selection": False,
            "read_only": True,
        }
    ]


def _eligible_lane_mapping(*, path_id: str | None, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "lane_gate_note")]
    lanes = _lanes_for_path(path_id)
    if path_id == "hold_no_go_path" or not lanes:
        return stored + [
            {
                "mapping_id": "hold-no-lane-entry",
                "selected_path": path_id or "unselected",
                "eligible_lanes": [],
                "lane_entry": False,
                "detail": "Hold path — no execution lane entry until human decision changes.",
                "read_only": True,
            }
        ]
    return stored + [
        {
            "mapping_id": f"lanes-for-{path_id}",
            "selected_path": path_id,
            "eligible_lanes": lanes,
            "lane_entry": False,
            "autonomous_lane_entry": False,
            "detail": f"Eligible governed lanes for `{path_id}` — handoff coordinates only.",
            "read_only": True,
        }
    ]


def _execution_handoff_package(
    *,
    records: list[dict[str, Any]],
    path_id: str | None,
    lanes: list[str],
    human_decision_board: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "handoff_artifact")]
    review_pkg = (_sections(human_decision_board).get("decision_review_package") or [{}])[0]
    package = {
        "package_id": "execution-handoff-package",
        "selected_path": path_id,
        "eligible_lane_count": len(lanes),
        "decision_review_ready": bool(review_pkg.get("human_selection_recorded")),
        "execution_authority": False,
        "detail": "Execution handoff package — connects human decision to governed lanes without executing.",
        "recommendation_only": True,
        "read_only": True,
    }
    return stored + [package]


def _required_lane_gates(*, orchestration: dict[str, Any], lanes: list[str]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    stage_orch = _sections(orchestration).get("governed_stage_orchestration") or {}
    if isinstance(stage_orch, dict):
        current_stage = stage_orch.get("current_stage")
        if current_stage:
            gates.append(
                {
                    "gate_id": f"{current_stage}-stage",
                    "lane": "software_delivery",
                    "stage": current_stage,
                    "status": "current",
                    "gate_passed": False,
                    "autonomous_pass": False,
                    "read_only": True,
                }
            )
        for gate in (stage_orch.get("pending_gates") or [])[:6]:
            gate_id = gate if isinstance(gate, str) else gate.get("gate") or gate.get("gate_id")
            gates.append(
                {
                    "gate_id": gate_id,
                    "lane": "software_delivery",
                    "status": "pending",
                    "gate_passed": False,
                    "autonomous_pass": False,
                    "read_only": True,
                }
            )
        for stage in (stage_orch.get("upcoming_stages") or [])[:4]:
            gates.append(
                {
                    "gate_id": f"{stage}-upcoming",
                    "lane": "software_delivery",
                    "stage": stage,
                    "status": "upcoming",
                    "gate_passed": False,
                    "autonomous_pass": False,
                    "read_only": True,
                }
            )
    elif isinstance(stage_orch, list):
        for row in stage_orch[:6]:
            gates.append(
                {
                    "gate_id": row.get("stage") or row.get("gate_id"),
                    "lane": "software_delivery",
                    "status": row.get("status"),
                    "gate_passed": False,
                    "autonomous_pass": False,
                    "read_only": True,
                }
            )
    for lane in lanes:
        if lane != "software_delivery":
            gates.append(
                {
                    "gate_id": f"{lane}-governance-boundary",
                    "lane": lane,
                    "detail": f"Governed entry to `{lane}` requires explicit human approval.",
                    "autonomous_pass": False,
                    "read_only": True,
                }
            )
    if not gates:
        gates.append(
            {
                "gate_id": "no-lane-gates",
                "detail": "No lane gates until human selects an actionable path.",
                "read_only": True,
            }
        )
    return gates


def _required_approvals(*, records: list[dict[str, Any]], inbox: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "approval_requirement_note")]
    approvals: list[dict[str, Any]] = list(stored)
    for item in inbox.get("items") or []:
        if item.get("status") != "pending":
            continue
        approvals.append(
            {
                "approval_id": item.get("inbox_id"),
                "gate_id": item.get("gate_id"),
                "required_phrases": item.get("required_phrases") or [],
                "autonomous_approval": False,
                "human_review_required": True,
                "read_only": True,
            }
        )
    if not approvals:
        approvals.append(
            {
                "approval_id": "human-approval-required",
                "detail": "All lane entry requires explicit human approval — handoff never approves.",
                "read_only": True,
            }
        )
    return approvals


def _remaining_blockers(
    *,
    records: list[dict[str, Any]],
    human_decision_board: dict[str, Any],
    orchestration: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "blocker_note")]
    planning_blockers = human_decision_board.get("sources", {})
    blocked = _sections(orchestration).get("blocked_by_relationships") or []
    blockers: list[dict[str, Any]] = list(stored)
    if not planning_blockers.get("mission_planning_deliberation"):
        blockers.append(
            {
                "blocker_id": "deliberation-incomplete",
                "detail": "Complete multi-agent deliberation before execution handoff.",
                "read_only": True,
            }
        )
    for idx, row in enumerate(blocked[:4]):
        blockers.append(
            {
                "blocker_id": f"orchestration-blocker-{idx + 1}",
                "blocked_entity": row.get("blocked_entity"),
                "blocked_by": row.get("blocked_by"),
                "read_only": True,
            }
        )
    if not blockers:
        blockers.append(
            {
                "blocker_id": "handoff-blocker-check",
                "detail": "Review blockers before entering governed execution lane.",
                "read_only": True,
            }
        )
    return blockers


def _forbidden_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "forbidden_action_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_HANDOFF_ACTIONS
    ]
    return stored + catalog


def _next_step_command_sequence(*, path_id: str | None, lanes: list[str], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "next_step_note")]
    if stored:
        return stored
    if not path_id or path_id == "hold_no_go_path":
        return [
            {
                "step": 1,
                "command_hint": "decision select: <path> — record human selection on FIX 166 board",
                "autonomous_execution": False,
                "read_only": True,
            }
        ]
    steps: list[dict[str, Any]] = [
        {
            "step": 1,
            "command_hint": "human decision board — confirm selection and decision review package",
            "autonomous_execution": False,
            "read_only": True,
        }
    ]
    if "software_delivery" in lanes:
        for idx, stage in enumerate(SOFTWARE_DELIVERY_LOOP_ORDER[:4], start=2):
            steps.append(
                {
                    "step": idx,
                    "command_hint": f"software delivery — review governed stage `{stage}` (human approval required)",
                    "lane": "software_delivery",
                    "autonomous_execution": False,
                    "read_only": True,
                }
            )
    for lane, hint in LANE_NEXT_STEP_HINTS:
        if lane in lanes and lane != "software_delivery":
            steps.append(
                {
                    "step": len(steps) + 1,
                    "command_hint": hint,
                    "lane": lane,
                    "autonomous_execution": False,
                    "read_only": True,
                }
            )
    return steps


def _handoff_integrity_scoring(*, records: list[dict[str, Any]], handoff_ready: bool) -> list[dict[str, Any]]:
    score = 35 + (25 if handoff_ready else 0) + min(len(records) * 3, 15)
    has_artifact = bool(_by_kind(records, "handoff_artifact"))
    if has_artifact:
        score += 15
    score = min(100, score)
    label = "handoff_ready" if score >= 80 else "handoff_partial" if score >= 50 else "handoff_blocked"
    return [
        {
            "score_id": "handoff-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "human_decision_required": True,
            "execution_authority": False,
            "detail": "Handoff integrity — coordinates to governed lanes without execution authority.",
            "read_only": True,
        }
    ]


def build_execution_handoff_coordination(*, session_id: str) -> ExecutionHandoffCoordinationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    decision_result = build_human_decision_board(session_id=sid)
    human_decision_board = decision_result.human_decision_board if decision_result.ok else {}
    orchestration_result = build_mission_orchestration(session_id=sid)
    orchestration = orchestration_result.orchestration if orchestration_result.ok else {}

    plan_id = str(human_decision_board.get("plan_id") or orchestration.get("plan_id") or "") or None
    correlation_id = str(
        human_decision_board.get("correlation_id") or orchestration.get("correlation_id") or ""
    ) or None

    records = list_execution_handoff_coordination_records(session_id=sid, plan_id=plan_id)
    inbox = approval_inbox_payload(session_id=sid)

    path_id, _ = _resolve_selected_path(human_decision_board)
    lanes = _lanes_for_path(path_id)
    handoff_ready = path_id is not None and path_id != "pending-human-selection"

    sections = {
        "selected_human_decision_read": _selected_human_decision_read(human_decision_board=human_decision_board),
        "eligible_lane_mapping": _eligible_lane_mapping(path_id=path_id, records=records),
        "execution_handoff_package": _execution_handoff_package(
            records=records,
            path_id=path_id,
            lanes=lanes,
            human_decision_board=human_decision_board,
        ),
        "required_lane_gates": _required_lane_gates(orchestration=orchestration, lanes=lanes),
        "required_approvals": _required_approvals(records=records, inbox=inbox),
        "remaining_blockers": _remaining_blockers(
            records=records,
            human_decision_board=human_decision_board,
            orchestration=orchestration,
        ),
        "forbidden_actions": _forbidden_actions(records=records),
        "next_step_command_sequence": _next_step_command_sequence(path_id=path_id, lanes=lanes, records=records),
        "handoff_integrity_scoring": _handoff_integrity_scoring(records=records, handoff_ready=handoff_ready),
    }

    execution_handoff_coordination: dict[str, Any] = {
        "schema_version": EXECUTION_HANDOFF_COORDINATION_SCHEMA_VERSION,
        "fix": EXECUTION_HANDOFF_COORDINATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_167,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_167,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_167,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_167,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167,
        "pr_open_enabled": PR_OPEN_ENABLED_FIX_167,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_167,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_167,
        "invariant": EXECUTION_HANDOFF_COORDINATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "handoff_record_count": len(records),
        "selected_path_id": path_id,
        "eligible_lane_count": len(lanes),
        "all_recommendations_executable": False,
        "execution_handoff_coordination_cognition": True,
        "handoff_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in HANDOFF_PRINCIPLES
        ],
        "sources": {
            "human_decision_board": decision_result.ok,
            "mission_orchestration": orchestration_result.ok,
            "human_selection_recorded": handoff_ready,
            "handoff_records": len(records),
        },
    }
    return ExecutionHandoffCoordinationResult(
        ok=True,
        session_id=sid,
        execution_handoff_coordination=execution_handoff_coordination,
        detail="Execution handoff coordination assembled (recommendation-only — no execution authority).",
    )

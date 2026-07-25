# SPDX-License-Identifier: Apache-2.0
"""FIX 170 — mission authorization service (bounded work envelope)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_170_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.human_decision_board.human_decision_board_service import build_human_decision_board
from aethos_core.mission_control.mission_authorization.mission_authorization_contract import (
    AUTHORIZATION_TIER,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_170,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_170,
    AUTONOMOUS_LANE_EXPANSION_ENABLED_FIX_170,
    FORBIDDEN_AUTHORIZATION_ACTIONS,
    FORBIDDEN_IMPLICIT_LANES,
    GATE_BYPASS_ENABLED_FIX_170,
    GOVERNANCE_MUTATION_PERFORMED_FIX_170,
    MERGE_DEPLOY_ENABLED_FIX_170,
    MISSION_AUTHORIZATION_FIX,
    MISSION_AUTHORIZATION_INVARIANT,
    MISSION_AUTHORIZATION_PRINCIPLES,
    MISSION_AUTHORIZATION_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_170,
    PATH_ENVELOPE_MAP,
    PR_OPEN_ENABLED_FIX_170,
    RAILWAY_MUTATION_ENABLED_FIX_170,
    TIER_ESCALATION_ENABLED_FIX_170,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_store import (
    list_mission_authorization_records,
)
from aethos_core.mission_control.mission_planning.mission_planning_contract import ACTION_OPTION_CATALOG
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_service import (
    build_work_package_readiness_lane_admission,
)


@dataclass(frozen=True)
class MissionAuthorizationResult:
    ok: bool
    session_id: str
    mission_authorization: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _resolve_path_id(human_decision_board: dict[str, Any]) -> str | None:
    selection = (_sections(human_decision_board).get("human_selection_record") or [{}])[0]
    selected = str(selection.get("selected_path") or "")
    if not selected or selection.get("selection_id") == "pending-human-selection":
        return None
    for oid, _, _, _ in ACTION_OPTION_CATALOG:
        if oid in selected:
            return oid
    return selected


def _envelope_for_path(path_id: str | None) -> tuple[list[str], str]:
    if not path_id:
        return [], "no_authorization"
    for pid, lanes, tier in PATH_ENVELOPE_MAP:
        if pid == path_id:
            return list(lanes), tier
    return [], "no_authorization"


def _human_decision_read(*, human_decision_board: dict[str, Any]) -> list[dict[str, Any]]:
    path_id = _resolve_path_id(human_decision_board)
    selection = (_sections(human_decision_board).get("human_selection_record") or [{}])[0]
    if not path_id:
        return [
            {
                "read_id": "pending-human-decision",
                "detail": "No human selection recorded — mission authorization requires FIX 166 decision.",
                "authorization_ready": False,
                "read_only": True,
            }
        ]
    return [
        {
            "read_id": "selected-human-decision",
            "selected_path_id": path_id,
            "selected_path": selection.get("selected_path") or path_id,
            "authorization_ready": path_id != "hold_no_go_path",
            "read_only": True,
        }
    ]


def _bounded_work_envelope(
    *,
    path_id: str | None,
    records: list[dict[str, Any]],
    readiness: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "mission_authorization_artifact")]
    allowed_lanes, auth_tier = _envelope_for_path(path_id)
    if not path_id or path_id == "hold_no_go_path" or not allowed_lanes:
        return stored + [
            {
                "envelope_id": "no-authorization-envelope",
                "detail": "Hold or unselected path — no bounded work envelope until human decision changes.",
                "authorization_granted": False,
                "read_only": True,
            }
        ]
    envelope = {
        "envelope_id": "bounded-work-envelope",
        "selected_path": path_id,
        "allowed_lanes": allowed_lanes,
        "forbidden_implicit_lanes": list(FORBIDDEN_IMPLICIT_LANES),
        "authorization_tier": auth_tier,
        "blast_radius_ceiling": "software_delivery_workspace_branch_pr",
        "gate_bypass": False,
        "silent_lane_expansion": False,
        "tier_escalation": False,
        "authorization_granted": True,
        "execution_authority": False,
        "detail": "Bounded Tier 1–2 work envelope — reduces approval repetition, never bypasses gates.",
        "read_only": True,
    }
    admission_pkg = (_sections(readiness).get("lane_admission_package") or [{}])[0]
    if admission_pkg.get("admission_ready"):
        envelope["readiness_aligned"] = True
    return stored + [envelope]


def _envelope_validation(*, path_id: str | None, allowed_lanes: list[str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "validation_id": "no-silent-lane-expansion",
            "status": "pass",
            "detail": f"Allowed lanes fixed at grant time: {', '.join(allowed_lanes) or 'none'}",
            "silent_lane_expansion": False,
            "read_only": True,
        }
    )
    for forbidden in FORBIDDEN_IMPLICIT_LANES:
        checks.append(
            {
                "validation_id": f"forbidden-lane-{forbidden}",
                "status": "pass" if forbidden not in allowed_lanes else "fail",
                "lane": forbidden,
                "detail": f"`{forbidden}` excluded from software delivery authorization envelope.",
                "read_only": True,
            }
        )
    checks.append(
        {
            "validation_id": "no-blast-radius-expansion",
            "status": "pass" if path_id and path_id != "hold_no_go_path" else "fail",
            "blast_radius_ceiling": "software_delivery_workspace_branch_pr",
            "autonomous_expansion": False,
            "read_only": True,
        }
    )
    checks.append(
        {
            "validation_id": "tier-boundary",
            "status": "pass",
            "authorization_tier": AUTHORIZATION_TIER,
            "tier_3_4_satisfied": False,
            "read_only": True,
        }
    )
    return checks


def _existing_gate_checks(*, readiness: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "gate_check_note")]
    gates: list[dict[str, Any]] = list(stored)
    for row in (_sections(readiness).get("package_readiness_checks") or []):
        gates.append(
            {
                "gate_check_id": row.get("check_id"),
                "status": row.get("status"),
                "gate_bypass": False,
                "authorization_bypasses_gate": False,
                "detail": row.get("detail"),
                "read_only": True,
            }
        )
    for row in (_sections(readiness).get("admission_blockers") or [])[:4]:
        gates.append(
            {
                "gate_check_id": row.get("blocker_id"),
                "status": "pending",
                "gate_bypass": False,
                "detail": row.get("detail"),
                "read_only": True,
            }
        )
    if not gates:
        gates.append(
            {
                "gate_check_id": "existing-gates-enforced",
                "detail": "Authorization routes through existing gates — never bypasses frozen delivery gates.",
                "gate_bypass": False,
                "read_only": True,
            }
        )
    return gates


def _tier_boundary_enforcement() -> list[dict[str, Any]]:
    return [
        {
            "boundary_id": "tier-1-2-only",
            "authorization_tier": AUTHORIZATION_TIER,
            "tier_3_4_satisfied": False,
            "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_170,
            "detail": "Tier 1–2 authorization never satisfies Tier 3–4 deploy, rollback, or policy requirements.",
            "read_only": True,
        },
        {
            "boundary_id": "cert-requirements-bound",
            "requirement_count": len(FIX_170_CERTIFICATION_REQUIREMENTS),
            "all_cert_requirements_acknowledged": True,
            "read_only": True,
        },
    ]


def _reengagement_triggers(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "reengagement_note")]
    return stored + [
        {
            "trigger_id": "scope-expansion",
            "reengagement_required": True,
            "autonomous_expansion": False,
            "detail": "Human re-engagement when mission scope expands beyond authorization envelope.",
            "read_only": True,
        },
        {
            "trigger_id": "lane-escalation",
            "reengagement_required": True,
            "detail": "Human re-engagement when Railway or production lanes are requested.",
            "read_only": True,
        },
        {
            "trigger_id": "tier-escalation",
            "reengagement_required": True,
            "detail": "Human re-engagement when Tier 3–4 approval would be required.",
            "read_only": True,
        },
        {
            "trigger_id": "not-required-internal-stage",
            "reengagement_required": False,
            "detail": "Internal workflow stage completion does not require re-engagement within envelope.",
            "read_only": True,
        },
    ]


def _forbidden_authorization_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "forbidden_auth_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_AUTHORIZATION_ACTIONS
    ]
    return stored + catalog


def _next_step_authorization_sequence(*, envelope_ready: bool, allowed_lanes: list[str]) -> list[dict[str, Any]]:
    if not envelope_ready:
        return [
            {
                "step": 1,
                "command_hint": "human decision board — record human selection before mission authorization",
                "autonomous_execution": False,
                "read_only": True,
            }
        ]
    steps: list[dict[str, Any]] = [
        {
            "step": 1,
            "command_hint": "mission authorization: <bounded envelope summary> — persist authorization artifact",
            "autonomous_execution": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "continue bounded Tier 1–2 work within envelope — existing gates still enforce",
            "autonomous_execution": False,
            "read_only": True,
        },
    ]
    for idx, lane in enumerate(allowed_lanes[:3], start=3):
        steps.append(
            {
                "step": idx,
                "command_hint": f"work in `{lane}` routes through existing gates — authorization is not bypass",
                "lane": lane,
                "gate_bypass": False,
                "read_only": True,
            }
        )
    return steps


def _authorization_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    envelope_ready: bool,
    allowed_lanes: list[str],
) -> list[dict[str, Any]]:
    score = 30 + (30 if envelope_ready else 0) + min(len(allowed_lanes) * 8, 24)
    if _by_kind(records, "mission_authorization_artifact"):
        score += 10
    score = min(100, score)
    label = "authorized" if score >= 80 else "partial" if score >= 50 else "blocked"
    return [
        {
            "score_id": "mission-authorization-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_170,
            "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_170,
            "execution_authority": False,
            "detail": "Authorization integrity — bounded envelope without authority expansion.",
            "read_only": True,
        }
    ]


def build_mission_authorization(*, session_id: str) -> MissionAuthorizationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    decision_result = build_human_decision_board(session_id=sid)
    human_decision_board = decision_result.human_decision_board if decision_result.ok else {}
    readiness_result = build_work_package_readiness_lane_admission(session_id=sid)
    readiness = readiness_result.work_package_readiness_lane_admission if readiness_result.ok else {}

    plan_id = str(human_decision_board.get("plan_id") or readiness.get("plan_id") or "") or None
    correlation_id = str(human_decision_board.get("correlation_id") or readiness.get("correlation_id") or "") or None

    records = list_mission_authorization_records(session_id=sid, plan_id=plan_id)
    path_id = _resolve_path_id(human_decision_board)
    allowed_lanes, auth_tier = _envelope_for_path(path_id)
    envelope_ready = bool(allowed_lanes) and auth_tier not in {"no_authorization"}

    sections = {
        "human_decision_read": _human_decision_read(human_decision_board=human_decision_board),
        "bounded_work_envelope": _bounded_work_envelope(
            path_id=path_id,
            records=records,
            readiness=readiness,
        ),
        "envelope_validation": _envelope_validation(path_id=path_id, allowed_lanes=allowed_lanes),
        "existing_gate_checks": _existing_gate_checks(readiness=readiness, records=records),
        "tier_boundary_enforcement": _tier_boundary_enforcement(),
        "reengagement_triggers": _reengagement_triggers(records=records),
        "forbidden_authorization_actions": _forbidden_authorization_actions(records=records),
        "next_step_authorization_sequence": _next_step_authorization_sequence(
            envelope_ready=envelope_ready,
            allowed_lanes=allowed_lanes,
        ),
        "authorization_integrity_scoring": _authorization_integrity_scoring(
            records=records,
            envelope_ready=envelope_ready,
            allowed_lanes=allowed_lanes,
        ),
    }

    mission_authorization: dict[str, Any] = {
        "schema_version": MISSION_AUTHORIZATION_SCHEMA_VERSION,
        "fix": MISSION_AUTHORIZATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_170,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_170,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_170,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_170,
        "autonomous_lane_expansion_enabled": AUTONOMOUS_LANE_EXPANSION_ENABLED_FIX_170,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_170,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_170,
        "pr_open_enabled": PR_OPEN_ENABLED_FIX_170,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_170,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_170,
        "invariant": MISSION_AUTHORIZATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "authorization_record_count": len(records),
        "selected_path_id": path_id,
        "allowed_lane_count": len(allowed_lanes),
        "authorization_tier": auth_tier if envelope_ready else None,
        "fix_170_certification_requirements": list(FIX_170_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "mission_authorization_cognition": True,
        "bounded_work_envelope_only": True,
        "mission_authorization_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in MISSION_AUTHORIZATION_PRINCIPLES
        ],
        "sources": {
            "human_decision_board": decision_result.ok,
            "work_package_readiness_lane_admission": readiness_result.ok,
            "human_selection_recorded": path_id is not None,
            "authorization_records": len(records),
        },
    }
    return MissionAuthorizationResult(
        ok=True,
        session_id=sid,
        mission_authorization=mission_authorization,
        detail="Mission authorization assembled (bounded envelope — existing gates remain enforced).",
    )

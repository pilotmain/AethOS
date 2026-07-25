# SPDX-License-Identifier: Apache-2.0
"""FIX 175 — governed lane readiness board (composes FIX 174 + FIX 170 envelope read)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_175_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_service import (
    build_governed_lane_entry_recommendation,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_175,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_175,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175,
    BOARD_TIER,
    CODE_WRITE_ENABLED_FIX_175,
    EXECUTION_PERFORMED_FIX_175,
    FORBIDDEN_BOARD_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_175,
    GOVERNANCE_MUTATION_PERFORMED_FIX_175,
    GOVERNED_LANE_READINESS_BOARD_FIX,
    GOVERNED_LANE_READINESS_BOARD_INVARIANT,
    GOVERNED_LANE_READINESS_BOARD_PRINCIPLES,
    GOVERNED_LANE_READINESS_BOARD_SCHEMA_VERSION,
    LANE_ADMISSION_DECISION_PERFORMED_FIX_175,
    LANE_ADMISSION_PERFORMED_FIX_175,
    MERGE_DEPLOY_ENABLED_FIX_175,
    MUTATION_PERFORMED_FIX_175,
    PR_ACTION_ENABLED_FIX_175,
    RAILWAY_MUTATION_ENABLED_FIX_175,
    TIER_ESCALATION_ENABLED_FIX_175,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_170,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_174,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
    list_governed_lane_readiness_board_records,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_service import (
    build_mission_authorization,
)


@dataclass(frozen=True)
class GovernedLaneReadinessBoardResult:
    ok: bool
    session_id: str
    governed_lane_readiness_board: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _lane_recommendation_upstream_read(*, recommendation: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "read_id": "fix-174-recommendation-read",
            "upstream_fix": "FIX 174",
            "recommendation_ready": recommendation.get("recommendation_ready"),
            "lane_entry_candidate_count": recommendation.get("lane_entry_candidate_count"),
            "eligible_lane_entry_count": recommendation.get("eligible_lane_entry_count"),
            "lane_recommendation_record_count": recommendation.get("lane_recommendation_record_count"),
            "read_only": True,
            "recomputed_by_fix_175": False,
        }
    ]


def _authorization_envelope_status(*, authorization: dict[str, Any]) -> list[dict[str, Any]]:
    envelope_rows = _sections(authorization).get("bounded_work_envelope") or []
    envelope = envelope_rows[-1] if envelope_rows else {}
    return [
        {
            "status_id": "authorization-envelope-status",
            "upstream_fix": "FIX 170",
            "authorization_tier": authorization.get("authorization_tier"),
            "allowed_lane_count": authorization.get("allowed_lane_count"),
            "selected_path_id": authorization.get("selected_path_id"),
            "blast_radius_ceiling": envelope.get("blast_radius_ceiling"),
            "allowed_lanes": envelope.get("allowed_lanes") or [],
            "envelope_ready": envelope.get("envelope_id") == "bounded-work-envelope",
            "lane_admission_decision_performed": False,
            "read_only": True,
            "recomputed_by_fix_175": False,
        }
    ]


def _recommended_lane_candidates_board(
    *,
    recommendation: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "board_candidate_note")]
    board: list[dict[str, Any]] = list(stored)
    for row in _sections(recommendation).get("lane_entry_candidates") or []:
        if not row.get("candidate_id"):
            continue
        board.append(
            {
                "board_row_id": f"board-{row.get('candidate_id')}",
                "upstream_fix": "FIX 174",
                "candidate_id": row.get("candidate_id"),
                "agent_role_id": row.get("agent_role_id"),
                "recommended_lane": row.get("recommended_lane"),
                "recommended_gate": row.get("recommended_gate"),
                "recommendation_status": row.get("recommendation_status"),
                "lane_admission_decision_performed": False,
                "read_only": True,
            }
        )
    if not board:
        board.append(
            {
                "board_row_id": "no-candidates",
                "detail": "No lane candidates until FIX 174 lane recommendation is ready.",
                "read_only": True,
            }
        )
    return board[:12]


def _blocked_lanes_board(*, recommendation: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "board_blocker_note")]
    blocked: list[dict[str, Any]] = list(stored)
    for row in _sections(recommendation).get("blocked_lane_explanations") or []:
        if row.get("explanation_id"):
            blocked.append(
                {
                    "board_row_id": row.get("explanation_id"),
                    "upstream_fix": row.get("upstream_fix") or "FIX 174",
                    "detail": row.get("detail"),
                    "lane_admission_decision_performed": False,
                    "read_only": True,
                }
            )
    if not blocked:
        blocked.append(
            {
                "board_row_id": "no-blocked-lanes",
                "detail": "No blocked lanes in upstream FIX 174 context.",
                "read_only": True,
            }
        )
    return blocked[:16]


def _required_gates_board(*, recommendation: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "board_gate_note")]
    gates: list[dict[str, Any]] = list(stored)
    for row in _sections(recommendation).get("recommended_next_gate") or []:
        if row.get("gate_id"):
            gates.append(
                {
                    "board_row_id": f"gate-{row.get('gate_id')}",
                    "upstream_fix": "FIX 174",
                    "gate_id": row.get("gate_id"),
                    "lane": row.get("lane"),
                    "detail": row.get("detail"),
                    "gate_bypass": False,
                    "lane_admission_decision_performed": False,
                    "read_only": True,
                }
            )
    if not gates:
        gates.append(
            {
                "board_row_id": "no-gates",
                "detail": "Required gates unavailable until FIX 174 recommends next gate.",
                "read_only": True,
            }
        )
    return gates[:8]


def _missing_prerequisites_board(*, recommendation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(recommendation).get("missing_prerequisites_references") or []:
        if row.get("missing_prerequisites"):
            rows.append(
                {
                    "board_row_id": row.get("reference_id"),
                    "upstream_fix": row.get("upstream_fix") or "FIX 174",
                    "missing_prerequisites": row.get("missing_prerequisites"),
                    "detail": row.get("detail"),
                    "read_only": True,
                }
            )
    if not rows:
        rows.append(
            {
                "board_row_id": "no-missing-prerequisites",
                "detail": "No missing prerequisites referenced from upstream.",
                "read_only": True,
            }
        )
    return rows


def _escalation_requirements_board(
    *,
    recommendation: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "board_escalation_note")]
    reqs: list[dict[str, Any]] = list(stored)
    for row in _sections(recommendation).get("escalation_requirements") or []:
        tid = row.get("requirement_id") or row.get("trigger_id") or row.get("monitor_id")
        if tid or row.get("escalation_required"):
            reqs.append({**row, "board_row_id": tid, "upstream_fix": "FIX 174", "read_only": True})
    if not reqs:
        reqs.append(
            {
                "board_row_id": "no-escalation",
                "detail": "No escalation requirements from upstream FIX 174.",
                "read_only": True,
            }
        )
    return reqs


def _risk_blast_radius_summary(
    *,
    authorization: dict[str, Any],
    recommendation: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "board_risk_note")]
    envelope = (_sections(authorization).get("bounded_work_envelope") or [{}])[-1]
    blocked_count = sum(
        1
        for r in _sections(recommendation).get("blocked_lane_explanations") or []
        if r.get("explanation_id") and r.get("explanation_id") != "no-blocked-lanes"
    )
    eligible = int(recommendation.get("eligible_lane_entry_count") or 0)
    risk_label = "elevated" if blocked_count >= 3 else "moderate" if blocked_count else "bounded"
    return stored + [
        {
            "summary_id": "risk-blast-radius",
            "risk_label": risk_label,
            "blast_radius_ceiling": envelope.get("blast_radius_ceiling") or "software_delivery_workspace_branch_pr",
            "blocked_lane_count": blocked_count,
            "eligible_lane_entry_count": eligible,
            "authorization_tier": authorization.get("authorization_tier"),
            "detail": "Risk summary from FIX 170 envelope ceiling and FIX 174 blocked/eligible counts.",
            "lane_admission_decision_performed": False,
            "read_only": True,
        }
    ]


def _lane_readiness_board_packet(
    *,
    recommendation: dict[str, Any],
    authorization: dict[str, Any],
    candidate_count: int,
    blocked_count: int,
) -> list[dict[str, Any]]:
    envelope = (_sections(authorization).get("bounded_work_envelope") or [{}])[-1]
    return [
        {
            "packet_id": "lane-readiness-board-packet",
            "recommendation_ready": recommendation.get("recommendation_ready"),
            "authorization_tier": authorization.get("authorization_tier"),
            "blast_radius_ceiling": envelope.get("blast_radius_ceiling"),
            "candidate_count": candidate_count,
            "blocked_lane_count": blocked_count,
            "eligible_lane_entry_count": recommendation.get("eligible_lane_entry_count"),
            "lane_admission_decision_performed": False,
            "lane_admission_performed": False,
            "detail": "Lane readiness board packet — human reviews before FIX 176 admission decision.",
            "read_only": True,
        }
    ]


def _forbidden_board_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "forbidden_board_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_BOARD_ACTIONS
    ]
    return stored + catalog


def _next_step_lane_readiness_board_sequence(*, board_ready: bool) -> list[dict[str, Any]]:
    if not board_ready:
        return [
            {
                "step": 1,
                "command_hint": "lane entry recommendation — complete FIX 174 before lane readiness board",
                "lane_admission_decision_performed": False,
                "read_only": True,
            }
        ]
    return [
        {
            "step": 1,
            "command_hint": "lane readiness board artifact: <review summary> — persist board record",
            "lane_admission_decision_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "review candidates, blockers, gates, and risk on board — human decides admission (FIX 176)",
            "read_only": True,
        },
        {
            "step": 3,
            "command_hint": "hand board to human lane admission decision — board does not admit",
            "lane_admission_performed": False,
            "read_only": True,
        },
    ]


def _lane_readiness_board_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    board_ready: bool,
    candidate_count: int,
) -> list[dict[str, Any]]:
    score = 25 + (35 if board_ready else 0) + min(candidate_count * 5, 25)
    if _by_kind(records, "lane_readiness_board_artifact"):
        score += 10
    score = min(100, score)
    label = "board_ready" if score >= 80 else "partial" if score >= 50 else "blocked"
    return [
        {
            "score_id": "governed-lane-readiness-board-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "lane_admission_decision_performed": LANE_ADMISSION_DECISION_PERFORMED_FIX_175,
            "composes_upstream_layers": True,
            "detail": "Lane readiness board integrity — consolidates FIX 174 for human review.",
            "read_only": True,
        }
    ]


def build_governed_lane_readiness_board(*, session_id: str) -> GovernedLaneReadinessBoardResult:
    sid = (session_id or "default").strip()[:64] or "default"

    recommendation_result = build_governed_lane_entry_recommendation(session_id=sid)
    authorization_result = build_mission_authorization(session_id=sid)
    recommendation = (
        recommendation_result.governed_lane_entry_recommendation if recommendation_result.ok else {}
    )
    authorization = authorization_result.mission_authorization if authorization_result.ok else {}

    plan_id = str(recommendation.get("plan_id") or authorization.get("plan_id") or "") or None
    correlation_id = str(recommendation.get("correlation_id") or authorization.get("correlation_id") or "") or None

    records = list_governed_lane_readiness_board_records(session_id=sid, plan_id=plan_id)
    board_ready = bool(recommendation.get("recommendation_ready")) and recommendation_result.ok

    candidates_board = _recommended_lane_candidates_board(recommendation=recommendation, records=records)
    blocked_board = _blocked_lanes_board(recommendation=recommendation, records=records)
    blocked_count = sum(
        1 for r in blocked_board if r.get("board_row_id") and r.get("board_row_id") != "no-blocked-lanes"
    )

    sections = {
        "lane_recommendation_upstream_read": _lane_recommendation_upstream_read(recommendation=recommendation),
        "authorization_envelope_status": _authorization_envelope_status(authorization=authorization),
        "recommended_lane_candidates_board": candidates_board,
        "blocked_lanes_board": blocked_board,
        "required_gates_board": _required_gates_board(recommendation=recommendation, records=records),
        "missing_prerequisites_board": _missing_prerequisites_board(recommendation=recommendation),
        "escalation_requirements_board": _escalation_requirements_board(
            recommendation=recommendation,
            records=records,
        ),
        "risk_blast_radius_summary": _risk_blast_radius_summary(
            authorization=authorization,
            recommendation=recommendation,
            records=records,
        ),
        "lane_readiness_board_packet": _lane_readiness_board_packet(
            recommendation=recommendation,
            authorization=authorization,
            candidate_count=len(candidates_board),
            blocked_count=blocked_count,
        ),
        "forbidden_board_actions": _forbidden_board_actions(records=records),
        "next_step_lane_readiness_board_sequence": _next_step_lane_readiness_board_sequence(
            board_ready=board_ready,
        ),
        "lane_readiness_board_integrity_scoring": _lane_readiness_board_integrity_scoring(
            records=records,
            board_ready=board_ready,
            candidate_count=len(candidates_board),
        ),
    }

    governed_lane_readiness_board: dict[str, Any] = {
        "schema_version": GOVERNED_LANE_READINESS_BOARD_SCHEMA_VERSION,
        "fix": GOVERNED_LANE_READINESS_BOARD_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_175,
        "execution_performed": EXECUTION_PERFORMED_FIX_175,
        "lane_admission_performed": LANE_ADMISSION_PERFORMED_FIX_175,
        "lane_admission_decision_performed": LANE_ADMISSION_DECISION_PERFORMED_FIX_175,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_175,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_175,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_175,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_175,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_175,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_175,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_175,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_175,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_175,
        "invariant": GOVERNED_LANE_READINESS_BOARD_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "lane_readiness_board_record_count": len(records),
        "board_candidate_count": len(candidates_board),
        "blocked_lane_count": blocked_count,
        "board_tier": BOARD_TIER if board_ready else None,
        "board_ready": board_ready,
        "recommendation_ready_upstream": recommendation.get("recommendation_ready"),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_174_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_174),
            "fix_170_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_170),
        },
        "fix_175_certification_requirements": list(FIX_175_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "governed_lane_readiness_board_cognition": True,
        "lane_readiness_board_not_admission_decision": True,
        "governed_lane_readiness_board_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_LANE_READINESS_BOARD_PRINCIPLES
        ],
        "sources": {
            "composes_governed_lane_entry_recommendation": recommendation_result.ok,
            "composes_mission_authorization_envelope_read": authorization_result.ok,
            "governed_lane_entry_recommendation_fix": "FIX 174",
            "mission_authorization_fix": "FIX 170",
            "lane_readiness_board_records": len(records),
        },
    }
    return GovernedLaneReadinessBoardResult(
        ok=True,
        session_id=sid,
        governed_lane_readiness_board=governed_lane_readiness_board,
        detail="Governed lane readiness board assembled (composes FIX 174 — board ≠ admission decision).",
    )

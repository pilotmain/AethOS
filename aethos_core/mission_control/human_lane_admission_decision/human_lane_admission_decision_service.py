# SPDX-License-Identifier: Apache-2.0
"""FIX 176 — human lane admission decision (composes FIX 175)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_176_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_service import (
    build_governed_lane_readiness_board,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_176,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_176,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176,
    CODE_WRITE_ENABLED_FIX_176,
    DECISION_TIER,
    EXECUTION_PERFORMED_FIX_176,
    FORBIDDEN_DECISION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_176,
    GOVERNANCE_MUTATION_PERFORMED_FIX_176,
    HUMAN_LANE_ADMISSION_DECISION_FIX,
    HUMAN_LANE_ADMISSION_DECISION_INVARIANT,
    HUMAN_LANE_ADMISSION_DECISION_PRINCIPLES,
    HUMAN_LANE_ADMISSION_DECISION_SCHEMA_VERSION,
    LANE_ADMISSION_DECISION_VALUES,
    LANE_ADMISSION_EXECUTED_FIX_176,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_176,
    MERGE_DEPLOY_ENABLED_FIX_176,
    MUTATION_PERFORMED_FIX_176,
    PR_ACTION_ENABLED_FIX_176,
    RAILWAY_MUTATION_ENABLED_FIX_176,
    TIER_ESCALATION_ENABLED_FIX_176,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_175,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
    list_human_lane_admission_decision_records,
)


@dataclass(frozen=True)
class HumanLaneAdmissionDecisionResult:
    ok: bool
    session_id: str
    human_lane_admission_decision: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _parse_decision_value(content: str) -> str | None:
    lower = (content or "").strip().lower()
    for value in LANE_ADMISSION_DECISION_VALUES:
        if lower.startswith(value):
            return value
    return None


def _lane_readiness_board_upstream_read(*, board: dict[str, Any]) -> list[dict[str, Any]]:
    packet = (_sections(board).get("lane_readiness_board_packet") or [{}])[0]
    return [
        {
            "read_id": "fix-175-board-read",
            "upstream_fix": "FIX 175",
            "board_ready": board.get("board_ready"),
            "board_candidate_count": board.get("board_candidate_count"),
            "blocked_lane_count": board.get("blocked_lane_count"),
            "authorization_tier": packet.get("authorization_tier"),
            "read_only": True,
            "recomputed_by_fix_176": False,
        }
    ]


def _selected_lane_admission_decision(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = _by_kind(records, "lane_admission_decision_record")
    artifacts = _by_kind(records, "lane_admission_decision_artifact")
    rows: list[dict[str, Any]] = []
    for rec in decisions + artifacts:
        content = str(rec.get("content") or "")
        decision = _parse_decision_value(content)
        rows.append(
            {
                "decision_id": rec.get("record_id"),
                "decision_value": decision,
                "decision_content": content,
                "decided_by": rec.get("author"),
                "decided_at": rec.get("recorded_at"),
                "human_governed": True,
                "autonomous_decision": False,
                "lane_entry_execution_performed": False,
                "lane_admission_executed": False,
                "read_only": True,
            }
        )
    if not rows:
        rows.append(
            {
                "decision_id": "pending-human-decision",
                "detail": "No human lane admission decision recorded — admit, hold, or reject required.",
                "human_governed": True,
                "autonomous_decision": False,
                "lane_entry_execution_performed": False,
                "read_only": True,
            }
        )
    return rows


def _decision_rationale(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "decision_rationale_note")]
    if stored:
        return stored
    return [
        {
            "rationale_id": "no-rationale",
            "detail": "Decision rationale not yet recorded.",
            "read_only": True,
        }
    ]


def _accepted_risks_tradeoffs(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "risk_tradeoff_acceptance_note")]
    if stored:
        return stored
    return [
        {
            "acceptance_id": "no-risks-accepted",
            "detail": "No accepted risks or tradeoffs recorded.",
            "read_only": True,
        }
    ]


def _rejected_lane_candidates(
    *,
    board: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "rejected_candidate_note")]
    rows: list[dict[str, Any]] = list(stored)
    if not rows:
        candidates = _sections(board).get("recommended_lane_candidates_board") or []
        for cand in candidates:
            if cand.get("recommendation_status") == "blocked" and cand.get("board_row_id"):
                rows.append(
                    {
                        "rejection_id": f"implicit-{cand.get('board_row_id')}",
                        "upstream_fix": "FIX 175",
                        "agent_role_id": cand.get("agent_role_id"),
                        "recommended_gate": cand.get("recommended_gate"),
                        "detail": "Blocked candidate from board — not selected for admission.",
                        "read_only": True,
                    }
                )
    if not rows:
        rows.append(
            {
                "rejection_id": "no-rejections",
                "detail": "No rejected lane candidates recorded.",
                "read_only": True,
            }
        )
    return rows[:12]


def _acknowledged_remaining_blockers(
    *,
    board: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "acknowledged_blocker_note")]
    rows: list[dict[str, Any]] = list(stored)
    if not rows:
        for row in _sections(board).get("blocked_lanes_board") or []:
            if row.get("board_row_id") and row.get("board_row_id") != "no-blocked-lanes":
                rows.append(
                    {
                        "acknowledgment_id": f"board-{row.get('board_row_id')}",
                        "upstream_fix": row.get("upstream_fix") or "FIX 175",
                        "detail": row.get("detail"),
                        "human_acknowledged": False,
                        "read_only": True,
                    }
                )
    if not rows:
        rows.append(
            {
                "acknowledgment_id": "no-blockers",
                "detail": "No remaining blockers to acknowledge.",
                "read_only": True,
            }
        )
    return rows[:16]


def _lane_admission_decision_packet(
    *,
    board: dict[str, Any],
    records: list[dict[str, Any]],
    decision_recorded: bool,
) -> list[dict[str, Any]]:
    latest = _selected_lane_admission_decision(records=records)[-1]
    return [
        {
            "packet_id": "lane-admission-decision-packet",
            "board_ready_upstream": board.get("board_ready"),
            "human_decision_recorded": decision_recorded,
            "decision_value": latest.get("decision_value"),
            "lane_entry_execution_performed": False,
            "lane_admission_executed": False,
            "gate_bypass": False,
            "detail": "Human lane admission decision packet — FIX 177 performs gate-routed handoff.",
            "read_only": True,
        }
    ]


def _forbidden_decision_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_DECISION_ACTIONS
    ]
    return catalog


def _next_step_admission_decision_sequence(*, decision_recorded: bool) -> list[dict[str, Any]]:
    if not decision_recorded:
        return [
            {
                "step": 1,
                "command_hint": "lane admission decision admit|hold|reject: <summary> — record human decision",
                "lane_entry_execution_performed": False,
                "read_only": True,
            },
            {
                "step": 2,
                "command_hint": "lane admission rationale: <why> — persist decision rationale",
                "read_only": True,
            },
        ]
    return [
        {
            "step": 1,
            "command_hint": "lane admission decision artifact: <summary> — persist decision artifact",
            "lane_entry_execution_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "gate-routed lane entry handoff (FIX 177) — handoff does not execute lane entry alone",
            "read_only": True,
        },
    ]


def _decision_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    decision_ready: bool,
    decision_recorded: bool,
) -> list[dict[str, Any]]:
    score = 20 + (30 if decision_ready else 0) + (25 if decision_recorded else 0)
    if _by_kind(records, "decision_rationale_note"):
        score += 10
    if _by_kind(records, "risk_tradeoff_acceptance_note"):
        score += 10
    score = min(100, score)
    label = "decision_recorded" if decision_recorded and score >= 70 else "partial" if score >= 40 else "blocked"
    return [
        {
            "score_id": "human-lane-admission-decision-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_176,
            "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_176,
            "composes_upstream_layers": True,
            "detail": "Human decision integrity — records choice without lane entry execution.",
            "read_only": True,
        }
    ]


def build_human_lane_admission_decision(*, session_id: str) -> HumanLaneAdmissionDecisionResult:
    sid = (session_id or "default").strip()[:64] or "default"

    board_result = build_governed_lane_readiness_board(session_id=sid)
    board = board_result.governed_lane_readiness_board if board_result.ok else {}

    plan_id = str(board.get("plan_id") or "") or None
    correlation_id = str(board.get("correlation_id") or "") or None

    records = list_human_lane_admission_decision_records(session_id=sid, plan_id=plan_id)
    decision_ready = bool(board.get("board_ready")) and board_result.ok
    decision_records = _by_kind(records, "lane_admission_decision_record") + _by_kind(
        records, "lane_admission_decision_artifact"
    )
    decision_recorded = bool(decision_records)

    sections = {
        "lane_readiness_board_upstream_read": _lane_readiness_board_upstream_read(board=board),
        "selected_lane_admission_decision": _selected_lane_admission_decision(records=records),
        "decision_rationale": _decision_rationale(records=records),
        "accepted_risks_tradeoffs": _accepted_risks_tradeoffs(records=records),
        "rejected_lane_candidates": _rejected_lane_candidates(board=board, records=records),
        "acknowledged_remaining_blockers": _acknowledged_remaining_blockers(board=board, records=records),
        "lane_admission_decision_packet": _lane_admission_decision_packet(
            board=board,
            records=records,
            decision_recorded=decision_recorded,
        ),
        "forbidden_decision_actions": _forbidden_decision_actions(records=records),
        "next_step_admission_decision_sequence": _next_step_admission_decision_sequence(
            decision_recorded=decision_recorded,
        ),
        "decision_integrity_scoring": _decision_integrity_scoring(
            records=records,
            decision_ready=decision_ready,
            decision_recorded=decision_recorded,
        ),
    }

    human_lane_admission_decision: dict[str, Any] = {
        "schema_version": HUMAN_LANE_ADMISSION_DECISION_SCHEMA_VERSION,
        "fix": HUMAN_LANE_ADMISSION_DECISION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_176,
        "execution_performed": EXECUTION_PERFORMED_FIX_176,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_176,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_176,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_176,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_176,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_176,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_176,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_176,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_176,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_176,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_176,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_176,
        "invariant": HUMAN_LANE_ADMISSION_DECISION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "human_lane_admission_decision_record_count": len(records),
        "human_decision_recorded": decision_recorded,
        "decision_tier": DECISION_TIER if decision_ready else None,
        "decision_ready": decision_ready,
        "board_ready_upstream": board.get("board_ready"),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_175_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_175),
        },
        "fix_176_certification_requirements": list(FIX_176_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "human_lane_admission_decision_cognition": True,
        "human_lane_admission_decision_not_lane_entry_execution": True,
        "human_lane_admission_decision_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in HUMAN_LANE_ADMISSION_DECISION_PRINCIPLES
        ],
        "sources": {
            "composes_governed_lane_readiness_board": board_result.ok,
            "governed_lane_readiness_board_fix": "FIX 175",
            "human_lane_admission_decision_records": len(records),
        },
    }
    return HumanLaneAdmissionDecisionResult(
        ok=True,
        session_id=sid,
        human_lane_admission_decision=human_lane_admission_decision,
        detail="Human lane admission decision assembled (composes FIX 175 — decision ≠ lane entry execution).",
    )

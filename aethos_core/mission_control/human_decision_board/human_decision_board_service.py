# SPDX-License-Identifier: Apache-2.0
"""FIX 166 — human decision board + action selection service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.human_decision_board.human_decision_board_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_166,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_166,
    AUTONOMOUS_MERGE_ENABLED_FIX_166,
    AUTONOMOUS_PR_CREATION_ENABLED_FIX_166,
    AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_166,
    AUTONOMOUS_SELECTION_ENABLED_FIX_166,
    DECISION_BOARD_EXECUTABLE,
    DECISION_PRINCIPLES,
    GOVERNANCE_MUTATION_PERFORMED_FIX_166,
    HUMAN_DECISION_BOARD_FIX,
    HUMAN_DECISION_BOARD_INVARIANT,
    HUMAN_DECISION_BOARD_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_166,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
    list_human_decision_board_records,
)
from aethos_core.mission_control.mission_planning.mission_planning_contract import ACTION_OPTION_CATALOG
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_service import (
    build_mission_planning_deliberation,
)


@dataclass(frozen=True)
class HumanDecisionBoardResult:
    ok: bool
    session_id: str
    human_decision_board: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _candidate_action_board(*, deliberation: dict[str, Any], mission_planning: dict[str, Any]) -> list[dict[str, Any]]:
    options = _sections(mission_planning).get("action_option_generation") or []
    if not options:
        options = [
            {
                "option_id": oid,
                "label": label,
                "detail": detail,
                "lanes_touched": list(lanes),
                "human_selectable": True,
                "autonomous_selection": False,
                "read_only": True,
            }
            for oid, label, detail, lanes in ACTION_OPTION_CATALOG
        ]
    consolidated = (_sections(deliberation).get("consolidated_recommendation") or [{}])[0]
    return [
        {
            **row,
            "board_id": f"candidate-{row.get('option_id') or idx + 1}",
            "candidate_label": chr(65 + idx) if idx < 26 else f"option-{idx + 1}",
            "deliberation_informed": bool(consolidated.get("recommendation_id")),
            "human_selection_required": True,
            "autonomous_selection": False,
            "read_only": True,
        }
        for idx, row in enumerate(options)
        if row.get("option_id") or row.get("label")
    ]


def _human_selection_record(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selections = [{**r, "read_only": True} for r in _by_kind(records, "selection_record")]
    if selections:
        latest = selections[-1]
        return [
            {
                "selection_id": latest.get("record_id"),
                "selected_path": latest.get("content"),
                "selected_by": latest.get("author"),
                "selected_at": latest.get("recorded_at"),
                "autonomous_selection": False,
                "human_governed": True,
                "read_only": True,
            }
        ]
    return [
        {
            "selection_id": "pending-human-selection",
            "detail": "No human selection recorded — AethOS cannot select autonomously.",
            "autonomous_selection": False,
            "human_governed": True,
            "read_only": True,
        }
    ]


def _rejected_paths_analysis(*, records: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "rejection_note")]
    if stored:
        return stored
    candidate_ids = [str(c.get("option_id") or "") for c in candidates if c.get("option_id")]
    selections = _by_kind(records, "selection_record")
    selected_text = (selections[-1].get("content") if selections else "") or ""
    rejected = [
        {
            "rejection_id": f"implicit-reject-{oid}",
            "rejected_path": oid,
            "detail": f"Not selected — human chose alternative path.",
            "read_only": True,
        }
        for oid in candidate_ids
        if oid and oid not in selected_text
    ]
    return rejected[:4] if rejected else [
        {
            "rejection_id": "no-rejections-recorded",
            "detail": "Record rejected paths explicitly with decision reject: notes.",
            "read_only": True,
        }
    ]


def _decision_rationale_capture(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "rationale_note")]
    if stored:
        return stored
    return [
        {
            "rationale_id": "pending-rationale",
            "detail": "Capture decision rationale with decision rationale: — why this path was chosen.",
            "read_only": True,
        }
    ]


def _accepted_tradeoffs_and_risks(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tradeoffs = [{**r, "read_only": True, "acceptance_type": "tradeoff"} for r in _by_kind(records, "tradeoff_acceptance_note")]
    risks = [{**r, "read_only": True, "acceptance_type": "risk"} for r in _by_kind(records, "risk_acceptance_note")]
    combined = tradeoffs + risks
    if combined:
        return combined
    return [
        {
            "acceptance_id": "pending-tradeoffs-risks",
            "detail": "Record consciously accepted tradeoffs and risks at decision time.",
            "read_only": True,
        }
    ]


def _decision_traceability(
    *,
    records: list[dict[str, Any]],
    deliberation: dict[str, Any],
) -> list[dict[str, Any]]:
    agent_outputs = deliberation.get("agent_outputs") or []
    agents = [str(o.get("agent_role_id") or "") for o in agent_outputs if o.get("agent_role_id")]
    selections = _by_kind(records, "selection_record")
    latest = selections[-1] if selections else {}
    return [
        {
            "trace_id": "human-decision-trace",
            "selected_by": latest.get("author"),
            "selected_at": latest.get("recorded_at"),
            "decision_record_count": len(records),
            "agents_participated": agents,
            "agent_participation_count": len(agents),
            "deliberation_record_count": deliberation.get("deliberation_record_count", 0),
            "evidence_at_decision": {
                "mission_planning": deliberation.get("sources", {}).get("mission_planning"),
                "deliberation_complete": deliberation.get("agent_role_count", 0) >= 6,
            },
            "autonomous_selection": False,
            "read_only": True,
        }
    ]


def _decision_review_package(
    *,
    records: list[dict[str, Any]],
    sections: dict[str, Any],
) -> list[dict[str, Any]]:
    decision_artifacts = _by_kind(records, "decision_artifact")
    approval_artifacts = _by_kind(records, "approval_artifact")
    handoff_artifacts = _by_kind(records, "execution_handoff_artifact")
    selection = sections.get("human_selection_record") or []
    package = {
        "package_id": "decision-review-package",
        "decision_artifact_count": len(decision_artifacts),
        "approval_artifact_count": len(approval_artifacts),
        "execution_handoff_artifact_count": len(handoff_artifacts),
        "human_selection_recorded": bool(_by_kind(records, "selection_record")),
        "execution_handoff_ready": bool(handoff_artifacts) and bool(_by_kind(records, "selection_record")),
        "autonomous_execution": False,
        "detail": "Decision review package for governed execution lane handoff — human-governed only.",
        "read_only": True,
    }
    items: list[dict[str, Any]] = [package]
    for kind, label in (
        ("decision_artifact", "decision"),
        ("approval_artifact", "approval"),
        ("execution_handoff_artifact", "execution_handoff"),
    ):
        for row in _by_kind(records, kind):
            items.append({**row, "artifact_type": label, "read_only": True})
    if selection:
        items.append(
            {
                "artifact_type": "selection_summary",
                "selection_id": selection[0].get("selection_id"),
                "selected_path": selection[0].get("selected_path") or selection[0].get("detail"),
                "read_only": True,
            }
        )
    return items


def _decision_integrity_scoring(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    has_selection = bool(_by_kind(records, "selection_record"))
    has_rationale = bool(_by_kind(records, "rationale_note"))
    has_tradeoff = bool(_by_kind(records, "tradeoff_acceptance_note"))
    has_risk = bool(_by_kind(records, "risk_acceptance_note"))
    score = 40 + (15 if has_selection else 0) + (15 if has_rationale else 0) + (10 if has_tradeoff else 0) + (10 if has_risk else 0)
    score = min(100, score + min(len(records), 10))
    label = "decision_complete" if score >= 85 else "decision_partial" if score >= 55 else "decision_pending"
    return [
        {
            "score_id": "decision-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "human_selection_recorded": has_selection,
            "autonomous_selection": False,
            "detail": "Decision integrity reflects human-recorded choice — never autonomous selection.",
            "read_only": True,
        }
    ]


def build_human_decision_board(*, session_id: str) -> HumanDecisionBoardResult:
    sid = (session_id or "default").strip()[:64] or "default"

    deliberation_result = build_mission_planning_deliberation(session_id=sid)
    deliberation = deliberation_result.mission_planning_deliberation if deliberation_result.ok else {}

    from aethos_core.mission_control.mission_planning.mission_planning_service import build_mission_planning

    planning_result = build_mission_planning(session_id=sid)
    mission_planning = planning_result.mission_planning if planning_result.ok else {}

    plan_id = str(
        deliberation.get("plan_id") or mission_planning.get("plan_id") or ""
    ) or None
    correlation_id = str(
        deliberation.get("correlation_id") or mission_planning.get("correlation_id") or ""
    ) or None

    records = list_human_decision_board_records(session_id=sid, plan_id=plan_id)

    candidates = _candidate_action_board(deliberation=deliberation, mission_planning=mission_planning)
    sections = {
        "candidate_action_board": candidates,
        "human_selection_record": _human_selection_record(records=records),
        "rejected_paths_analysis": _rejected_paths_analysis(records=records, candidates=candidates),
        "decision_rationale_capture": _decision_rationale_capture(records=records),
        "accepted_tradeoffs_and_risks": _accepted_tradeoffs_and_risks(records=records),
        "decision_traceability": _decision_traceability(records=records, deliberation=deliberation),
        "decision_integrity_scoring": _decision_integrity_scoring(records=records),
    }
    sections["decision_review_package"] = _decision_review_package(records=records, sections=sections)

    human_decision_board: dict[str, Any] = {
        "schema_version": HUMAN_DECISION_BOARD_SCHEMA_VERSION,
        "fix": HUMAN_DECISION_BOARD_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_166,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_166,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166,
        "autonomous_selection_enabled": AUTONOMOUS_SELECTION_ENABLED_FIX_166,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_166,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_166,
        "autonomous_pr_creation_enabled": AUTONOMOUS_PR_CREATION_ENABLED_FIX_166,
        "autonomous_merge_enabled": AUTONOMOUS_MERGE_ENABLED_FIX_166,
        "autonomous_railway_mutation_enabled": AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_166,
        "invariant": HUMAN_DECISION_BOARD_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "decision_record_count": len(records),
        "candidate_count": len(candidates),
        "all_recommendations_executable": False,
        "human_decision_board_cognition": True,
        "human_selection_cognition": True,
        "decision_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in DECISION_PRINCIPLES
        ],
        "sources": {
            "mission_planning_deliberation": deliberation_result.ok,
            "mission_planning": planning_result.ok,
            "deliberation_agent_count": deliberation.get("agent_role_count", 0),
            "decision_records": len(records),
        },
    }
    return HumanDecisionBoardResult(
        ok=True,
        session_id=sid,
        human_decision_board=human_decision_board,
        detail="Human decision board assembled (human choice only — no autonomous selection or execution).",
    )

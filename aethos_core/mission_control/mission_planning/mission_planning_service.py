# SPDX-License-Identifier: Apache-2.0
"""FIX 164 — mission planning + institutional action cognition across synthesis and orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_service import (
    build_constitutional_synthesis,
)
from aethos_core.mission_control.cross_lane.cross_lane_contract import OBSERVED_LANES
from aethos_core.mission_control.mission_orchestration.mission_orchestration_service import build_mission_orchestration
from aethos_core.mission_control.mission_planning.mission_planning_contract import (
    ACTION_OPTION_CATALOG,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164,
    AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_164,
    AUTO_PATH_SELECTION_ENABLED_FIX_164,
    DO_NOT_DO_CATALOG,
    GOVERNANCE_MUTATION_PERFORMED_FIX_164,
    MERGE_DEPLOY_RESTART_ENABLED_FIX_164,
    MISSION_PLANNING_FIX,
    MISSION_PLANNING_INVARIANT,
    MISSION_PLANNING_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_164,
    PLANNING_PRINCIPLES,
    PLANNING_RECOMMENDATION_EXECUTABLE,
    PR_OPEN_ENABLED_FIX_164,
    RAILWAY_MUTATION_ENABLED_FIX_164,
)
from aethos_core.mission_control.mission_planning.mission_planning_store import list_mission_planning_records
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
    build_mission_readiness_review,
)
from aethos_core.mission_control.mission_strategy.mission_strategy_service import build_mission_strategy


@dataclass(frozen=True)
class MissionPlanningResult:
    ok: bool
    session_id: str
    mission_planning: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _action_option_generation(*, records: list[dict[str, Any]], synthesis: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "action_option_note")]
    synthesis_score = None
    scoring = _sections(synthesis).get("synthesis_coherence_scoring") or []
    if scoring:
        synthesis_score = scoring[0].get("coherence_score")
    catalog = [
        {
            "option_id": oid,
            "label": label,
            "detail": detail,
            "lanes_touched": list(lanes),
            "autonomous_execution": False,
            "auto_selected": False,
            "synthesis_informed": synthesis_score is not None,
            "recommendation_only": True,
            "read_only": True,
        }
        for oid, label, detail, lanes in ACTION_OPTION_CATALOG
    ]
    return stored + catalog


def _option_comparison(
    *,
    records: list[dict[str, Any]],
    orchestration: dict[str, Any],
    strategy: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "option_comparison_note")]
    readiness = _sections(orchestration).get("orchestration_readiness_scoring") or {}
    bottlenecks = _sections(strategy).get("strategic_bottlenecks") or []
    comparisons = [
        {
            "comparison_id": "institutional-action-comparison",
            "readiness_score": readiness.get("readiness_score"),
            "readiness_label": readiness.get("readiness_label"),
            "strategic_bottleneck_count": len(bottlenecks),
            "detail": "Compare action options against orchestration readiness and strategic bottlenecks — human selects path.",
            "auto_path_selection": False,
            "read_only": True,
        }
    ]
    if stored:
        return stored + comparisons
    option_ids = [oid for oid, _, _, _ in ACTION_OPTION_CATALOG]
    for idx, left in enumerate(option_ids):
        for right in option_ids[idx + 1 :]:
            comparisons.append(
                {
                    "comparison_id": f"{left}_vs_{right}",
                    "option_a": left,
                    "option_b": right,
                    "detail": f"Advisory comparison: `{left}` vs `{right}` — no autonomous path selection.",
                    "read_only": True,
                }
            )
    return comparisons


def _lane_touch_mapping(*, records: list[dict[str, Any]], orchestration: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "lane_mapping_note")]
    lane_sync = _sections(orchestration).get("lane_synchronization_visibility") or []
    mappings = list(stored)
    for oid, label, detail, lanes in ACTION_OPTION_CATALOG:
        if not lanes:
            continue
        mappings.append(
            {
                "mapping_id": f"lanes-{oid}",
                "option_id": oid,
                "option_label": label,
                "lanes_touched": list(lanes),
                "observed_lanes": list(OBSERVED_LANES),
                "lane_mutation": False,
                "detail": detail,
                "read_only": True,
            }
        )
    if lane_sync:
        mappings.append(
            {
                "mapping_id": "orchestration-lane-sync",
                "lane_sync_signal_count": len(lane_sync),
                "detail": "Orchestration lane synchronization informs lane touch mapping — planning does not mutate lanes.",
                "read_only": True,
            }
        )
    return mappings


def _required_approvals(*, records: list[dict[str, Any]], inbox: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "required_approval_note")]
    approvals: list[dict[str, Any]] = list(stored)
    for item in inbox.get("items") or []:
        if item.get("status") != "pending":
            continue
        approvals.append(
            {
                "approval_id": item.get("inbox_id"),
                "gate_id": item.get("gate_id"),
                "severity": item.get("severity"),
                "required_phrases": item.get("required_phrases") or [],
                "ui_approval_eligible": item.get("ui_approval_eligible"),
                "autonomous_approval": False,
                "human_review_required": True,
                "read_only": True,
            }
        )
    if not approvals:
        approvals.append(
            {
                "approval_id": "human-governance-required",
                "detail": "All institutional action paths require explicit human approval before execution.",
                "autonomous_approval": False,
                "read_only": True,
            }
        )
    return approvals


def _constitutional_tradeoffs(*, records: list[dict[str, Any]], synthesis: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "constitutional_tradeoff_note")]
    tradeoffs = _sections(synthesis).get("constitutional_tradeoff_maps") or []
    tensions = _sections(synthesis).get("constitutional_tension_analysis") or []
    mapped = [
        {
            "tradeoff_id": row.get("tradeoff_id") or row.get("tension_id"),
            "detail": row.get("detail") or row.get("description"),
            "source": "constitutional_synthesis",
            "planning_decision_authority": False,
            "read_only": True,
        }
        for row in (tradeoffs + tensions)[:8]
        if row.get("tradeoff_id") or row.get("tension_id")
    ]
    return stored + mapped


def _risks_and_blockers(
    *,
    records: list[dict[str, Any]],
    orchestration: dict[str, Any],
    readiness: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "risk_blocker_note")]
    blocked = _sections(orchestration).get("blocked_by_relationships") or []
    readiness_blockers = _sections(readiness).get("blockers") or []
    risks: list[dict[str, Any]] = list(stored)
    for idx, row in enumerate(blocked[:6]):
        risks.append(
            {
                "risk_id": f"orchestration-blocker-{idx + 1}",
                "blocked_entity": row.get("blocked_entity"),
                "blocked_by": row.get("blocked_by"),
                "priority": row.get("priority", "medium"),
                "source": "mission_orchestration",
                "read_only": True,
            }
        )
    for idx, row in enumerate(readiness_blockers[:6]):
        risks.append(
            {
                "risk_id": f"readiness-blocker-{idx + 1}",
                "blocker_id": row.get("blocker_id"),
                "detail": row.get("blocked_by") or row.get("detail"),
                "source": "mission_readiness_review",
                "read_only": True,
            }
        )
    if not risks:
        risks.append(
            {
                "risk_id": "bounded-planning-risk",
                "detail": "Planning surfaces risks; execution authority remains human-governed.",
                "read_only": True,
            }
        )
    return risks


def _do_not_do_paths(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "do_not_do_path_note")]
    catalog = [
        {"path_id": pid, "detail": detail, "executable": False, "read_only": True}
        for pid, detail in DO_NOT_DO_CATALOG
    ]
    return stored + catalog


def _operator_review_sequence(*, records: list[dict[str, Any]], orchestration: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "review_sequence_note")]
    sequencing = _sections(orchestration).get("operator_sequencing_recommendations") or []
    sequence: list[dict[str, Any]] = list(stored)
    for idx, row in enumerate(sequencing[:6]):
        sequence.append(
            {
                "sequence_step": idx + 1,
                "recommendation": row.get("recommendation"),
                "rationale": row.get("rationale"),
                "priority": row.get("priority", "medium"),
                "autonomous_execution": False,
                "read_only": True,
            }
        )
    if not sequence:
        sequence = [
            {"sequence_step": 1, "recommendation": "Review constitutional synthesis and tradeoffs.", "read_only": True},
            {"sequence_step": 2, "recommendation": "Compare institutional action options.", "read_only": True},
            {"sequence_step": 3, "recommendation": "Confirm required approvals and lane boundaries.", "read_only": True},
            {"sequence_step": 4, "recommendation": "Human selects path — planning does not execute.", "read_only": True},
        ]
    return sequence


def _mission_action_plan_artifact(
    *,
    records: list[dict[str, Any]],
    synthesis: dict[str, Any],
    orchestration: dict[str, Any],
    sections: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "mission_action_plan_artifact")]
    option_count = len(sections.get("action_option_generation") or [])
    approval_count = len(sections.get("required_approvals") or [])
    tradeoff_count = len(sections.get("constitutional_tradeoffs") or [])
    risk_count = len(sections.get("risks_and_blockers") or [])
    artifact = {
        "artifact_id": "mission-action-plan",
        "plan_id": synthesis.get("plan_id") or orchestration.get("plan_id"),
        "correlation_id": synthesis.get("correlation_id") or orchestration.get("correlation_id"),
        "action_option_count": option_count,
        "required_approval_count": approval_count,
        "constitutional_tradeoff_count": tradeoff_count,
        "risk_blocker_count": risk_count,
        "auto_path_selected": False,
        "execution_authority": False,
        "detail": "Mission action plan artifact — institutional action options for human-governed lane selection.",
        "recommendation_only": True,
        "read_only": True,
    }
    return stored + [artifact]


def build_mission_planning(*, session_id: str) -> MissionPlanningResult:
    sid = (session_id or "default").strip()[:64] or "default"

    synthesis_result = build_constitutional_synthesis(session_id=sid)
    orchestration_result = build_mission_orchestration(session_id=sid)
    strategy_result = build_mission_strategy(session_id=sid)
    readiness_result = build_mission_readiness_review(session_id=sid)

    synthesis = synthesis_result.constitutional_synthesis if synthesis_result.ok else {}
    orchestration = orchestration_result.orchestration if orchestration_result.ok else {}
    strategy = strategy_result.strategy if strategy_result.ok else {}
    readiness = readiness_result.review if readiness_result.ok else {}

    plan_id = str(
        synthesis.get("plan_id") or orchestration.get("plan_id") or readiness.get("plan_id") or ""
    ) or None
    correlation_id = str(
        synthesis.get("correlation_id") or orchestration.get("correlation_id") or readiness.get("correlation_id") or ""
    ) or None

    inbox = approval_inbox_payload(session_id=sid)
    records = list_mission_planning_records(session_id=sid, plan_id=plan_id)

    sections = {
        "action_option_generation": _action_option_generation(records=records, synthesis=synthesis),
        "option_comparison": _option_comparison(records=records, orchestration=orchestration, strategy=strategy),
        "lane_touch_mapping": _lane_touch_mapping(records=records, orchestration=orchestration),
        "required_approvals": _required_approvals(records=records, inbox=inbox),
        "constitutional_tradeoffs": _constitutional_tradeoffs(records=records, synthesis=synthesis),
        "risks_and_blockers": _risks_and_blockers(
            records=records, orchestration=orchestration, readiness=readiness
        ),
        "do_not_do_paths": _do_not_do_paths(records=records),
        "operator_review_sequence": _operator_review_sequence(records=records, orchestration=orchestration),
    }
    sections["mission_action_plan_artifact"] = _mission_action_plan_artifact(
        records=records,
        synthesis=synthesis,
        orchestration=orchestration,
        sections=sections,
    )

    mission_planning: dict[str, Any] = {
        "schema_version": MISSION_PLANNING_SCHEMA_VERSION,
        "fix": MISSION_PLANNING_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_164,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_164,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164,
        "autonomous_action_execution_enabled": AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_164,
        "auto_path_selection_enabled": AUTO_PATH_SELECTION_ENABLED_FIX_164,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_164,
        "pr_open_enabled": PR_OPEN_ENABLED_FIX_164,
        "merge_deploy_restart_enabled": MERGE_DEPLOY_RESTART_ENABLED_FIX_164,
        "invariant": MISSION_PLANNING_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "planning_record_count": len(records),
        "all_recommendations_executable": False,
        "mission_planning_cognition": True,
        "institutional_action_cognition": True,
        "planning_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in PLANNING_PRINCIPLES
        ],
        "sources": {
            "constitutional_synthesis": synthesis_result.ok,
            "mission_orchestration": orchestration_result.ok,
            "mission_strategy": strategy_result.ok,
            "mission_readiness_review": readiness_result.ok,
            "planning_records": len(records),
        },
    }
    return MissionPlanningResult(
        ok=True,
        session_id=sid,
        mission_planning=mission_planning,
        detail="Mission planning assembled (recommendation-only — no execution authority or autonomous path selection).",
    )

# SPDX-License-Identifier: Apache-2.0
"""FIX 360 / WORKSTREAM_H3 — strategic execution oversight executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_executor import (
    build_initiative_risk_planning_report,
    build_strategic_initiative_registry,
    compute_strategic_execution_metrics,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_store import (
    has_strategic_execution_review_approve,
    list_strategic_initiative_registry_entries,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_executor import (
    compute_strategic_direction_metrics,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_contract import (
    OVERSIGHT_INITIATIVE_MIN_SIZE,
    OVERSIGHT_MATURITY_LEVELS,
    RISK_MONITORING_FIX_MODULES,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_store import (
    has_strategic_oversight_review_approve,
    list_initiative_status_registry_entries,
    list_oversight_milestone_registry_entries,
    register_initiative_status,
    register_oversight_milestone,
)

DEFAULT_MILESTONES: tuple[str, ...] = (
    "planning_complete",
    "governance_ready",
    "execution_started",
    "outcome_measured",
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _approved_initiatives(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_strategic_initiative_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _milestones(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_oversight_milestone_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _statuses(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_initiative_status_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _status_for_initiative(*, program_session_id: str, initiative_id: str) -> str:
    for row in _statuses(program_session_id=program_session_id):
        if str(row.get("initiative_id") or "") == initiative_id:
            return str(row.get("status") or "monitoring")
    return "monitoring"


def _milestone_complete(status: str | None) -> bool:
    return str(status or "").lower() in {"complete", "completed", "passed", "done"}


def build_strategic_initiative_oversight_registry(*, program_session_id: str) -> dict[str, Any]:
    initiatives = _approved_initiatives(program_session_id=program_session_id)
    milestones = _milestones(program_session_id=program_session_id)
    statuses = _statuses(program_session_id=program_session_id)
    h2_metrics = compute_strategic_execution_metrics(program_session_id=program_session_id)

    oversight_items: list[dict[str, Any]] = []
    for initiative in initiatives:
        initiative_id = str(initiative.get("initiative_id") or "")
        initiative_milestones = [
            m for m in milestones if str(m.get("initiative_id") or "") == initiative_id
        ]
        if not initiative_milestones:
            initiative_milestones = [
                {
                    "initiative_id": initiative_id,
                    "milestone": name,
                    "status": "pending",
                    "default_milestone": True,
                }
                for name in DEFAULT_MILESTONES
            ]
        oversight_items.append(
            {
                "initiative_id": initiative_id,
                "growth_path": initiative.get("growth_path"),
                "objective": initiative.get("objective"),
                "success_criteria": initiative.get("success_criteria"),
                "initiative_status": _status_for_initiative(
                    program_session_id=program_session_id,
                    initiative_id=initiative_id,
                ),
                "milestones": initiative_milestones,
                "governance_state": "approved" if has_strategic_execution_review_approve(program_session_id=program_session_id) else "pending",
            }
        )

    return {
        "registry_id": "strategic-initiative-oversight-registry",
        "program_session_id": program_session_id,
        "initiative_count": len(initiatives),
        "minimum_initiative_count": OVERSIGHT_INITIATIVE_MIN_SIZE,
        "oversight_items": oversight_items,
        "status_entries": statuses,
        "execution_readiness_level_from_h2": h2_metrics.get("execution_readiness_level"),
        "workstream_h2_reference": {"workstream": "WORKSTREAM_H2", "composed_read_only": True},
        "initiative_monitoring_demonstrated": len(oversight_items) >= OVERSIGHT_INITIATIVE_MIN_SIZE,
        "read_only": True,
    }


def build_initiative_outcome_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_strategic_initiative_oversight_registry(program_session_id=program_session_id)
    outcomes: list[dict[str, Any]] = []

    for item in registry.get("oversight_items") or []:
        milestones = item.get("milestones") or []
        total = len(milestones) or 1
        completed = sum(1 for m in milestones if _milestone_complete(m.get("status")))
        progress = round(completed / total, 3)
        outcomes.append(
            {
                "initiative_id": item.get("initiative_id"),
                "objective_progress": progress,
                "milestones_completed": completed,
                "milestones_total": total,
                "expected_outcome": item.get("success_criteria"),
                "actual_outcome_status": "on_track" if progress >= 0.5 else "at_risk",
                "outcome_tracking_only": True,
            }
        )

    avg_progress = round(
        sum(float(o.get("objective_progress") or 0) for o in outcomes) / max(len(outcomes), 1),
        3,
    )

    return {
        "report_id": "initiative-outcome-report",
        "program_session_id": program_session_id,
        "outcomes": outcomes,
        "average_objective_progress": avg_progress,
        "outcome_tracking_demonstrated": bool(outcomes),
        "execution_performed": False,
        "read_only": True,
    }


def build_initiative_risk_monitoring_report(*, program_session_id: str) -> dict[str, Any]:
    h2_risk = build_initiative_risk_planning_report(program_session_id=program_session_id)
    outcomes = build_initiative_outcome_report(program_session_id=program_session_id)
    at_risk = sum(1 for o in outcomes.get("outcomes") or [] if o.get("actual_outcome_status") == "at_risk")

    fix_refs = {
        fix_id: {
            "module": fix_id,
            "monitoring_only": True,
            "execution_risk_reference": h2_risk.get("execution_risk_score"),
            "read_only": True,
        }
        for fix_id in RISK_MONITORING_FIX_MODULES
    }

    return {
        "report_id": "initiative-risk-monitoring-report",
        "program_session_id": program_session_id,
        "risk_monitoring_fix_modules": list(RISK_MONITORING_FIX_MODULES),
        "fix_module_references": [fix_refs[f] for f in RISK_MONITORING_FIX_MODULES],
        "workstream_h2_risk_reference": {
            "workstream": "WORKSTREAM_H2",
            "execution_risk_score": h2_risk.get("execution_risk_score"),
            "composed_read_only": True,
        },
        "initiatives_at_risk": at_risk,
        "risk_monitoring_demonstrated": True,
        "initiative_changes_performed": False,
        "read_only": True,
    }


def build_initiative_governance_monitoring_report(*, program_session_id: str) -> dict[str, Any]:
    h2_approved = has_strategic_execution_review_approve(program_session_id=program_session_id)
    h3_approved = has_strategic_oversight_review_approve(program_session_id=program_session_id)
    initiatives = _approved_initiatives(program_session_id=program_session_id)

    reviews_completed = int(h2_approved) + int(h3_approved)
    compliance = round(reviews_completed / 2, 3) if initiatives else 0.0
    approval_health = "healthy" if h2_approved and compliance >= 0.5 else "needs_review"

    return {
        "report_id": "initiative-governance-monitoring-report",
        "program_session_id": program_session_id,
        "review_completion_count": reviews_completed,
        "governance_compliance_score": compliance,
        "approval_health": approval_health,
        "h2_execution_review_complete": h2_approved,
        "h3_oversight_review_complete": h3_approved,
        "governance_bypass_performed": False,
        "milestone_governance_demonstrated": h2_approved,
        "read_only": True,
    }


def build_strategic_learning_report(*, program_session_id: str) -> dict[str, Any]:
    outcomes = build_initiative_outcome_report(program_session_id=program_session_id)
    governance = build_initiative_governance_monitoring_report(program_session_id=program_session_id)
    gaps = build_outcome_gap_report(program_session_id=program_session_id)

    successful: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    execution_lessons: list[dict[str, Any]] = []
    governance_lessons: list[dict[str, Any]] = []

    for outcome in outcomes.get("outcomes") or []:
        if outcome.get("actual_outcome_status") == "on_track":
            successful.append(
                {
                    "initiative_id": outcome.get("initiative_id"),
                    "pattern": "Milestone progress aligns with planned objectives",
                    "advisory_only": True,
                }
            )
        else:
            failed.append(
                {
                    "initiative_id": outcome.get("initiative_id"),
                    "pattern": "Milestone completion lagging planned objectives",
                    "advisory_only": True,
                }
            )
            execution_lessons.append(
                {
                    "lesson": "Increase milestone visibility before scaling initiative scope",
                    "advisory_only": True,
                }
            )

    if float(governance.get("governance_compliance_score") or 0) < 1.0:
        governance_lessons.append(
            {
                "lesson": "Complete H2 and H3 human reviews before claiming outcome governance",
                "advisory_only": True,
            }
        )

    if gaps.get("gap_count", 0) > 0:
        execution_lessons.append(
            {
                "lesson": "Close planned-vs-actual outcome gaps before adaptive strategy updates",
                "advisory_only": True,
            }
        )

    lesson_count = len(successful) + len(failed) + len(execution_lessons) + len(governance_lessons)
    return {
        "report_id": "strategic-learning-report",
        "program_session_id": program_session_id,
        "successful_patterns": successful,
        "failed_patterns": failed,
        "execution_lessons": execution_lessons,
        "governance_lessons": governance_lessons,
        "lesson_count": lesson_count,
        "strategic_learning_demonstrated": lesson_count > 0,
        "strategy_mutation_performed": False,
        "read_only": True,
    }


def build_outcome_gap_report(*, program_session_id: str) -> dict[str, Any]:
    outcomes = build_initiative_outcome_report(program_session_id=program_session_id)
    gaps: list[dict[str, Any]] = []

    for outcome in outcomes.get("outcomes") or []:
        progress = float(outcome.get("objective_progress") or 0)
        if progress < 1.0:
            gaps.append(
                {
                    "initiative_id": outcome.get("initiative_id"),
                    "planned_outcome": outcome.get("expected_outcome"),
                    "actual_progress": progress,
                    "gap": round(1.0 - progress, 3),
                    "category": "outcome_gap",
                }
            )

    return {
        "report_id": "outcome-gap-report",
        "program_session_id": program_session_id,
        "gap_count": len(gaps),
        "outcome_gaps": gaps,
        "outcome_gap_analysis_demonstrated": True,
        "read_only": True,
    }


def build_strategic_improvement_registry(*, program_session_id: str) -> dict[str, Any]:
    learning = build_strategic_learning_report(program_session_id=program_session_id)
    gaps = build_outcome_gap_report(program_session_id=program_session_id)
    governance = build_initiative_governance_monitoring_report(program_session_id=program_session_id)

    governance_improvements: list[dict[str, Any]] = []
    execution_improvements: list[dict[str, Any]] = []
    planning_improvements: list[dict[str, Any]] = []
    measurement_improvements: list[dict[str, Any]] = []

    for lesson in learning.get("governance_lessons") or []:
        governance_improvements.append({"improvement": lesson.get("lesson"), "advisory_only": True})

    for lesson in learning.get("execution_lessons") or []:
        execution_improvements.append({"improvement": lesson.get("lesson"), "advisory_only": True})

    if gaps.get("gap_count", 0) > 0:
        measurement_improvements.append(
            {
                "improvement": "Tighten milestone measurement cadence for outcome realization",
                "advisory_only": True,
            }
        )
        planning_improvements.append(
            {
                "improvement": "Align H2 success criteria with H3 milestone definitions",
                "advisory_only": True,
            }
        )

    if float(governance.get("governance_compliance_score") or 0) < 1.0:
        governance_improvements.append(
            {
                "improvement": "Maintain sequential H2 execution and H3 oversight review gates",
                "advisory_only": True,
            }
        )

    improvements = (
        governance_improvements
        + execution_improvements
        + planning_improvements
        + measurement_improvements
    )
    return {
        "registry_id": "strategic-improvement-registry",
        "program_session_id": program_session_id,
        "improvement_count": len(improvements),
        "governance_improvements": governance_improvements,
        "execution_improvements": execution_improvements,
        "planning_improvements": planning_improvements,
        "measurement_improvements": measurement_improvements,
        "automatic_initiative_changes_performed": False,
        "read_only": True,
    }


def _oversight_maturity_level(*, program_session_id: str, metrics: dict[str, Any]) -> str:
    if has_strategic_oversight_review_approve(program_session_id=program_session_id):
        if float(metrics.get("strategic_learning_score") or 0) >= 0.6:
            return "adaptive"
        return "learning" if float(metrics.get("strategic_learning_score") or 0) >= 0.4 else "measured"
    if float(metrics.get("outcome_realization_score") or 0) >= 0.5:
        return "measured"
    if float(metrics.get("governance_compliance_score") or 0) >= 0.5:
        return "governed"
    return "tracked"


def compute_strategic_oversight_metrics(*, program_session_id: str) -> dict[str, Any]:
    outcomes = build_initiative_outcome_report(program_session_id=program_session_id)
    governance = build_initiative_governance_monitoring_report(program_session_id=program_session_id)
    learning = build_strategic_learning_report(program_session_id=program_session_id)
    registry = build_strategic_initiative_oversight_registry(program_session_id=program_session_id)

    outcome_rows = outcomes.get("outcomes") or []
    on_track = sum(1 for o in outcome_rows if o.get("actual_outcome_status") == "on_track")
    initiative_success_rate = round(on_track / max(len(outcome_rows), 1), 3)

    total_milestones = sum(int(o.get("milestones_total") or 0) for o in outcome_rows)
    completed_milestones = sum(int(o.get("milestones_completed") or 0) for o in outcome_rows)
    milestone_completion_rate = round(
        completed_milestones / max(total_milestones, 1),
        3,
    )

    governance_compliance_score = float(governance.get("governance_compliance_score") or 0)
    outcome_realization_score = float(outcomes.get("average_objective_progress") or 0)
    strategic_learning_score = round(
        min(1.0, int(learning.get("lesson_count") or 0) / max(len(outcome_rows) * 2, 1)),
        3,
    )
    h1_leverage = float(compute_strategic_direction_metrics(program_session_id=program_session_id).get("strategic_leverage_score") or 0)

    metrics = {
        "initiative_success_rate": initiative_success_rate,
        "milestone_completion_rate": milestone_completion_rate,
        "governance_compliance_score": governance_compliance_score,
        "outcome_realization_score": outcome_realization_score,
        "strategic_learning_score": strategic_learning_score,
        "strategic_leverage_score": h1_leverage,
        "oversight_maturity_level": "",
        "oversight_maturity_levels": list(OVERSIGHT_MATURITY_LEVELS),
        "monitored_initiative_count": registry.get("initiative_count"),
        "read_only": True,
    }
    metrics["oversight_maturity_level"] = _oversight_maturity_level(
        program_session_id=program_session_id,
        metrics=metrics,
    )
    return metrics


def register_oversight_milestone_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    entry = register_oversight_milestone(
        entry={
            "initiative_id": kv.get("initiative_id") or kv.get("initiative") or "initiative-1",
            "program_session_id": program_session_id,
            "milestone": kv.get("milestone") or "outcome_measured",
            "status": kv.get("status") or "pending",
            "notes": kv.get("notes") or "",
        }
    )
    from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_store import (
        append_strategic_oversight_record,
    )

    append_strategic_oversight_record(
        session_id=program_session_id,
        kind="strategic_oversight_milestone_entry",
        content=body,
        metadata=entry,
    )
    return entry


def register_initiative_status_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    entry = register_initiative_status(
        entry={
            "initiative_id": kv.get("initiative_id") or kv.get("initiative") or "initiative-1",
            "program_session_id": program_session_id,
            "status": kv.get("status") or "monitoring",
        }
    )
    from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_store import (
        append_strategic_oversight_record,
    )

    append_strategic_oversight_record(
        session_id=program_session_id,
        kind="strategic_oversight_status_entry",
        content=body,
        metadata=entry,
    )
    return entry

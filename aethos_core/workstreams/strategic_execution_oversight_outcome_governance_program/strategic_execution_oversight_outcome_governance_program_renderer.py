# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H3 / FIX 360 — render strategic oversight deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_strategic_oversight_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    registry = _section(payload, "phase_1_strategic_initiative_oversight_registry", "strategic_initiative_oversight_registry") or {}
    lines = [
        "# Strategic Oversight Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_H3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 360')}",
        "",
        "## Core principle",
        "",
        "Strategic oversight evaluates outcomes. **Strategic oversight ≠ execution authority.**",
        "",
        f"- Oversight maturity level: **{metrics.get('oversight_maturity_level')}**",
        f"- Initiative success rate: **{metrics.get('initiative_success_rate')}**",
        f"- Milestone completion rate: **{metrics.get('milestone_completion_rate')}**",
        f"- Governance compliance score: **{metrics.get('governance_compliance_score')}**",
        f"- Monitored initiatives: **{registry.get('initiative_count')}**",
        f"- Execution authority: **{payload.get('execution_authority')}**",
    ]
    return "\n".join(lines)


def render_initiative_outcome_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_2_outcome_tracking_analysis", "initiative_outcome_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Initiative Outcome Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Average objective progress: **{report.get('average_objective_progress')}**",
        f"- Outcome realization score: **{metrics.get('outcome_realization_score')}**",
        f"- Outcome tracking demonstrated: **{report.get('outcome_tracking_demonstrated')}**",
    ]
    for outcome in report.get("outcomes") or []:
        lines.append(
            f"- **{outcome.get('initiative_id')}**: progress **{outcome.get('objective_progress')}**, "
            f"status **{outcome.get('actual_outcome_status')}**"
        )
    return "\n".join(lines)


def render_strategic_learning_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_strategic_learning_analysis", "strategic_learning_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Strategic Learning Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Strategic learning score: **{metrics.get('strategic_learning_score')}**",
        f"- Lesson count: **{report.get('lesson_count')}**",
        f"- Successful patterns: **{len(report.get('successful_patterns') or [])}**",
        f"- Failed patterns: **{len(report.get('failed_patterns') or [])}**",
        f"- Strategy mutation performed: **{payload.get('strategy_mutation')}**",
    ]
    for lesson in (report.get("execution_lessons") or [])[:5]:
        lines.append(f"- Execution lesson: {lesson.get('lesson')}")
    return "\n".join(lines)


def render_all_strategic_oversight_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "STRATEGIC_OVERSIGHT_REPORT.md": render_strategic_oversight_report(payload),
        "INITIATIVE_OUTCOME_REPORT.md": render_initiative_outcome_report(payload),
        "STRATEGIC_LEARNING_REPORT.md": render_strategic_learning_report(payload),
    }


def render_strategic_execution_oversight_outcome_governance_program(
    payload: dict[str, Any],
    *,
    focus: str = "strategic_oversight_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Strategic Execution Oversight & Outcome Governance",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_H3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 360')}",
        "",
        f"Maturity: **{metrics.get('oversight_maturity_level')}** · "
        f"Success rate: **{metrics.get('initiative_success_rate')}** · "
        f"Learning: **{metrics.get('strategic_learning_score')}**",
        "",
        "## Operator commands",
        "",
        "- `strategic oversight milestone: initiative_id=..., milestone=..., status=complete`",
        "- `strategic oversight status: initiative_id=..., status=monitoring`",
        "- `strategic oversight note: ...`",
        "- `strategic oversight review approve: ...`",
        "- `show strategic oversight dashboard`",
        "",
    ]
    return "\n".join(lines)

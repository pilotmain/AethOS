# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H2 / FIX 359 — render strategic execution deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_strategic_execution_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    registry = _section(payload, "phase_1_strategic_initiative_registry", "strategic_initiative_registry") or {}
    lines = [
        "# Strategic Execution Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_H2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 359')}",
        "",
        "## Core principle",
        "",
        "Strategic execution planning prepares execution. **Strategic execution planning ≠ strategic execution authority.**",
        "",
        f"- Execution readiness score: **{metrics.get('execution_readiness_score')}**",
        f"- Execution readiness level: **{metrics.get('execution_readiness_level')}**",
        f"- Initiative readiness score: **{metrics.get('initiative_readiness_score')}**",
        f"- Governance readiness score: **{metrics.get('governance_readiness_score')}**",
        f"- Strategic leverage score: **{metrics.get('strategic_leverage_score')}**",
        f"- Initiatives registered: **{registry.get('initiative_count')}**",
        f"- Execution authority: **{payload.get('execution_authority')}**",
    ]
    return "\n".join(lines)


def render_initiative_dependency_analysis(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_3_dependency_analysis", "initiative_dependency_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Initiative Dependency Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Total dependencies: **{report.get('total_dependency_count')}**",
        f"- Dependency complexity score: **{metrics.get('dependency_complexity_score')}**",
        f"- Dependency analysis demonstrated: **{report.get('dependency_analysis_demonstrated')}**",
    ]
    for item in report.get("initiative_dependencies") or []:
        lines.append(
            f"- **{item.get('initiative_id')}**: {item.get('dependency_count')} dependencies"
        )
    return "\n".join(lines)


def render_execution_readiness_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    success = payload.get("success_criteria") or {}
    governance = _section(payload, "phase_6_governance_readiness_analysis", "initiative_governance_readiness_report") or {}
    lines = [
        "# Execution Readiness Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Execution readiness score: **{metrics.get('execution_readiness_score')}**",
        f"- Execution readiness level: **{metrics.get('execution_readiness_level')}**",
        f"- Governance readiness score: **{governance.get('governance_readiness_score')}**",
        f"- Execution readiness assessed: **{success.get('execution_readiness_assessed')}**",
        f"- Program complete: **{success.get('program_complete')}**",
        f"- Budget allocation performed: **{payload.get('budget_allocation')}**",
        f"- Initiative launch performed: **{payload.get('initiative_launch')}**",
    ]
    return "\n".join(lines)


def render_all_strategic_execution_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "STRATEGIC_EXECUTION_REPORT.md": render_strategic_execution_report(payload),
        "INITIATIVE_DEPENDENCY_ANALYSIS.md": render_initiative_dependency_analysis(payload),
        "EXECUTION_READINESS_REPORT.md": render_execution_readiness_report(payload),
    }


def render_governed_strategic_execution_program(
    payload: dict[str, Any],
    *,
    focus: str = "strategic_execution_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Governed Strategic Execution Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_H2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 359')}",
        "",
        f"Readiness: **{metrics.get('execution_readiness_score')}** · "
        f"Level: **{metrics.get('execution_readiness_level')}** · "
        f"Governance: **{metrics.get('governance_readiness_score')}**",
        "",
        "## Operator commands",
        "",
        "- `strategic execution initiative: initiative_id=..., growth_path=..., objective=...`",
        "- `strategic execution note: ...`",
        "- `strategic execution review approve: ...`",
        "- `show strategic execution dashboard`",
        "",
    ]
    return "\n".join(lines)

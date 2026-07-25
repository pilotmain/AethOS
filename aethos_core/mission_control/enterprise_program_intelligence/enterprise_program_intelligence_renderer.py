# SPDX-License-Identifier: Apache-2.0
"""FIX 327 — enterprise program intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_enterprise_program_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "enterprise_program_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "program_registry":
        registry = (sections.get("program_registry") or [{}])[0]
        lines = ["## Program registry", ""]
        for program in registry.get("programs") or []:
            lines.append(f"- **{program.get('entity_type')}**: {program.get('name')}")
        return "\n".join(lines)

    if focus == "program_dependency_report":
        report = (sections.get("program_dependency_report") or [{}])[0]
        lines = ["## Program dependencies", "", "### Dependencies", ""]
        for dep in report.get("dependencies") or []:
            lines.append(f"- {dep.get('from_program')} → {dep.get('to_program')}")
        lines.extend(["", "### Blockers", ""])
        for blocker in report.get("blockers") or []:
            lines.append(f"- {blocker.get('program')}: {blocker.get('blocker')}")
        lines.extend(["", "### Critical path", ""])
        for step in report.get("critical_path") or []:
            lines.append(f"- {step}")
        return "\n".join(lines)

    if focus == "program_health_report":
        report = (sections.get("program_health_report") or [{}])[0]
        lines = ["## Program health", ""]
        for program in report.get("programs") or []:
            lines.append(f"- **{program.get('name')}** — {program.get('health_status')}")
        return "\n".join(lines)

    if focus == "program_progress_report":
        report = (sections.get("program_progress_report") or [{}])[0]
        return "\n".join(
            [
                "## Program progress",
                "",
                f"- Completion trend: **{report.get('completion_trend', 'unknown')}**",
                f"- Average completion: **{report.get('average_completion_percent', 0)}%**",
                f"- Execution confidence: **{report.get('execution_confidence', 'medium')}**",
            ]
        )

    if focus == "program_risk_report":
        report = (sections.get("program_risk_report") or [{}])[0]
        lines = ["## Program risk", ""]
        for risk in report.get("program_risks") or []:
            lines.append(f"- {risk.get('risk_signal')}")
        return "\n".join(lines) if len(lines) > 2 else "## Program risk\n\n(no elevated program risks)"

    if focus == "program_alignment_report":
        report = (sections.get("program_alignment_report") or [{}])[0]
        lines = ["## Program alignment", "", f"- Alignment score: **{report.get('alignment_score', 0)}**", ""]
        for row in report.get("aligned_rows") or []:
            lines.append(f"- **{row.get('goal')}** → {', '.join(row.get('programs') or [])}")
        return "\n".join(lines)

    if focus == "program_opportunity_registry":
        registry = (sections.get("program_opportunity_registry") or [{}])[0]
        lines = ["## Program opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('opportunity_type')})")
        return "\n".join(lines)

    if focus == "program_priority_matrix":
        matrix = (sections.get("program_priority_matrix") or [{}])[0]
        lines = ["## Program priority matrix", ""]
        for row in matrix.get("ranked_programs") or []:
            lines.append(f"- **{row.get('name')}** — score {row.get('priority_score')}")
        return "\n".join(lines) if len(lines) > 2 else "## Program priority matrix\n\n(no ranked programs)"

    dashboard = (sections.get("enterprise_program_dashboard") or [{}])[0]
    lines = [
        "## Enterprise program dashboard",
        "",
        f"- Programs: **{dashboard.get('program_count', 0)}**",
        f"- Healthy / blocked / at risk: **{dashboard.get('healthy_program_count', 0)}** / "
        f"**{dashboard.get('blocked_program_count', 0)}** / **{dashboard.get('at_risk_program_count', 0)}**",
        f"- Dependencies / blockers: **{dashboard.get('dependency_count', 0)}** / **{dashboard.get('blocker_count', 0)}**",
        f"- Alignment score: **{dashboard.get('alignment_score', 0)}**",
        f"- Top priority program: **{dashboard.get('top_priority_program', 'unknown')}**",
        "",
        "## Privacy",
        "",
        "Enterprise program intelligence ≠ program execution authority. Humans execute programs.",
    ]
    return "\n".join(lines)

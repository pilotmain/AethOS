# SPDX-License-Identifier: Apache-2.0
"""FIX 328 — organizational effectiveness intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_organizational_effectiveness_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "organizational_effectiveness_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "organizational_structure_registry":
        registry = (sections.get("organizational_structure_registry") or [{}])[0]
        return "\n".join(
            [
                "## Organizational structure",
                "",
                f"- Organizations: **{registry.get('organization_count', 0)}**",
                f"- Workspaces: **{registry.get('workspace_count', 0)}**",
                f"- Roles tracked: **{len(registry.get('roles') or [])}**",
            ]
        )

    if focus == "governance_friction_report":
        report = (sections.get("governance_friction_report") or [{}])[0]
        lines = ["## Governance friction", "", "### Approval delays", ""]
        for item in report.get("approval_delays") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Review delays", ""])
        for item in report.get("review_delays") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Bottlenecks", ""])
        for item in report.get("governance_bottlenecks") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "coordination_intelligence_report":
        report = (sections.get("coordination_intelligence_report") or [{}])[0]
        lines = ["## Coordination intelligence", "", "### Failures", ""]
        for item in report.get("coordination_failures") or []:
            lines.append(f"- {item}")
        return "\n".join(lines) if len(lines) > 3 else "## Coordination intelligence\n\n(no coordination failures detected)"

    if focus == "organizational_capacity_report":
        report = (sections.get("organizational_capacity_report") or [{}])[0]
        return "\n".join(
            [
                "## Organizational capacity",
                "",
                f"- Active initiatives: **{report.get('active_initiative_count', 0)}**",
                f"- Active programs: **{report.get('active_program_count', 0)}**",
                f"- Operational burden: **{report.get('operational_burden', 0)}**",
                f"- Review burden: **{report.get('review_burden', 0)}**",
                f"- Capacity constrained: **{report.get('capacity_constrained', False)}**",
            ]
        )

    if focus == "decision_velocity_report":
        report = (sections.get("decision_velocity_report") or [{}])[0]
        return "\n".join(
            [
                "## Decision velocity",
                "",
                f"- Review velocity: **{report.get('review_velocity', 0)}**",
                f"- Decision latency: **{report.get('decision_latency', 'medium')}**",
                f"- Approval throughput: **{report.get('approval_throughput', 0)}**",
            ]
        )

    if focus == "organizational_risk_report":
        report = (sections.get("organizational_risk_report") or [{}])[0]
        lines = ["## Organizational risk", ""]
        for category in ("execution_risk", "dependency_risk", "governance_risk", "operational_risk"):
            lines.extend([f"### {category.replace('_', ' ').title()}", ""])
            for item in report.get(category) or []:
                if isinstance(item, dict):
                    lines.append(f"- {item.get('title') or item.get('risk_signal') or item}")
                else:
                    lines.append(f"- {item}")
            lines.append("")
        return "\n".join(lines)

    if focus == "organizational_opportunity_registry":
        registry = (sections.get("organizational_opportunity_registry") or [{}])[0]
        lines = ["## Organizational opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('opportunity_type')})")
        return "\n".join(lines)

    if focus == "organizational_effectiveness_scorecard":
        scorecard = (sections.get("organizational_effectiveness_scorecard") or [{}])[0]
        lines = [
            "## Organizational effectiveness scorecard",
            "",
            f"- Overall level: **{scorecard.get('overall_level', 'STABLE')}**",
            f"- Overall score: **{scorecard.get('overall_score', 0)}**",
            "",
        ]
        for dim in scorecard.get("dimensions") or []:
            level = (scorecard.get("dimension_levels") or {}).get(dim, "STABLE")
            score = (scorecard.get("dimension_scores") or {}).get(dim, 0)
            lines.append(f"- **{dim}**: {level} ({score})")
        return "\n".join(lines)

    dashboard = (sections.get("organizational_effectiveness_dashboard") or [{}])[0]
    lines = [
        "## Organizational effectiveness dashboard",
        "",
        f"- Friction signals: **{dashboard.get('friction_signal_count', 0)}**",
        f"- Governance bottlenecks: **{dashboard.get('governance_bottleneck_count', 0)}**",
        f"- Coordination failures: **{dashboard.get('coordination_failure_count', 0)}**",
        f"- Capacity constrained: **{dashboard.get('capacity_constrained', False)}**",
        f"- Overall effectiveness: **{dashboard.get('overall_effectiveness_level', 'STABLE')}**",
        "",
        "## Privacy",
        "",
        "Organizational effectiveness intelligence ≠ organizational authority. Humans manage organizations.",
    ]
    return "\n".join(lines)

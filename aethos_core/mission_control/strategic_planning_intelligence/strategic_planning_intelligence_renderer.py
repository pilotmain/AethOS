# SPDX-License-Identifier: Apache-2.0
"""FIX 326 — strategic planning intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_strategic_planning_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "strategic_planning_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "strategic_planning_registry":
        registry = (sections.get("strategic_planning_registry") or [{}])[0]
        return "\n".join(
            [
                "## Strategic planning registry",
                "",
                f"- Active plans: **{registry.get('active_count', 0)}**",
                f"- Proposed plans: **{registry.get('proposed_count', 0)}**",
                f"- Archived plans: **{registry.get('archived_count', 0)}**",
            ]
        )

    if focus == "strategic_scenario_report":
        report = (sections.get("strategic_scenario_report") or [{}])[0]
        lines = ["## Strategic scenarios", ""]
        for scenario in report.get("scenarios") or []:
            lines.append(
                f"- **{scenario.get('title')}** — projected value "
                f"**{scenario.get('projected_value_score', 0)}** ({scenario.get('timeline')})"
            )
        return "\n".join(lines)

    if focus == "scenario_impact_report":
        report = (sections.get("scenario_impact_report") or [{}])[0]
        lines = ["## Scenario impact", ""]
        for impact in report.get("impacts") or []:
            lines.append(
                f"- **{impact.get('title')}** — customer {impact.get('customer_impact')}, "
                f"commercial {impact.get('commercial_impact')}"
            )
        return "\n".join(lines)

    if focus == "strategic_risk_forecast":
        report = (sections.get("strategic_risk_forecast") or [{}])[0]
        lines = ["## Strategic risk forecast", ""]
        for category in ("operational_risks", "commercial_risks", "adoption_risks", "execution_risks"):
            lines.extend([f"### {category.replace('_', ' ').title()}", ""])
            for item in report.get(category) or []:
                lines.append(f"- {item}")
            lines.append("")
        return "\n".join(lines)

    if focus == "strategic_opportunity_forecast":
        report = (sections.get("strategic_opportunity_forecast") or [{}])[0]
        lines = ["## Strategic opportunity forecast", ""]
        for category in ("growth_opportunities", "expansion_opportunities", "efficiency_opportunities"):
            lines.extend([f"### {category.replace('_', ' ').title()}", ""])
            for item in report.get(category) or []:
                lines.append(f"- {item.get('title')}")
            lines.append("")
        return "\n".join(lines)

    if focus == "resource_planning_report":
        report = (sections.get("resource_planning_report") or [{}])[0]
        return "\n".join(
            [
                "## Resource planning",
                "",
                f"- Engineering allocation: **{report.get('engineering_allocation', 0)}**",
                f"- Operational allocation: **{report.get('operational_allocation', 0)}**",
                f"- Support allocation: **{report.get('support_allocation', 0)}**",
                f"- Investment allocation: **{report.get('investment_allocation', 0)}**",
            ]
        )

    if focus == "strategic_plan_registry":
        registry = (sections.get("strategic_plan_registry") or [{}])[0]
        lines = ["## Strategic plans", ""]
        for plan in registry.get("plans") or []:
            lines.append(
                f"- **{plan.get('scenario')}** — confidence **{plan.get('confidence', 0)}**"
            )
        lines.append("", "Planning options only — humans choose plans.")
        return "\n".join(lines)

    if focus == "strategic_comparison_matrix":
        matrix = (sections.get("strategic_comparison_matrix") or [{}])[0]
        lines = ["## Strategic comparison matrix", ""]
        strongest = matrix.get("strongest_plan") or {}
        if strongest:
            lines.append(
                f"Strongest plan: **{strongest.get('scenario')}** "
                f"(score **{strongest.get('comparison_score', 0)}**)"
            )
            lines.append("")
        for row in matrix.get("comparisons") or []:
            lines.append(
                f"- **{row.get('scenario')}** — value {row.get('value')}, risk {row.get('risk')}, "
                f"confidence {row.get('confidence')}, timeline {row.get('timeline')}"
            )
        return "\n".join(lines)

    dashboard = (sections.get("strategic_planning_dashboard") or [{}])[0]
    lines = [
        "## Strategic planning dashboard",
        "",
        f"- Scenarios: **{dashboard.get('scenario_count', 0)}**",
        f"- Generated plans: **{dashboard.get('generated_plan_count', 0)}**",
        f"- Growth opportunities: **{dashboard.get('growth_opportunity_count', 0)}**",
        f"- Operational risks: **{dashboard.get('operational_risk_count', 0)}**",
        f"- Strongest plan: **{dashboard.get('strongest_plan', 'unknown')}**",
        f"- Strongest plan score: **{dashboard.get('strongest_plan_score', 0)}**",
        "",
        "## Privacy",
        "",
        "Strategic planning intelligence ≠ strategic execution authority. Humans choose plans.",
    ]
    return "\n".join(lines)

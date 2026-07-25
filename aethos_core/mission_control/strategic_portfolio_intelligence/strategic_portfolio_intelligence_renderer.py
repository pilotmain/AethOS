# SPDX-License-Identifier: Apache-2.0
"""FIX 324 — strategic portfolio intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_strategic_portfolio_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "strategic_portfolio_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "portfolio_asset_registry":
        registry = (sections.get("portfolio_asset_registry") or [{}])[0]
        lines = ["## Portfolio assets", ""]
        for asset in registry.get("assets") or []:
            lines.append(f"- **{asset.get('asset_type')}**: {asset.get('name')}")
        return "\n".join(lines)

    if focus == "strategic_value_report":
        report = (sections.get("strategic_value_report") or [{}])[0]
        return "\n".join(
            [
                "## Strategic value",
                "",
                f"- Strategic value: **{report.get('strategic_value_score', 0)}**",
                f"- Customer value: **{report.get('customer_value_score', 0)}**",
                f"- Business value: **{report.get('business_value_score', 0)}**",
                f"- PMF level: **{report.get('pmf_level', 'UNKNOWN')}**",
                f"- Value realization: **{report.get('value_realization_level', 'UNKNOWN')}**",
            ]
        )

    if focus == "investment_opportunity_report":
        report = (sections.get("investment_opportunity_report") or [{}])[0]
        lines = ["## Investment opportunities", "", "### High value", ""]
        for item in report.get("high_value_opportunities") or []:
            lines.append(f"- {item.get('title')}")
        lines.extend(["", "### Underinvested", ""])
        for item in report.get("underinvested_areas") or []:
            lines.append(f"- {item.get('title')}")
        return "\n".join(lines)

    if focus == "portfolio_risk_report":
        report = (sections.get("portfolio_risk_report") or [{}])[0]
        lines = ["## Portfolio risk", ""]
        for category in ("operational_risk", "product_risk", "customer_risk", "commercial_risk"):
            lines.extend([f"### {category.replace('_', ' ').title()}", ""])
            for item in report.get(category) or []:
                lines.append(f"- {item}")
            lines.append("")
        return "\n".join(lines)

    if focus == "resource_allocation_report":
        report = (sections.get("resource_allocation_report") or [{}])[0]
        return "\n".join(
            [
                "## Resource allocation",
                "",
                f"- Engineering effort: **{report.get('engineering_effort_units', 0)}**",
                f"- Operational effort: **{report.get('operational_effort_units', 0)}**",
                f"- Support effort: **{report.get('support_effort_units', 0)}**",
            ]
        )

    if focus == "strategic_alignment_report":
        report = (sections.get("strategic_alignment_report") or [{}])[0]
        lines = ["## Strategic alignment", "", "### Goals", ""]
        for item in report.get("goals") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Initiatives", ""])
        for item in report.get("initiatives") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "portfolio_opportunity_registry":
        registry = (sections.get("portfolio_opportunity_registry") or [{}])[0]
        lines = ["## Portfolio opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('opportunity_type')})")
        lines.append("", "Recommendations only — no automatic strategy execution.")
        return "\n".join(lines)

    if focus == "strategic_priority_matrix":
        matrix = (sections.get("strategic_priority_matrix") or [{}])[0]
        lines = ["## Strategic priority matrix", ""]
        for opp in matrix.get("ranked_opportunities") or []:
            lines.append(f"- **{opp.get('title')}** — score {opp.get('priority_score')}")
        return "\n".join(lines) if len(lines) > 2 else "## Strategic priority matrix\n\n(no ranked opportunities)"

    dashboard = (sections.get("strategic_portfolio_dashboard") or [{}])[0]
    lines = [
        "## Strategic portfolio dashboard",
        "",
        f"- Portfolio assets: **{dashboard.get('portfolio_asset_count', 0)}**",
        f"- Business value score: **{dashboard.get('business_value_score', 0)}**",
        f"- High-value opportunities: **{dashboard.get('high_value_opportunity_count', 0)}**",
        f"- Underinvested areas: **{dashboard.get('underinvested_area_count', 0)}**",
        f"- Operational / customer risks: **{dashboard.get('operational_risk_count', 0)}** / **{dashboard.get('customer_risk_count', 0)}**",
        f"- Alignment nodes: **{dashboard.get('alignment_node_count', 0)}**",
        f"- Portfolio opportunities: **{dashboard.get('portfolio_opportunity_count', 0)}**",
        "",
        "## Privacy",
        "",
        "Strategic portfolio intelligence ≠ executive authority. Tenant isolation preserved.",
    ]
    return "\n".join(lines)

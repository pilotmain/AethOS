# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_executive_decision_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "executive_decision_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "executive_decision_registry":
        registry = (sections.get("executive_decision_registry") or [{}])[0]
        lines = [
            "## Executive decision registry",
            "",
            f"- Pending: **{registry.get('pending_count', 0)}**",
            f"- Reviewed: **{registry.get('reviewed_count', 0)}**",
            f"- Deferred: **{registry.get('deferred_count', 0)}**",
        ]
        return "\n".join(lines)

    if focus == "decision_opportunity_report":
        report = (sections.get("decision_opportunity_report") or [{}])[0]
        lines = ["## Decision opportunities", "", "### High value", ""]
        for item in report.get("high_value_opportunities") or []:
            lines.append(f"- {item.get('title')}")
        lines.extend(["", "### High urgency", ""])
        for item in report.get("high_urgency_opportunities") or []:
            lines.append(f"- {item.get('title')}")
        return "\n".join(lines)

    if focus == "decision_risk_report":
        report = (sections.get("decision_risk_report") or [{}])[0]
        lines = ["## Decision risk", "", "### Highest risk decisions", ""]
        for item in report.get("highest_risk_decisions") or []:
            lines.append(f"- {item.get('title')}")
        return "\n".join(lines) if len(lines) > 3 else "## Decision risk\n\n(no elevated risk decisions)"

    if focus == "executive_recommendation_report":
        report = (sections.get("executive_recommendation_report") or [{}])[0]
        lines = ["## Executive recommendations", ""]
        for rec in report.get("recommendations") or []:
            lines.append(f"- **{rec.get('recommendation_level')}**: {rec.get('title')}")
        lines.append("", "Recommendations only — humans decide.")
        return "\n".join(lines)

    if focus == "tradeoff_analysis_report":
        report = (sections.get("tradeoff_analysis_report") or [{}])[0]
        lines = ["## Trade-off analysis", ""]
        for row in report.get("tradeoffs") or []:
            lines.append(
                f"- **{row.get('title')}** — value {row.get('value')}, effort {row.get('effort')}, "
                f"risk {row.get('risk')}, confidence {row.get('confidence')}"
            )
        return "\n".join(lines)

    if focus == "executive_alignment_report":
        report = (sections.get("executive_alignment_report") or [{}])[0]
        return "\n".join(
            [
                "## Executive alignment",
                "",
                f"- Goal alignment: **{report.get('goal_alignment_score', 0)}**",
                f"- Portfolio alignment: **{report.get('portfolio_alignment_score', 0)}**",
                f"- Investment alignment: **{report.get('investment_alignment_score', 0)}**",
            ]
        )

    if focus == "executive_opportunity_registry":
        registry = (sections.get("executive_opportunity_registry") or [{}])[0]
        lines = ["## Executive opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('source_type')})")
        return "\n".join(lines)

    if focus == "executive_priority_matrix":
        matrix = (sections.get("executive_priority_matrix") or [{}])[0]
        lines = ["## Executive priority matrix", ""]
        for row in matrix.get("ranked_decisions") or []:
            lines.append(f"- **{row.get('title')}** — score {row.get('priority_score')}")
        return "\n".join(lines) if len(lines) > 2 else "## Executive priority matrix\n\n(no ranked decisions)"

    dashboard = (sections.get("executive_decision_dashboard") or [{}])[0]
    lines = [
        "## Executive decision dashboard",
        "",
        f"- Pending decisions: **{dashboard.get('pending_decision_count', 0)}**",
        f"- Recommendations: **{dashboard.get('recommendation_count', 0)}**",
        f"- High urgency opportunities: **{dashboard.get('high_urgency_opportunity_count', 0)}**",
        f"- Highest risk decisions: **{dashboard.get('highest_risk_decision_count', 0)}**",
        f"- Goal alignment score: **{dashboard.get('goal_alignment_score', 0)}**",
        f"- Top recommendation: **{dashboard.get('top_recommendation_level', 'REVIEW')}**",
        "",
        "## Privacy",
        "",
        "Executive decision intelligence ≠ executive authority. AethOS recommends; humans decide.",
    ]
    return "\n".join(lines)

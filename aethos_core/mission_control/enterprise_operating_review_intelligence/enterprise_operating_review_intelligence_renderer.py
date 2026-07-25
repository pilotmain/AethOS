# SPDX-License-Identifier: Apache-2.0
"""FIX 329 — enterprise operating review intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_enterprise_operating_review_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "enterprise_operating_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "executive_operating_snapshot":
        snapshot = (sections.get("executive_operating_snapshot") or [{}])[0]
        state = snapshot.get("current_state") or {}
        lines = [
            "## Executive operating snapshot",
            "",
            f"- Business value: **{state.get('business_value_score', 0)}**",
            f"- Pending decisions: **{state.get('pending_decisions', 0)}**",
            f"- Programs: **{state.get('program_count', 0)}**",
            f"- Effectiveness: **{state.get('effectiveness_level', 'STABLE')}**",
            "",
            "### Major risks",
            "",
        ]
        for item in snapshot.get("major_risks") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Major opportunities", ""])
        for item in snapshot.get("major_opportunities") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Major decisions", ""])
        for item in snapshot.get("major_decisions") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "strategic_health_review":
        review = (sections.get("strategic_health_review") or [{}])[0]
        lines = ["## Strategic health review", ""]
        for dim, score in (review.get("dimensions") or {}).items():
            lines.append(f"- **{dim}**: {score}")
        return "\n".join(lines)

    if focus == "program_health_review":
        review = (sections.get("program_health_review") or [{}])[0]
        return "\n".join(
            [
                "## Program health review",
                "",
                f"- Healthy: **{review.get('healthy_count', 0)}**",
                f"- At risk: **{review.get('at_risk_count', 0)}**",
                f"- Blocked: **{review.get('blocked_count', 0)}**",
            ]
        )

    if focus == "organizational_health_review":
        review = (sections.get("organizational_health_review") or [{}])[0]
        lines = ["## Organizational health review", ""]
        for dim, score in (review.get("dimensions") or {}).items():
            lines.append(f"- **{dim}**: {score}")
        lines.append(f"- Overall: **{review.get('overall_level', 'STABLE')}**")
        return "\n".join(lines)

    if focus == "enterprise_risk_review":
        review = (sections.get("enterprise_risk_review") or [{}])[0]
        lines = ["## Enterprise risk review", ""]
        for category in ("strategic_risks", "program_risks", "organizational_risks", "operational_risks"):
            lines.extend([f"### {category.replace('_', ' ').title()}", ""])
            for item in review.get(category) or []:
                lines.append(f"- {item}")
            lines.append("")
        return "\n".join(lines)

    if focus == "enterprise_opportunity_review":
        review = (sections.get("enterprise_opportunity_review") or [{}])[0]
        lines = ["## Enterprise opportunity review", ""]
        for opp in review.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('source')})")
        return "\n".join(lines)

    if focus == "executive_action_registry":
        registry = (sections.get("executive_action_registry") or [{}])[0]
        lines = ["## Executive action registry", "", "Advisory actions only — humans make decisions.", ""]
        for action in registry.get("actions") or []:
            lines.append(f"- **{action.get('action_type')}**: {action.get('title')}")
        return "\n".join(lines)

    if focus == "executive_operating_scorecard":
        scorecard = (sections.get("executive_operating_scorecard") or [{}])[0]
        lines = [
            "## Executive operating scorecard",
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

    dashboard = (sections.get("enterprise_operating_dashboard") or [{}])[0]
    lines = [
        "## Enterprise operating dashboard",
        "",
        f"- Overall operating level: **{dashboard.get('overall_operating_level', 'STABLE')}**",
        f"- Major risks: **{dashboard.get('major_risk_count', 0)}**",
        f"- Major opportunities: **{dashboard.get('major_opportunity_count', 0)}**",
        f"- Executive actions: **{dashboard.get('executive_action_count', 0)}**",
        f"- Healthy / blocked programs: **{dashboard.get('healthy_program_count', 0)}** / **{dashboard.get('blocked_program_count', 0)}**",
        "",
        "## Privacy",
        "",
        "Enterprise operating review intelligence ≠ executive authority. Humans make decisions.",
    ]
    return "\n".join(lines)

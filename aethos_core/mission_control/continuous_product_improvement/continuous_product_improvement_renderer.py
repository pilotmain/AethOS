# SPDX-License-Identifier: Apache-2.0
"""FIX 317 — continuous product improvement renderer."""

from __future__ import annotations

from typing import Any


def render_continuous_product_improvement(payload: dict[str, Any], *, focus: str = "continuous_improvement_dashboard") -> str:
    sections = payload.get("sections") or {}

    if focus == "improvement_priority_matrix":
        matrix = (sections.get("improvement_priority_matrix") or [{}])[0]
        lines = ["## Improvement priority matrix", ""]
        for row in matrix.get("ranked_opportunities") or []:
            lines.append(
                f"- **{row.get('title', '—')}** — impact `{row.get('impact')}`, effort `{row.get('effort')}`, "
                f"score `{row.get('priority_score')}`"
            )
        lines.extend(["", "Recommendations only — no automatic backlog or feature creation."])
        return "\n".join(lines)

    if focus == "feedback_intelligence_report":
        report = (sections.get("feedback_intelligence_report") or [{}])[0]
        lines = ["## Feedback intelligence", ""]
        for opp in (report.get("opportunities") or [])[:8]:
            lines.append(f"- {opp.get('title')}")
        return "\n".join(lines) if len(lines) > 2 else "## Feedback intelligence\n\n(no signals)"

    if focus == "onboarding_improvement_report":
        report = (sections.get("onboarding_improvement_report") or [{}])[0]
        lines = ["## Onboarding improvement", ""]
        for point in report.get("friction_points") or []:
            lines.append(f"- {point}")
        for opp in (report.get("opportunities") or [])[:6]:
            lines.append(f"- {opp.get('title')}")
        return "\n".join(lines) if len(lines) > 2 else "## Onboarding improvement\n\n(no friction points)"

    if focus == "operational_improvement_report":
        report = (sections.get("operational_improvement_report") or [{}])[0]
        lines = ["## Operational improvement", ""]
        for opp in (report.get("opportunities") or [])[:8]:
            lines.append(f"- {opp.get('title')}")
        return "\n".join(lines) if len(lines) > 2 else "## Operational improvement\n\n(no recurring blockers)"

    if focus == "governance_improvement_report":
        report = (sections.get("governance_improvement_report") or [{}])[0]
        lines = ["## Governance improvement", ""]
        for opp in (report.get("opportunities") or [])[:8]:
            lines.append(f"- {opp.get('title')}")
        return "\n".join(lines) if len(lines) > 2 else "## Governance improvement\n\n(no friction signals)"

    if focus == "commercial_improvement_report":
        report = (sections.get("commercial_improvement_report") or [{}])[0]
        lines = ["## Commercial improvement", ""]
        for opp in (report.get("opportunities") or [])[:8]:
            lines.append(f"- {opp.get('title')}")
        return "\n".join(lines) if len(lines) > 2 else "## Commercial improvement\n\n(no commercial friction signals)"

    dashboard = (sections.get("continuous_improvement_dashboard") or [{}])[0]
    lines = [
        "## Continuous improvement dashboard",
        "",
        f"- Opportunities identified: **{dashboard.get('opportunity_count', 0)}**",
        f"- Top opportunity: **{dashboard.get('top_opportunity') or '—'}**",
        f"- Feedback signals: **{dashboard.get('feedback_signals', 0)}**",
        f"- Onboarding friction points: **{dashboard.get('onboarding_friction_points', 0)}**",
        f"- Operational blockers: **{dashboard.get('operational_blockers', 0)}**",
        f"- Commercial friction signals: **{dashboard.get('commercial_friction_signals', 0)}**",
        "",
        "## Core principle",
        "",
        str(dashboard.get("core_principle") or "improvement_recommendations ≠ automatic_execution"),
        "",
        "Humans decide what to pursue. AethOS does not create work automatically.",
    ]
    return "\n".join(lines)

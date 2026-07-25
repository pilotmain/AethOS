# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — growth & adoption intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_growth_adoption_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "growth_adoption_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "adoption_registry":
        registry = (sections.get("adoption_registry") or [{}])[0]
        lines = [
            "## Adoption registry",
            "",
            f"- Activated customers: **{registry.get('activated_customers', 0)}**",
            "",
            "### Adopted capabilities",
            "",
        ]
        for item in registry.get("adopted_capabilities") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Adopted providers", ""])
        for item in registry.get("adopted_providers") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Adopted channels", ""])
        for item in registry.get("adopted_channels") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "adoption_analytics_report":
        report = (sections.get("adoption_analytics_report") or [{}])[0]
        return "\n".join(
            [
                "## Adoption analytics",
                "",
                f"- Adoption rate: **{report.get('adoption_rate_percent', 0)}%**",
                f"- Adoption velocity score: **{report.get('adoption_velocity_score', 0)}**",
                f"- Adoption completion: **{report.get('adoption_completion_percent', 0)}%**",
                f"- Provider adoption count: **{report.get('provider_adoption_count', 0)}**",
            ]
        )

    if focus == "retention_intelligence_report":
        report = (sections.get("retention_intelligence_report") or [{}])[0]
        lines = [
            "## Retention intelligence",
            "",
            f"- Retained customers: **{report.get('retained_customers', 0)}**",
            f"- Disengaged customers: **{report.get('disengaged_customers', 0)}**",
            f"- Retention trend: **{report.get('retention_trend', 'stable')}**",
            "",
            "### Retention cohorts",
            "",
        ]
        for cohort in report.get("retention_cohorts") or []:
            lines.append(f"- **{cohort.get('cohort')}**: {cohort.get('count', 0)}")
        return "\n".join(lines)

    if focus == "expansion_intelligence_report":
        report = (sections.get("expansion_intelligence_report") or [{}])[0]
        lines = [
            "## Expansion intelligence",
            "",
            f"- Workspace growth: **{report.get('workspace_growth', 0)}**",
            f"- Project growth: **{report.get('project_growth', 0)}**",
            "",
            "### Plan expansion paths",
            "",
        ]
        for item in report.get("plan_expansion") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Upgrade candidates", ""])
        for item in report.get("upgrade_candidates") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "success_pattern_report":
        report = (sections.get("success_pattern_report") or [{}])[0]
        lines = ["## Success patterns", "", "### Behaviors linked to success", ""]
        for item in report.get("behaviors_linked_to_success") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Onboarding paths linked to retention", ""])
        for item in report.get("onboarding_paths_linked_to_retention") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Provider usage linked to success", ""])
        for item in report.get("provider_usage_linked_to_success") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "churn_risk_report":
        report = (sections.get("churn_risk_report") or [{}])[0]
        lines = [
            "## Churn risk intelligence",
            "",
            f"- Churn risk score: **{report.get('churn_risk_score', 0)}**",
            f"- At-risk count: **{report.get('at_risk_count', 0)}**",
            "",
            "### Disengagement patterns",
            "",
        ]
        for item in report.get("disengagement_patterns") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Adoption failures", ""])
        for item in report.get("adoption_failures") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "growth_opportunity_registry":
        registry = (sections.get("growth_opportunity_registry") or [{}])[0]
        lines = ["## Growth opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('opportunity_type')})")
        lines.append("", "Recommendations only — no automatic growth execution.")
        return "\n".join(lines)

    if focus == "growth_priority_matrix":
        matrix = (sections.get("growth_priority_matrix") or [{}])[0]
        lines = ["## Growth priority matrix", ""]
        for opp in matrix.get("ranked_opportunities") or []:
            lines.append(f"- **{opp.get('title')}** — ROI {opp.get('roi_score')}")
        return "\n".join(lines) if len(lines) > 2 else "## Growth priority matrix\n\n(no ranked opportunities)"

    dashboard = (sections.get("growth_adoption_dashboard") or [{}])[0]
    lines = [
        "## Growth & adoption dashboard",
        "",
        f"- Activated customers: **{dashboard.get('activated_customers', 0)}**",
        f"- Adoption rate / velocity: **{dashboard.get('adoption_rate_percent', 0)}%** / **{dashboard.get('adoption_velocity_score', 0)}**",
        f"- Retained / disengaged: **{dashboard.get('retained_customers', 0)}** / **{dashboard.get('disengaged_customers', 0)}**",
        f"- Workspace / project growth: **{dashboard.get('workspace_growth', 0)}** / **{dashboard.get('project_growth', 0)}**",
        f"- Churn risk score: **{dashboard.get('churn_risk_score', 0)}**",
        f"- Growth opportunities: **{dashboard.get('growth_opportunity_count', 0)}**",
        "",
        "## Privacy",
        "",
        "Growth intelligence ≠ growth execution. Tenant isolation preserved.",
    ]
    return "\n".join(lines)

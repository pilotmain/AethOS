# SPDX-License-Identifier: Apache-2.0
"""FIX 323 — customer value realization intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_customer_value_realization_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "customer_value_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "value_outcome_registry":
        registry = (sections.get("value_outcome_registry") or [{}])[0]
        lines = ["## Value outcomes", ""]
        for outcome in registry.get("outcomes") or []:
            lines.append(f"- **{outcome.get('category')}**: {outcome.get('detail')}")
        return "\n".join(lines)

    if focus == "expected_value_registry":
        registry = (sections.get("expected_value_registry") or [{}])[0]
        lines = ["## Expected value", ""]
        for item in registry.get("expectations") or []:
            lines.append(f"- **{item.get('source')}**: {item.get('detail')}")
        return "\n".join(lines)

    if focus == "value_gap_report":
        report = (sections.get("value_gap_report") or [{}])[0]
        lines = ["## Value gaps", ""]
        for gap in report.get("gaps") or []:
            lines.append(f"- Expected: {gap.get('expected_value')} | Gap: {gap.get('value_gap')}")
        return "\n".join(lines) if len(lines) > 2 else "## Value gaps\n\n(no gaps identified)"

    if focus == "capability_value_report":
        report = (sections.get("capability_value_report") or [{}])[0]
        lines = ["## Capability value", "", "### Highest value capabilities", ""]
        for item in report.get("highest_value_capabilities") or []:
            lines.append(f"- **{item.get('capability')}** ({item.get('value_signal')})")
        return "\n".join(lines)

    if focus == "journey_value_report":
        report = (sections.get("journey_value_report") or [{}])[0]
        lines = ["## Journey value", "", "### Highest value journeys", ""]
        for item in report.get("highest_value_journeys") or []:
            lines.append(f"- **{item.get('journey')}** ({item.get('value_signal')})")
        return "\n".join(lines)

    if focus == "customer_success_outcome_report":
        report = (sections.get("customer_success_outcome_report") or [{}])[0]
        return "\n".join(
            [
                "## Customer success outcomes",
                "",
                f"- Successful: **{report.get('successful_customers', 0)}**",
                f"- Partially successful: **{report.get('partially_successful_customers', 0)}**",
                f"- Unsuccessful: **{report.get('unsuccessful_customers', 0)}**",
            ]
        )

    if focus == "value_opportunity_registry":
        registry = (sections.get("value_opportunity_registry") or [{}])[0]
        lines = ["## Value opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('opportunity_type')})")
        lines.append("", "Recommendations only — no automatic customer success execution.")
        return "\n".join(lines)

    if focus == "value_realization_scorecard":
        scorecard = (sections.get("value_realization_scorecard") or [{}])[0]
        lines = [
            "## Value realization scorecard",
            "",
            f"- Overall: **{scorecard.get('overall_level', 'UNKNOWN')}** ({scorecard.get('overall_score', 0)})",
            "",
        ]
        for dim, score in (scorecard.get("dimensions") or {}).items():
            level = (scorecard.get("dimension_levels") or {}).get(dim, "UNKNOWN")
            lines.append(f"- **{dim.replace('_', ' ').title()}**: {level} ({score})")
        return "\n".join(lines)

    dashboard = (sections.get("customer_value_dashboard") or [{}])[0]
    lines = [
        "## Customer value dashboard",
        "",
        f"- Realized / expected outcomes: **{dashboard.get('realized_outcome_count', 0)}** / **{dashboard.get('expected_outcome_count', 0)}**",
        f"- Value gaps: **{dashboard.get('value_gap_count', 0)}**",
        f"- Highest-value capabilities: **{dashboard.get('highest_value_capability_count', 0)}**",
        f"- Highest-value journeys: **{dashboard.get('highest_value_journey_count', 0)}**",
        f"- Successful / partial / unsuccessful: **{dashboard.get('successful_customers', 0)}** / **{dashboard.get('partially_successful_customers', 0)}** / **{dashboard.get('unsuccessful_customers', 0)}**",
        f"- Value realization level: **{dashboard.get('value_realization_level', 'UNKNOWN')}** ({dashboard.get('value_realization_score', 0)})",
        f"- Value opportunities: **{dashboard.get('value_opportunity_count', 0)}**",
        "",
        "## Privacy",
        "",
        "Value realization intelligence ≠ customer success authority. Tenant isolation preserved.",
    ]
    return "\n".join(lines)

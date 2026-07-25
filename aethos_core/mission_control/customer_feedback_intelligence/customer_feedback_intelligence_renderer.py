# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — customer feedback intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_customer_feedback_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "customer_feedback_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "feedback_classification_report":
        report = (sections.get("feedback_classification_report") or [{}])[0]
        lines = ["## Feedback classification", ""]
        for label, count in (report.get("counts_by_classification") or {}).items():
            lines.append(f"- **{label}**: {count}")
        return "\n".join(lines)

    if focus == "feedback_sentiment_report":
        report = (sections.get("feedback_sentiment_report") or [{}])[0]
        lines = ["## Feedback sentiment", ""]
        for label, count in (report.get("counts_by_sentiment") or {}).items():
            lines.append(f"- **{label}**: {count}")
        return "\n".join(lines)

    if focus == "feedback_trend_report":
        report = (sections.get("feedback_trend_report") or [{}])[0]
        lines = [
            "## Feedback trends",
            "",
            "### Recurring requests",
            "",
        ]
        for item in report.get("recurring_requests") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Recurring complaints", ""])
        for item in report.get("recurring_complaints") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Emerging themes", ""])
        for item in report.get("emerging_themes") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "capability_gap_report":
        report = (sections.get("capability_gap_report") or [{}])[0]
        lines = ["## Capability gaps", ""]
        for gap in report.get("gaps") or []:
            lines.append(f"- {gap.get('requested_capability')}")
        if len(lines) <= 2:
            lines.append("- (no capability gaps identified)")
        return "\n".join(lines)

    if focus == "customer_friction_report":
        report = (sections.get("customer_friction_report") or [{}])[0]
        lines = [
            "## Customer friction",
            "",
            "### Onboarding friction",
            "",
        ]
        for item in report.get("onboarding_friction") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Provider friction", ""])
        for item in report.get("provider_friction") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Adoption friction", ""])
        for item in report.get("adoption_friction") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "feedback_opportunity_registry":
        registry = (sections.get("feedback_opportunity_registry") or [{}])[0]
        lines = ["## Feedback opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('classification')})")
        lines.append("", "Recommendations only — no automatic work creation.")
        return "\n".join(lines)

    if focus == "feedback_priority_matrix":
        matrix = (sections.get("feedback_priority_matrix") or [{}])[0]
        lines = ["## Feedback priority matrix", ""]
        for opp in matrix.get("ranked_opportunities") or []:
            lines.append(f"- **{opp.get('title')}** — score {opp.get('priority_score')}")
        return "\n".join(lines) if len(lines) > 2 else "## Feedback priority matrix\n\n(no ranked opportunities)"

    dashboard = (sections.get("customer_feedback_dashboard") or [{}])[0]
    lines = [
        "## Customer feedback dashboard",
        "",
        f"- Feedback items: **{dashboard.get('feedback_item_count', 0)}**",
        f"- Positive / negative sentiment: **{dashboard.get('positive_sentiment_count', 0)}** / **{dashboard.get('negative_sentiment_count', 0)}**",
        f"- Recurring requests / complaints: **{dashboard.get('recurring_request_count', 0)}** / **{dashboard.get('recurring_complaint_count', 0)}**",
        f"- Emerging themes: **{dashboard.get('emerging_theme_count', 0)}**",
        f"- Capability gaps: **{dashboard.get('capability_gap_count', 0)}**",
        f"- Onboarding / provider friction: **{dashboard.get('onboarding_friction_count', 0)}** / **{dashboard.get('provider_friction_count', 0)}**",
        f"- Opportunities ranked: **{dashboard.get('opportunity_count', 0)}**",
        "",
        "## Privacy",
        "",
        "Feedback intelligence ≠ customer authority. Tenant boundaries preserved.",
    ]
    return "\n".join(lines)

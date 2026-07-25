# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — product analytics renderer."""

from __future__ import annotations

from typing import Any


def render_product_analytics_foundation(payload: dict[str, Any], *, focus: str = "analytics_dashboard") -> str:
    sections = payload.get("sections") or {}

    if focus == "onboarding_analytics_report":
        report = (sections.get("onboarding_analytics_report") or [{}])[0]
        lines = [
            "## Onboarding analytics",
            "",
            f"- Users completed onboarding: **{report.get('users_completed_onboarding', 0)}**",
            f"- Average completion rate: **{report.get('average_completion_rate_percent', 0)}%**",
            "",
            "### Drop-off points",
            "",
        ]
        for point in report.get("drop_off_points") or []:
            lines.append(f"- {point}")
        if len(lines) <= 6:
            lines.append("- (no drop-off points recorded)")
        return "\n".join(lines)

    if focus == "capability_usage_report":
        report = (sections.get("capability_usage_report") or [{}])[0]
        lines = ["## Capability usage", "", "### Most used", ""]
        for item in report.get("capabilities_used") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Ignored or low adoption", ""])
        for item in report.get("capabilities_ignored") or []:
            lines.append(f"- {item}")
        return "\n".join(lines) if len(lines) > 4 else "## Capability usage\n\n(no capability signals)"

    if focus == "provider_analytics_report":
        report = (sections.get("provider_analytics_report") or [{}])[0]
        adoption = report.get("provider_adoption") or {}
        lines = ["## Provider analytics", ""]
        for provider, count in adoption.items():
            lines.append(f"- **{provider.title()}**: {count} connections")
        lines.append(f"- Most connected: **{report.get('most_connected_provider') or '—'}**")
        return "\n".join(lines)

    if focus == "commercial_analytics_report":
        report = (sections.get("commercial_analytics_report") or [{}])[0]
        lines = ["## Commercial analytics", ""]
        for plan in report.get("most_successful_plans") or report.get("plan_adoption") or []:
            lines.append(f"- {plan}")
        lines.append(f"- Active subscriptions: **{report.get('active_subscription_count', 0)}**")
        return "\n".join(lines) if len(lines) > 2 else "## Commercial analytics\n\n(no plan signals)"

    if focus == "customer_success_analytics_report":
        report = (sections.get("customer_success_analytics_report") or [{}])[0]
        return "\n".join(
            [
                "## Customer success analytics",
                "",
                f"- Healthy customers: **{report.get('healthy_customers', 0)}**",
                f"- At-risk customers: **{report.get('at_risk_customers', 0)}**",
            ]
        )

    if focus == "behavioral_opportunity_registry":
        registry = (sections.get("behavioral_opportunity_registry") or [{}])[0]
        lines = ["## Behavioral opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('signal')}**: {opp.get('detail')}")
        lines.append("", "Recommendations only — no automatic behavior modification.")
        return "\n".join(lines) if len(lines) > 2 else "## Behavioral opportunities\n\n(no opportunities)"

    if focus == "user_journey_report":
        report = (sections.get("user_journey_report") or [{}])[0]
        predictors = report.get("success_predictors") or []
        lines = ["## User journey analytics", "", "### Success predictors", ""]
        for item in predictors:
            lines.append(f"- {item}")
        return "\n".join(lines)

    dashboard = (sections.get("analytics_dashboard") or [{}])[0]
    lines = [
        "## Analytics dashboard",
        "",
        f"- Onboarding completion: **{dashboard.get('onboarding_completion_rate_percent', 0)}%**",
        f"- Users completed onboarding: **{dashboard.get('users_completed_onboarding', 0)}**",
        f"- Most connected provider: **{dashboard.get('most_connected_provider') or '—'}**",
        f"- Capabilities used: **{dashboard.get('capabilities_used_count', 0)}**",
        f"- Active subscriptions: **{dashboard.get('active_subscription_count', 0)}**",
        f"- Healthy / at-risk customers: **{dashboard.get('healthy_customers', 0)}** / **{dashboard.get('at_risk_customers', 0)}**",
        f"- Behavioral opportunities: **{dashboard.get('behavioral_opportunity_count', 0)}**",
        "",
        "## Privacy",
        "",
        "Analytics visibility ≠ user surveillance. Tenant isolation preserved.",
    ]
    return "\n".join(lines)

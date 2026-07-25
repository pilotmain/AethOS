# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard renderer."""

from __future__ import annotations

from typing import Any


def render_executive_operating_system_dashboard(
    payload: dict[str, Any],
    *,
    focus: str = "executive_operating_system_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "executive_summary_panel":
        panel = (sections.get("executive_summary_panel") or [{}])[0]
        health = panel.get("overall_health") or {}
        launch = panel.get("launch_state") or {}
        lines = [
            "## Executive summary panel",
            "",
            f"- Operating level: **{health.get('operating_level', 'STABLE')}**",
            f"- Business value: **{health.get('business_value_score', 0)}**",
            f"- Launch status: **{launch.get('overall_launch_status', 'UNKNOWN')}**",
            "",
            "### Major alerts",
            "",
        ]
        for item in panel.get("major_alerts") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "strategy_panel":
        panel = (sections.get("strategy_panel") or [{}])[0]
        lines = ["## Strategy panel", "", "### Top priorities", ""]
        for item in panel.get("top_priorities") or []:
            lines.append(f"- {item.get('title') if isinstance(item, dict) else item}")
        lines.extend(["", "### Strategic risks", ""])
        for item in panel.get("strategic_risks") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "program_panel":
        panel = (sections.get("program_panel") or [{}])[0]
        return "\n".join(
            [
                "## Program panel",
                "",
                f"- Active programs: **{panel.get('active_program_count', 0)}**",
                f"- Blocked programs: **{panel.get('blocked_program_count', 0)}**",
                f"- Critical dependencies: **{len(panel.get('critical_dependencies') or [])}**",
            ]
        )

    if focus == "organization_panel":
        panel = (sections.get("organization_panel") or [{}])[0]
        effectiveness = panel.get("effectiveness") or {}
        return "\n".join(
            [
                "## Organization panel",
                "",
                f"- Effectiveness: **{effectiveness.get('overall_level', 'STABLE')}**",
                f"- Friction signals: **{effectiveness.get('friction_signal_count', 0)}**",
                f"- Capacity level: **{(panel.get('capacity') or {}).get('capacity_level', 'STABLE')}**",
            ]
        )

    if focus == "customer_panel":
        panel = (sections.get("customer_panel") or [{}])[0]
        adoption = panel.get("adoption") or {}
        retention = panel.get("retention") or {}
        pmf = panel.get("pmf") or {}
        value = panel.get("value_realization") or {}
        health = panel.get("customer_health") or {}
        return "\n".join(
            [
                "## Customer panel",
                "",
                f"- Activated customers: **{adoption.get('activated_customers', 0)}**",
                f"- Retained customers: **{retention.get('retained_customers', 0)}**",
                f"- PMF fit: **{pmf.get('fit_level', 'UNKNOWN')}**",
                f"- Value realization: **{value.get('realization_level', 'UNKNOWN')}**",
                f"- Customer health: **{health.get('health_level', 'STABLE')}**",
            ]
        )

    if focus == "operations_panel":
        panel = (sections.get("operations_panel") or [{}])[0]
        deploy = panel.get("deploy_health") or {}
        incidents = panel.get("incidents") or {}
        recovery = panel.get("recovery_status") or {}
        return "\n".join(
            [
                "## Operations panel",
                "",
                f"- Deploy readiness: **{deploy.get('readiness_level', 'REVIEW')}**",
                f"- Monitoring health: **{deploy.get('monitoring_health', 'UNKNOWN')}**",
                f"- Incident classification: **{incidents.get('classification', 'UNKNOWN')}**",
                f"- Recovery stage: **{recovery.get('recovery_stage', 'observation')}**",
                f"- Operations status: **{panel.get('operations_status', 'MONITORING')}**",
            ]
        )

    if focus == "commercial_panel":
        panel = (sections.get("commercial_panel") or [{}])[0]
        subs = panel.get("subscription_health") or {}
        monetization = panel.get("monetization_readiness") or {}
        return "\n".join(
            [
                "## Commercial panel",
                "",
                f"- Active subscriptions: **{subs.get('active_subscriptions', 0)}**",
                f"- Payment readiness: **{monetization.get('payment_readiness_level', 'REVIEW')}**",
                f"- Commercial risks: **{len(panel.get('commercial_risks') or [])}**",
            ]
        )

    if focus == "portfolio_panel":
        panel = (sections.get("portfolio_panel") or [{}])[0]
        return "\n".join(
            [
                "## Portfolio panel",
                "",
                f"- Products tracked: **{len(panel.get('products') or [])}**",
                f"- Initiatives: **{len(panel.get('initiatives') or [])}**",
                f"- Investment opportunities: **{len(panel.get('investment_opportunities') or [])}**",
                f"- Business value score: **{panel.get('business_value_score', 0)}**",
            ]
        )

    dashboard = (sections.get("executive_operating_system_dashboard") or [{}])[0]
    lines = [
        "## Executive operating system dashboard",
        "",
        f"- Operating level: **{dashboard.get('overall_operating_level', 'STABLE')}**",
        f"- Launch status: **{dashboard.get('launch_status', 'UNKNOWN')}**",
        f"- Customer health: **{dashboard.get('customer_health_level', 'STABLE')}**",
        f"- Blocked programs: **{dashboard.get('program_blocked_count', 0)}**",
        f"- Organization: **{dashboard.get('organization_effectiveness_level', 'STABLE')}**",
        f"- Operations: **{dashboard.get('operations_status', 'MONITORING')}**",
        f"- PMF: **{dashboard.get('pmf_fit_level', 'UNKNOWN')}**",
        "",
        "### Executive attention",
        "",
    ]
    for item in dashboard.get("executive_attention_items") or []:
        lines.append(f"- {item.get('title')}")
    return "\n".join(lines)

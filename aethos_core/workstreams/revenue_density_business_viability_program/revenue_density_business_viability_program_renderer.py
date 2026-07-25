# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G3 / FIX 356 — render revenue density deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_revenue_density_report(payload: dict[str, Any]) -> str:
    revenue = _section(payload, "phase_5_revenue_signal_analysis", "revenue_signal_report") or {}
    plan_util = _section(payload, "phase_2_plan_utilization_analysis", "plan_utilization_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Revenue Density Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_G3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 356')}",
        "",
        "## Core principle",
        "",
        "Revenue density measures business signals. **Revenue density ≠ commercial authority.**",
        "",
        f"- Revenue density score: **{metrics.get('revenue_density_score')}**",
        f"- Plan utilization score: **{metrics.get('plan_utilization_score')}**",
        f"- Active value signals: **{revenue.get('active_value_signals')}**",
        f"- Recurring value signals: **{revenue.get('recurring_value_signals')}**",
        f"- Expansion signals: **{revenue.get('expansion_signals')}**",
        f"- Plan engagement: **{plan_util.get('plan_engagement_demonstrated')}**",
        f"- Payment processing: **{payload.get('payment_processing')}**",
    ]
    return "\n".join(lines)


def render_business_viability_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    success = payload.get("success_criteria") or {}
    revenue = _section(payload, "phase_5_revenue_signal_analysis", "revenue_signal_report") or {}
    lines = [
        "# Business Viability Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Business viability score: **{metrics.get('business_viability_score')}**",
        f"- Retention strength: **{metrics.get('retention_strength')}**",
        f"- Adoption strength: **{metrics.get('adoption_strength')}**",
        f"- Expansion score: **{metrics.get('expansion_score')}**",
        f"- Sustainable value signals: **{success.get('sustainable_value_signals')}**",
        f"- Revenue maturity: **{revenue.get('revenue_maturity_distribution')}**",
        f"- Billing execution: **{payload.get('billing_execution')}**",
    ]
    return "\n".join(lines)


def render_expansion_signal_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_3_expansion_potential_analysis", "expansion_potential_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Expansion Signal Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Expansion score: **{metrics.get('expansion_score')}**",
        f"- Workspace growth: **{report.get('workspace_growth')}**",
        f"- Project growth: **{report.get('project_growth')}**",
        f"- Provider growth: **{report.get('provider_growth')}**",
        f"- Plan upgrade indicators: **{report.get('plan_upgrade_indicators')}**",
        f"- Plan upgrade performed: **{report.get('plan_upgrade_performed')}**",
    ]
    return "\n".join(lines)


def render_all_revenue_density_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "REVENUE_DENSITY_REPORT.md": render_revenue_density_report(payload),
        "BUSINESS_VIABILITY_REPORT.md": render_business_viability_report(payload),
        "EXPANSION_SIGNAL_REPORT.md": render_expansion_signal_report(payload),
    }


def render_revenue_density_business_viability_program(
    payload: dict[str, Any],
    *,
    focus: str = "business_viability_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Revenue Density & Business Viability Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_G3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 356')}",
        "",
        f"Viability: **{metrics.get('business_viability_score')}** · "
        f"Revenue density: **{metrics.get('revenue_density_score')}** · "
        f"Expansion: **{metrics.get('expansion_score')}**",
        "",
        "## Operator commands",
        "",
        "- `revenue density cohort: customer_id=..., plan=PRO, customer_session_id=..., segment=startup`",
        "- `revenue density note: ...`",
        "- `revenue density review approve: ...`",
        "- `show business viability dashboard`",
        "",
    ]
    return "\n".join(lines)

# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F6 / FIX 352 — render business sustainability deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_business_sustainability_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    metrics = payload.get("metrics") or {}
    cohort = _section(payload, "phase_1_economic_cohort_registry", "economic_cohort_registry") or {}
    lines = [
        "# Business Sustainability Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F6')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 352')}",
        "",
        "## Core principle",
        "",
        "Economic validation measures sustainability signals. "
        "**Economic validation ≠ commercial authority.**",
        "",
        f"- Cohort size: **{cohort.get('cohort_size', 0)}**",
        f"- Delivery cost (units): **{metrics.get('delivery_cost')}**",
        f"- Support cost (units): **{metrics.get('support_cost')}**",
        f"- Sustainability score: **{metrics.get('sustainability_score')}**",
        f"- Operational efficiency: **{metrics.get('operational_efficiency_score')}**",
        f"- Billing execution: **{payload.get('billing_execution')}**",
        f"- Platform economics sustainable: **{success.get('sustainable_platform_economics')}**",
    ]
    return "\n".join(lines)


def render_unit_economics_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_unit_economics_analysis", "unit_economics_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Unit Economics Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Estimated value delivered: **{report.get('estimated_value_delivered_score')}**",
        f"- Estimated operating cost (units): **{report.get('estimated_operating_cost_units')}**",
        f"- Estimated support burden (units): **{report.get('estimated_support_burden_units')}**",
        f"- Sustainability score: **{metrics.get('sustainability_score')}**",
        f"- Value-to-cost ratio: **{report.get('value_to_cost_ratio')}**",
        f"- Financial forecasting as fact: **{report.get('financial_forecasting_presented_as_fact')}**",
    ]
    return "\n".join(lines)


def render_retention_economics_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_retention_economics", "retention_economics_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Retention Economics Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Retention strength: **{metrics.get('retention_strength')}**",
        f"- Expansion strength: **{metrics.get('expansion_strength')}**",
        f"- Expansion likelihood: **{report.get('expansion_likelihood')}**",
        f"- Churn indicators: **{len(report.get('churn_indicators') or [])}**",
        f"- Retention economics sustainable: **{report.get('retention_economics_sustainable')}**",
    ]
    return "\n".join(lines)


def render_all_business_sustainability_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "BUSINESS_SUSTAINABILITY_REPORT.md": render_business_sustainability_report(payload),
        "UNIT_ECONOMICS_REPORT.md": render_unit_economics_report(payload),
        "RETENTION_ECONOMICS_REPORT.md": render_retention_economics_report(payload),
    }


def render_unit_economics_business_sustainability_program(
    payload: dict[str, Any],
    *,
    focus: str = "business_sustainability_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Unit Economics & Business Sustainability Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F6')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 352')}",
        "",
        f"Sustainability: **{metrics.get('sustainability_score')}** · "
        f"Delivery cost: **{metrics.get('delivery_cost')}** · "
        f"Retention: **{metrics.get('retention_strength')}**",
        "",
        "## Operator commands",
        "",
        "- `business sustainability cohort: customer_id=..., plan=PRO, segment=startup, customer_session_id=...`",
        "- `business sustainability note: ...`",
        "- `business sustainability review approve: ...`",
        "- `show business sustainability dashboard`",
        "",
    ]
    return "\n".join(lines)

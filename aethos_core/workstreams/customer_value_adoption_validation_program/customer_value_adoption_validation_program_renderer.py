# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F2 / FIX 348 — render customer value & adoption validation deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_customer_adoption_validation_report(payload: dict[str, Any]) -> str:
    adoption = _section(payload, "phase_3_adoption_analysis", "customer_adoption_report") or {}
    usage = _section(payload, "phase_2_usage_observation", "customer_usage_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Customer Adoption Validation Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 348')}",
        "",
        "## Core principle",
        "",
        "AethOS measures outcomes without influencing customers. "
        "**Value validation ≠ customer manipulation.**",
        "",
        f"- First use: **{adoption.get('first_use')}**",
        f"- Repeat use: **{adoption.get('repeat_use')}**",
        f"- Active usage: **{adoption.get('active_usage')}**",
        f"- Adoption rate: **{metrics.get('adoption_rate')}**",
        f"- Repeat usage rate: **{metrics.get('repeat_usage_rate')}**",
        f"- Usage observations: **{usage.get('observation_count', 0)}**",
    ]
    return "\n".join(lines)


def render_customer_value_validation_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_value_validation", "customer_value_validation_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Customer Value Validation Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Value aligned: **{report.get('value_aligned')}**",
        f"- Value realization score: **{metrics.get('value_realization_score')}**",
        f"- Expected goal: **{(report.get('expected_value') or {}).get('goal', '—')}**",
        f"- Observed repeat use: **{(report.get('observed_value') or {}).get('repeat_use')}**",
        f"- Customer manipulation performed: **{report.get('customer_manipulation_performed')}**",
    ]
    return "\n".join(lines)


def render_customer_retention_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_retention_intelligence", "customer_retention_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Customer Retention Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Continued usage: **{report.get('continued_usage')}**",
        f"- Declining usage: **{report.get('declining_usage')}**",
        f"- Dormant usage: **{report.get('dormant_usage')}**",
        f"- Retention rate: **{metrics.get('retention_rate')}**",
        f"- Abandonment rate: **{metrics.get('abandonment_rate')}**",
        f"- Satisfaction trend: **{metrics.get('customer_satisfaction_trend')}**",
    ]
    return "\n".join(lines)


def render_all_customer_value_adoption_validation_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "CUSTOMER_ADOPTION_VALIDATION_REPORT.md": render_customer_adoption_validation_report(payload),
        "CUSTOMER_VALUE_VALIDATION_REPORT.md": render_customer_value_validation_report(payload),
        "CUSTOMER_RETENTION_REPORT.md": render_customer_retention_report(payload),
    }


def render_customer_value_adoption_validation_program(
    payload: dict[str, Any],
    *,
    focus: str = "customer_value_dashboard",
) -> str:
    dashboard = _section(payload, "phase_8_executive_visibility", "customer_value_dashboard") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Customer Value & Adoption Validation Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 348')}",
        "",
        f"Adoption rate: **{metrics.get('adoption_rate')}** · "
        f"Retention rate: **{metrics.get('retention_rate')}** · "
        f"Value score: **{metrics.get('value_realization_score')}**",
        "",
        "## Operator commands",
        "",
        "- `customer usage observation: workflow=..., executions=..., endpoint=...`",
        "- `customer value note: ...`",
        "- `customer value review approve: ...`",
        "- `show customer value dashboard`",
        "",
        f"Executive modules: `{', '.join(dashboard.get('executive_fix_modules') or [])}`",
        "",
    ]
    return "\n".join(lines)

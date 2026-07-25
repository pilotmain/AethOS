# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F5 / FIX 351 — render commercial validation deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_commercial_validation_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    metrics = payload.get("metrics") or {}
    cohort = _section(payload, "phase_1_commercial_cohort_registry", "commercial_cohort_registry") or {}
    lines = [
        "# Commercial Validation Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F5')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 351')}",
        "",
        "## Core principle",
        "",
        "Commercial validation measures business outcomes. "
        "**Commercial validation ≠ commercial authority.**",
        "",
        f"- Cohort size: **{cohort.get('cohort_size', 0)}**",
        f"- Activation rate: **{metrics.get('activation_rate')}**",
        f"- Retention rate: **{metrics.get('retention_rate')}**",
        f"- Expansion rate: **{metrics.get('expansion_rate')}**",
        f"- Commercial sustainability: **{metrics.get('commercial_sustainability_score')}**",
        f"- Payment processing: **{payload.get('payment_processing')}**",
        f"- Plan attractiveness: **{success.get('plan_attractiveness_demonstrated')}**",
    ]
    return "\n".join(lines)


def render_commercial_retention_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_3_retention_analysis", "commercial_retention_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Commercial Retention Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Retention rate: **{metrics.get('retention_rate')}**",
        f"- Value realization score: **{metrics.get('value_realization_score')}**",
        f"- Churn indicators: **{len(report.get('churn_indicators') or [])}**",
        f"- Retention by plan demonstrated: **{report.get('retention_by_plan_demonstrated')}**",
    ]
    for row in report.get("plans") or []:
        lines.append(
            f"- Plan **{row.get('plan')}**: retention **{row.get('retention_rate')}**, "
            f"value **{row.get('value_realization_score')}**"
        )
    return "\n".join(lines)


def render_value_to_revenue_analysis(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_value_to_revenue_analysis", "value_to_revenue_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Value to Revenue Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Plan alignment rate: **{report.get('commercial_plan_alignment_rate')}**",
        f"- Value realization score: **{metrics.get('value_realization_score')}**",
        f"- Plan conversion: **{metrics.get('plan_conversion')}**",
        f"- Billing mutation performed: **{report.get('billing_mutation_performed')}**",
    ]
    return "\n".join(lines)


def render_all_commercial_validation_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "COMMERCIAL_VALIDATION_REPORT.md": render_commercial_validation_report(payload),
        "COMMERCIAL_RETENTION_REPORT.md": render_commercial_retention_report(payload),
        "VALUE_TO_REVENUE_ANALYSIS.md": render_value_to_revenue_analysis(payload),
    }


def render_commercial_validation_program(
    payload: dict[str, Any],
    *,
    focus: str = "commercial_validation_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Commercial Validation Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F5')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 351')}",
        "",
        f"Activation: **{metrics.get('activation_rate')}** · "
        f"Retention: **{metrics.get('retention_rate')}** · "
        f"Sustainability: **{metrics.get('commercial_sustainability_score')}**",
        "",
        "## Operator commands",
        "",
        "- `commercial validation cohort: customer_id=..., plan=PRO, segment=startup, customer_session_id=...`",
        "- `commercial validation note: ...`",
        "- `commercial validation review approve: ...`",
        "- `show commercial validation dashboard`",
        "",
    ]
    return "\n".join(lines)

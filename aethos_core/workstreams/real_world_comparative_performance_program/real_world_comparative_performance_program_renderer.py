# SPDX-License-Identifier: Apache-2.0
"""PHASE_J2 / FIX 365 — render real-world comparative performance deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_real_world_comparative_performance_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    learning = _section(payload, "phase_6_comparative_learning_analysis", "comparative_learning_report") or {}
    lines = [
        "# Real-World Comparative Performance Report",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_J2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 365')}",
        "",
        "## Core principle",
        "",
        "Comparative performance evaluates outcomes. **Comparative performance ≠ competitive authority.**",
        "",
        f"- Comparison level: **{metrics.get('comparison_level')}**",
        f"- Delivery performance delta: **{metrics.get('delivery_performance_delta')}**",
        f"- Deployment performance delta: **{metrics.get('deployment_performance_delta')}**",
        f"- Recovery performance delta: **{metrics.get('recovery_performance_delta')}**",
        f"- Customer outcome delta: **{metrics.get('customer_outcome_delta')}**",
        f"- Operational efficiency delta: **{metrics.get('operational_efficiency_delta')}**",
        f"- AethOS performs better: **{learning.get('aethos_performs_better')}**",
        f"- Competitive authority: **{payload.get('competitive_authority')}**",
    ]
    return "\n".join(lines)


def render_delivery_comparison_analysis(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_2_delivery_comparison_analysis", "delivery_comparison_report") or {}
    lines = [
        "# Delivery Comparison Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Time to delivery (AethOS): **{report.get('time_to_delivery_ms_aethos')}** ms",
        f"- Time to delivery (baseline): **{report.get('time_to_delivery_ms_baseline')}** ms",
        f"- Delivery consistency: **{report.get('delivery_consistency_score')}**",
        f"- Delivery quality: **{report.get('delivery_quality_score')}**",
        f"- Delivery performance delta: **{report.get('delivery_performance_delta')}**",
    ]
    return "\n".join(lines)


def render_customer_outcome_comparison_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_customer_outcome_comparison", "customer_outcome_comparison_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Customer Outcome Comparison Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Onboarding outcome score: **{report.get('onboarding_outcome_score')}**",
        f"- Value realization score: **{report.get('value_realization_score')}**",
        f"- Retention score: **{report.get('retention_score')}**",
        f"- Satisfaction score: **{report.get('satisfaction_score')}**",
        f"- Customer outcome delta: **{metrics.get('customer_outcome_delta')}**",
        f"- Strategy mutation performed: **{payload.get('strategy_mutation')}**",
    ]
    return "\n".join(lines)


def render_all_comparative_performance_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "REAL_WORLD_COMPARATIVE_PERFORMANCE_REPORT.md": render_real_world_comparative_performance_report(payload),
        "DELIVERY_COMPARISON_ANALYSIS.md": render_delivery_comparison_analysis(payload),
        "CUSTOMER_OUTCOME_COMPARISON_REPORT.md": render_customer_outcome_comparison_report(payload),
    }


def render_real_world_comparative_performance_program(
    payload: dict[str, Any],
    *,
    focus: str = "comparative_performance_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Real-World Comparative Performance Program",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_J2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 365')}",
        "",
        f"Comparison: **{metrics.get('comparison_level')}** · "
        f"Delivery delta: **{metrics.get('delivery_performance_delta')}** · "
        f"Customer delta: **{metrics.get('customer_outcome_delta')}**",
        "",
        "## Operator commands",
        "",
        "- `comparative performance benchmark: benchmark_id=..., approach=human_only, category=delivery, time_to_delivery_ms=7200000`",
        "- `comparative performance note: ...`",
        "- `comparative performance review approve: ...`",
        "- `show comparative performance dashboard`",
        "",
    ]
    return "\n".join(lines)

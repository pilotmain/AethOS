# SPDX-License-Identifier: Apache-2.0
"""PHASE_J3 / FIX 366 — render compounding value deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_compounding_value_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Compounding Value Report",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_J3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 366')}",
        "",
        "## Core principle",
        "",
        "Continuous improvement measurement tracks compounding value. **Continuous improvement measurement ≠ autonomous self-modification.**",
        "",
        f"- Improvement level: **{metrics.get('improvement_level')}**",
        f"- Compounding value score: **{metrics.get('compounding_value_score')}**",
        f"- Improvement velocity: **{metrics.get('improvement_velocity')}**",
        f"- Delivery improvement: **{metrics.get('delivery_improvement_score')}**",
        f"- Operational improvement: **{metrics.get('operational_improvement_score')}**",
        f"- Customer improvement: **{metrics.get('customer_improvement_score')}**",
        f"- Business improvement: **{metrics.get('business_improvement_score')}**",
        f"- Self-modification: **{payload.get('autonomous_self_modification')}**",
    ]
    return "\n".join(lines)


def render_continuous_improvement_report(payload: dict[str, Any]) -> str:
    delivery = _section(payload, "phase_2_delivery_improvement_analysis", "delivery_improvement_report") or {}
    operational = _section(payload, "phase_3_operational_improvement_analysis", "operational_improvement_report") or {}
    lines = [
        "# Continuous Improvement Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Delivery time trend: **{delivery.get('delivery_time_trend')}**",
        f"- Delivery quality trend: **{delivery.get('delivery_quality_trend')}**",
        f"- Deployment improvement: **{operational.get('deployment_improvement')}**",
        f"- Recovery improvement: **{operational.get('recovery_improvement')}**",
        f"- Incident reduction: **{operational.get('incident_reduction_score')}**",
        f"- Automatic policy changes: **{payload.get('automatic_policy_changes')}**",
    ]
    return "\n".join(lines)


def render_learning_effectiveness_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_6_learning_effectiveness_analysis", "learning_effectiveness_report") or {}
    lines = [
        "# Learning Effectiveness Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Recommendation adoption rate: **{report.get('recommendation_adoption_rate')}**",
        f"- Improvement effectiveness score: **{report.get('improvement_effectiveness_score')}**",
        f"- Recurring issue reduction score: **{report.get('recurring_issue_reduction_score')}**",
        f"- Governance mutation performed: **{payload.get('governance_mutation')}**",
    ]
    return "\n".join(lines)


def render_all_compounding_value_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "COMPOUNDING_VALUE_REPORT.md": render_compounding_value_report(payload),
        "CONTINUOUS_IMPROVEMENT_REPORT.md": render_continuous_improvement_report(payload),
        "LEARNING_EFFECTIVENESS_REPORT.md": render_learning_effectiveness_report(payload),
    }


def render_compounding_value_continuous_improvement_program(
    payload: dict[str, Any],
    *,
    focus: str = "compounding_value_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Compounding Value & Continuous Improvement Program",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_J3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 366')}",
        "",
        f"Improvement: **{metrics.get('improvement_level')}** · "
        f"Compounding score: **{metrics.get('compounding_value_score')}** · "
        f"Velocity: **{metrics.get('improvement_velocity')}**",
        "",
        "## Operator commands",
        "",
        "- `continuous improvement baseline: baseline_id=..., category=delivery, initial_score=0.35, current_score=0.6`",
        "- `continuous improvement note: ...`",
        "- `continuous improvement review approve: ...`",
        "- `show compounding value dashboard`",
        "",
    ]
    return "\n".join(lines)

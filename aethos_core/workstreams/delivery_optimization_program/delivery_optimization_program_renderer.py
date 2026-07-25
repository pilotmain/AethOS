# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C2 / FIX 340 — render delivery optimization deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_delivery_optimization_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    trends = payload.get("trends") or {}
    matrix = _section(payload, "phase_7_optimization_priority_matrix", "delivery_optimization_priority_matrix") or {}
    lines = [
        "# Delivery Optimization Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_C2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 340')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "AethOS recommends improvements; humans decide adoption. **Delivery optimization ≠ autonomous mutation.**",
        "",
        "## Success criteria",
        "",
        f"- Recurring failures identified: **{success.get('recurring_failures_identified')}**",
        f"- Recurring interventions identified: **{success.get('recurring_interventions_identified')}**",
        f"- Delivery bottlenecks identified: **{success.get('delivery_bottlenecks_identified')}**",
        f"- Improvement recommendations present: **{success.get('improvement_recommendations_present')}**",
        f"- Program complete: **{success.get('program_complete')}**",
        "",
        "## Optimization trends",
        "",
        f"- Deployment success trend: **{trends.get('deployment_success_trend')}**",
        f"- Intervention reduction trend: **{trends.get('intervention_reduction_trend')}**",
        f"- Delivery cycle time trend: **{trends.get('delivery_cycle_time_trend')}ms**",
        "",
        "## Top priority opportunities",
        "",
    ]
    for opp in (matrix.get("ranked_opportunities") or [])[:5]:
        lines.append(f"- **{opp.get('title')}** (score `{opp.get('priority_score')}`)")
    lines.extend(["", "## Non-goals", ""])
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_delivery_reliability_intelligence_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_reliability_intelligence", "delivery_reliability_intelligence_report") or {}
    failures = _section(payload, "phase_2_failure_intelligence", "delivery_failure_intelligence_report") or {}
    lines = [
        "# Delivery Reliability Intelligence Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Reliability",
        "",
        f"- Success rate: **{report.get('success_rate')}**",
        f"- Failure rate: **{report.get('failure_rate')}**",
        f"- Recovery rate: **{report.get('recovery_rate')}**",
        f"- Verification rate: **{report.get('verification_rate')}**",
        "",
        "## Failure intelligence",
        "",
        f"- ET1 failures: **{failures.get('execution_track_1_failures', 0)}**",
        f"- ET2 failures: **{failures.get('execution_track_2_failures', 0)}**",
        f"- ET3 failures: **{failures.get('execution_track_3_failures', 0)}**",
        f"- ET4 failures: **{failures.get('execution_track_4_failures', 0)}**",
        f"- ET5 failures: **{failures.get('execution_track_5_failures', 0)}**",
        "",
    ]
    return "\n".join(lines)


def render_delivery_improvement_opportunities(payload: dict[str, Any]) -> str:
    registry = _section(payload, "phase_6_improvement_opportunity_registry", "delivery_improvement_opportunity_registry") or {}
    matrix = _section(payload, "phase_7_optimization_priority_matrix", "delivery_optimization_priority_matrix") or {}
    lines = [
        "# Delivery Improvement Opportunities",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "Recommendations only — human adoption required. No autonomous engine modification.",
        "",
        "## Opportunity registry",
        "",
        "```json",
        _json_block(registry),
        "```",
        "",
        "## Priority matrix",
        "",
        "```json",
        _json_block(matrix),
        "```",
    ]
    return "\n".join(lines)


def render_all_delivery_optimization_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "DELIVERY_OPTIMIZATION_REPORT.md": render_delivery_optimization_report(payload),
        "DELIVERY_RELIABILITY_INTELLIGENCE_REPORT.md": render_delivery_reliability_intelligence_report(payload),
        "DELIVERY_IMPROVEMENT_OPPORTUNITIES.md": render_delivery_improvement_opportunities(payload),
    }


def render_delivery_optimization_program(
    payload: dict[str, Any],
    *,
    focus: str = "delivery_optimization_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("phase_8_executive_visibility") or [{}])[0].get(
        "delivery_optimization_dashboard", {}
    )
    trends = payload.get("trends") or {}
    lines = [
        "# Delivery Optimization Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_C2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 340')}",
        "",
        "Evidence-backed improvement loop — recommendations require human review before adoption.",
        "",
        f"Opportunities: **{dashboard.get('opportunity_count', 0)}**",
        f"Deployment success trend: **{trends.get('deployment_success_trend', 0.0)}**",
        f"Intervention reduction trend: **{trends.get('intervention_reduction_trend', 0.0)}**",
        "",
        "## Operator commands",
        "",
        "- `delivery optimization note: ...`",
        "- `analyze delivery optimization`",
        "- `delivery optimization review approve: ...`",
        "- `show delivery optimization dashboard`",
        "",
    ]
    return "\n".join(lines)

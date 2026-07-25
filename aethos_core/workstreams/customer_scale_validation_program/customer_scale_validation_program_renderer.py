# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F4 / FIX 350 — render customer scale validation deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_customer_scale_validation_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    metrics = payload.get("metrics") or {}
    cohort = _section(payload, "phase_1_scale_cohort_registry", "customer_scale_cohort_registry") or {}
    lines = [
        "# Customer Scale Validation Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F4')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 350')}",
        "",
        "## Core principle",
        "",
        "Scale validation measures operational capability. "
        "**Customer scale validation ≠ customer authority.**",
        "",
        f"- Concurrent customers: **{metrics.get('concurrent_customers', 0)}**",
        f"- Delivery throughput: **{metrics.get('delivery_throughput', 0)}**",
        f"- Deployment throughput: **{metrics.get('deployment_throughput', 0)}**",
        f"- Outcomes preserved: **{success.get('customer_outcomes_preserved')}**",
        f"- Governance bypass: **{payload.get('governance_bypass_authority')}**",
        f"- Cohort size: **{cohort.get('cohort_size', 0)}**",
    ]
    return "\n".join(lines)


def render_execution_capacity_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_execution_capacity_analysis", "execution_capacity_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Execution Capacity Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Workspace throughput: **{report.get('workspace_creation_throughput', 0)}**",
        f"- Code generation throughput: **{report.get('code_generation_throughput', 0)}**",
        f"- Git delivery throughput: **{report.get('git_delivery_throughput', 0)}**",
        f"- Deployment throughput: **{metrics.get('deployment_throughput', 0)}**",
        f"- Execution quality stable: **{report.get('execution_quality_stable')}**",
    ]
    return "\n".join(lines)


def render_customer_outcome_stability_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_6_customer_outcome_stability", "customer_outcome_stability_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Customer Outcome Stability Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Adoption under scale: **{metrics.get('adoption_rate')}**",
        f"- Retention under scale: **{metrics.get('retention_rate')}**",
        f"- Value score under scale: **{metrics.get('value_realization_score')}**",
        f"- Satisfaction trend: **{metrics.get('customer_satisfaction_trend')}**",
        f"- Outcomes stable: **{report.get('outcomes_stable_under_scale')}**",
    ]
    return "\n".join(lines)


def render_all_customer_scale_validation_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "CUSTOMER_SCALE_VALIDATION_REPORT.md": render_customer_scale_validation_report(payload),
        "EXECUTION_CAPACITY_REPORT.md": render_execution_capacity_report(payload),
        "CUSTOMER_OUTCOME_STABILITY_REPORT.md": render_customer_outcome_stability_report(payload),
    }


def render_customer_scale_validation_program(
    payload: dict[str, Any],
    *,
    focus: str = "customer_scale_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Customer Scale Validation Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F4')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 350')}",
        "",
        f"Concurrent customers: **{metrics.get('concurrent_customers')}** · "
        f"Delivery throughput: **{metrics.get('delivery_throughput')}** · "
        f"Bottlenecks: **{metrics.get('bottleneck_frequency')}**",
        "",
        "## Operator commands",
        "",
        "- `customer scale cohort: customer_id=..., customer_session_id=..., provider=Railway`",
        "- `customer scale note: ...`",
        "- `customer scale review approve: ...`",
        "- `show customer scale dashboard`",
        "",
    ]
    return "\n".join(lines)

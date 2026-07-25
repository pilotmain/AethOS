# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F7 / FIX 353 — render business operating model deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_business_operating_model_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    metrics = payload.get("metrics") or {}
    registry = _section(payload, "phase_1_operating_model_registry", "operating_model_registry") or {}
    lines = [
        "# Business Operating Model Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F7')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 353')}",
        "",
        "## Core principle",
        "",
        "Operating model validation measures sustainability. "
        "**Operating model validation ≠ operating authority.**",
        "",
        f"- Cohort size: **{registry.get('cohort_size', 0)}**",
        f"- Delivery efficiency: **{metrics.get('delivery_efficiency')}**",
        f"- Governance efficiency: **{metrics.get('governance_efficiency')}**",
        f"- Support efficiency: **{metrics.get('support_efficiency')}**",
        f"- Provider efficiency: **{metrics.get('provider_efficiency')}**",
        f"- Operating leverage: **{metrics.get('operating_leverage_score')}**",
        f"- Operating authority granted: **{payload.get('operating_authority')}**",
        f"- Sustainable customer growth: **{success.get('sustainable_customer_growth')}**",
    ]
    return "\n".join(lines)


def render_delivery_sustainability_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_2_delivery_sustainability_analysis", "delivery_sustainability_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Delivery Sustainability Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Throughput: **{report.get('throughput')}**",
        f"- Reliability: **{report.get('reliability')}**",
        f"- Intervention rate: **{report.get('intervention_rate')}**",
        f"- Execution burden (ms): **{report.get('execution_burden_ms')}**",
        f"- Delivery efficiency: **{metrics.get('delivery_efficiency')}**",
        f"- Delivery capacity sustainable: **{report.get('delivery_capacity_sustainable')}**",
    ]
    return "\n".join(lines)


def render_operating_model_sustainability_report(payload: dict[str, Any]) -> str:
    economic = _section(payload, "phase_6_economic_sustainability_analysis", "business_sustainability_analysis") or {}
    metrics = payload.get("metrics") or {}
    success = payload.get("success_criteria") or {}
    lines = [
        "# Operating Model Sustainability Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Business sustainability score: **{metrics.get('business_sustainability_score')}**",
        f"- Operating leverage score: **{metrics.get('operating_leverage_score')}**",
        f"- Efficiency: **{economic.get('efficiency')}**",
        f"- Cost burden (units): **{economic.get('cost_burden_units')}**",
        f"- Delivery capacity sustainable: **{success.get('sustainable_delivery_capacity')}**",
        f"- Support capacity sustainable: **{success.get('sustainable_support_capacity')}**",
        f"- Governance capacity sustainable: **{success.get('sustainable_governance_capacity')}**",
        f"- Provider capacity sustainable: **{success.get('sustainable_provider_capacity')}**",
    ]
    return "\n".join(lines)


def render_all_business_operating_model_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "BUSINESS_OPERATING_MODEL_REPORT.md": render_business_operating_model_report(payload),
        "DELIVERY_SUSTAINABILITY_REPORT.md": render_delivery_sustainability_report(payload),
        "OPERATING_MODEL_SUSTAINABILITY_REPORT.md": render_operating_model_sustainability_report(payload),
    }


def render_business_operating_model_validation_program(
    payload: dict[str, Any],
    *,
    focus: str = "operating_model_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Business Operating Model Validation Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F7')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 353')}",
        "",
        f"Leverage: **{metrics.get('operating_leverage_score')}** · "
        f"Sustainability: **{metrics.get('business_sustainability_score')}** · "
        f"Delivery: **{metrics.get('delivery_efficiency')}**",
        "",
        "## Operator commands",
        "",
        "- `operating model cohort: customer_id=..., plan=PRO, provider=Railway, customer_session_id=...`",
        "- `operating model note: ...`",
        "- `operating model review approve: ...`",
        "- `show operating model dashboard`",
        "",
    ]
    return "\n".join(lines)

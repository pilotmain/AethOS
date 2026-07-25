# SPDX-License-Identifier: Apache-2.0
"""PHASE_J1 / FIX 364 — render production reality deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_production_reality_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    registry = _section(payload, "phase_1_production_operations_registry", "production_operations_registry") or {}
    lines = [
        "# Production Reality Report",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_J1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 364')}",
        "",
        "## Core principle",
        "",
        "Production reality measurement tracks operational durability. **Production reality measurement ≠ operational authority.**",
        "",
        f"- Durability level: **{metrics.get('durability_level')}**",
        f"- Operational durability score: **{metrics.get('operational_durability_score')}**",
        f"- Deployment durability: **{metrics.get('deployment_durability_score')}**",
        f"- Recovery durability: **{metrics.get('recovery_durability_score')}**",
        f"- Provider durability: **{metrics.get('provider_durability_score')}**",
        f"- Customer durability: **{metrics.get('customer_durability_score')}**",
        f"- Production operations tracked: **{registry.get('operation_count')}**",
        f"- Operational authority: **{payload.get('operational_authority')}**",
    ]
    return "\n".join(lines)


def render_longitudinal_operations_report(payload: dict[str, Any]) -> str:
    incidents = _section(payload, "phase_3_incident_reality_analysis", "production_incident_report") or {}
    customer = _section(payload, "phase_6_customer_reality_analysis", "customer_reality_report") or {}
    lines = [
        "# Longitudinal Operations Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Incident frequency: **{incidents.get('incident_frequency')}**",
        f"- Incident recurrence: **{incidents.get('incident_recurrence')}**",
        f"- Retained customers: **{customer.get('retained_customers')}**",
        f"- Active customers: **{customer.get('active_customers')}**",
        f"- Customer outcome durability: **{customer.get('customer_outcome_durability')}**",
        f"- Autonomous production control: **{payload.get('autonomous_production_control')}**",
    ]
    return "\n".join(lines)


def render_production_durability_analysis(payload: dict[str, Any]) -> str:
    deployment = _section(payload, "phase_2_deployment_durability_analysis", "deployment_durability_report") or {}
    recovery = _section(payload, "phase_4_recovery_durability_analysis", "recovery_durability_report") or {}
    provider = _section(payload, "phase_5_provider_reality_analysis", "provider_reality_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Production Durability Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Deployment durability score: **{metrics.get('deployment_durability_score')}**",
        f"- Deployment success trend: **{deployment.get('deployment_success_trend')}**",
        f"- Recovery durability score: **{metrics.get('recovery_durability_score')}**",
        f"- Recovery success rate: **{recovery.get('recovery_success_rate')}**",
        f"- Provider durability score: **{metrics.get('provider_durability_score')}**",
        f"- Providers evaluated: **{len(provider.get('providers_evaluated') or [])}**",
    ]
    return "\n".join(lines)


def render_all_production_reality_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "PRODUCTION_REALITY_REPORT.md": render_production_reality_report(payload),
        "LONGITUDINAL_OPERATIONS_REPORT.md": render_longitudinal_operations_report(payload),
        "PRODUCTION_DURABILITY_ANALYSIS.md": render_production_durability_analysis(payload),
    }


def render_production_reality_longitudinal_operations_program(
    payload: dict[str, Any],
    *,
    focus: str = "production_reality_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Production Reality & Longitudinal Operations Program",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_J1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 364')}",
        "",
        f"Durability: **{metrics.get('durability_level')}** · "
        f"Score: **{metrics.get('operational_durability_score')}** · "
        f"Deployment: **{metrics.get('deployment_durability_score')}**",
        "",
        "## Operator commands",
        "",
        "- `production reality observation: operation_id=..., category=deployment, outcome=passed, provider=Railway`",
        "- `production reality note: ...`",
        "- `production reality review approve: ...`",
        "- `show production reality dashboard`",
        "",
    ]
    return "\n".join(lines)

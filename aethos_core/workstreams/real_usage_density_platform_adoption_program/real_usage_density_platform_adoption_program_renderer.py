# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G2 / FIX 355 — render platform adoption deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_real_usage_density_report(payload: dict[str, Any]) -> str:
    active = _section(payload, "phase_2_active_usage_analysis", "active_usage_report") or {}
    workflow = _section(payload, "phase_3_workflow_adoption_analysis", "workflow_adoption_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Real Usage Density Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_G2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 355')}",
        "",
        "## Core principle",
        "",
        "Usage density observes behavior. **Usage density ≠ user authority.**",
        "",
        f"- Active users: **{metrics.get('active_users')}**",
        f"- Retained users: **{metrics.get('retained_users')}**",
        f"- Recurring workflows: **{metrics.get('recurring_workflows')}**",
        f"- Workflow adoption rate: **{metrics.get('workflow_adoption_rate')}**",
        f"- Daily active users: **{active.get('daily_active_users')}**",
        f"- ET usage: **{workflow.get('et_usage')}**",
        f"- Mission Control usage: **{workflow.get('mission_control_usage')}**",
    ]
    return "\n".join(lines)


def render_platform_adoption_report(payload: dict[str, Any]) -> str:
    retained = _section(payload, "phase_4_retained_usage_analysis", "retained_usage_report") or {}
    friction = _section(payload, "phase_6_adoption_friction_analysis", "adoption_friction_report") or {}
    metrics = payload.get("metrics") or {}
    success = payload.get("success_criteria") or {}
    lines = [
        "# Platform Adoption Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Active usage demonstrated: **{success.get('active_usage_demonstrated')}**",
        f"- Retained usage demonstrated: **{success.get('retained_usage_demonstrated')}**",
        f"- Recurring workflows: **{metrics.get('recurring_workflows')}**",
        f"- Adoption friction score: **{metrics.get('adoption_friction_score')}**",
        f"- Repeat sessions: **{retained.get('repeat_sessions')}**",
        f"- Abandoned workflows: **{len(friction.get('abandoned_workflows') or [])}**",
        f"- Automated outreach: **{payload.get('automated_outreach')}**",
    ]
    return "\n".join(lines)


def render_platform_dependence_analysis(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_platform_dependence_analysis", "platform_dependence_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Platform Dependence Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Platform dependence score: **{metrics.get('platform_dependence_score')}**",
        f"- Workflow reliance sessions: **{report.get('workflow_reliance_sessions')}**",
        f"- Repeat execution patterns: **{report.get('repeat_execution_patterns')}**",
        f"- Operational dependence sessions: **{report.get('operational_dependence_sessions')}**",
        f"- Usage maturity distribution: **{report.get('usage_maturity_distribution')}**",
        f"- Workflow dependence demonstrated: **{report.get('workflow_dependence_demonstrated')}**",
    ]
    return "\n".join(lines)


def render_all_platform_adoption_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "REAL_USAGE_DENSITY_REPORT.md": render_real_usage_density_report(payload),
        "PLATFORM_ADOPTION_REPORT.md": render_platform_adoption_report(payload),
        "PLATFORM_DEPENDENCE_ANALYSIS.md": render_platform_dependence_analysis(payload),
    }


def render_real_usage_density_platform_adoption_program(
    payload: dict[str, Any],
    *,
    focus: str = "platform_adoption_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Real Usage Density & Platform Adoption Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_G2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 355')}",
        "",
        f"Active users: **{metrics.get('active_users')}** · "
        f"Adoption: **{metrics.get('workflow_adoption_rate')}** · "
        f"Dependence: **{metrics.get('platform_dependence_score')}**",
        "",
        "## Operator commands",
        "",
        "- `platform adoption session: customer_session_id=..., surface=mission_control`",
        "- `platform adoption note: ...`",
        "- `platform adoption review approve: ...`",
        "- `show platform adoption dashboard`",
        "",
    ]
    return "\n".join(lines)

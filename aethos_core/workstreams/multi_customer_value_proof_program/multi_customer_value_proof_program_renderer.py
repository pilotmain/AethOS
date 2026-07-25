# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F3 / FIX 349 — render multi-customer value proof deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_multi_customer_value_proof_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    metrics = payload.get("metrics") or {}
    cohort = _section(payload, "phase_1_customer_cohort_registry", "customer_cohort_registry") or {}
    lines = [
        "# Multi-Customer Value Proof Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 349')}",
        "",
        "## Core principle",
        "",
        "Multi-customer validation measures repeatable outcomes. "
        "**Multi-customer validation ≠ customer authority.**",
        "",
        f"- Cohort size: **{cohort.get('cohort_size', 0)}**",
        f"- Repeatable adoption: **{success.get('repeatable_adoption')}**",
        f"- Repeatable value: **{success.get('repeatable_value_realization')}**",
        f"- Repeatability score: **{metrics.get('repeatability_score')}**",
        f"- Customer authority granted: **{success.get('customer_authority_granted')}**",
    ]
    return "\n".join(lines)


def render_customer_success_patterns_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_6_success_pattern_discovery", "customer_success_pattern_report") or {}
    lines = [
        "# Customer Success Patterns Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Success pattern frequency: **{report.get('success_pattern_frequency', 0)}**",
        f"- Common success paths: **{len(report.get('common_success_paths') or [])}**",
        f"- Common failure paths: **{len(report.get('common_failure_paths') or [])}**",
        f"- Onboarding patterns: **{', '.join(report.get('onboarding_patterns') or []) or '—'}**",
        f"- Provider patterns: **{', '.join(report.get('provider_patterns') or []) or '—'}**",
    ]
    return "\n".join(lines)


def render_customer_retention_analysis_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_retention_analysis", "cohort_retention_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Customer Retention Analysis Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Cohort retention rate: **{metrics.get('retention_rate')}**",
        f"- Continued usage count: **{report.get('continued_usage_count', 0)}**",
        f"- Declining usage count: **{report.get('declining_usage_count', 0)}**",
        f"- Dormant usage count: **{report.get('dormant_usage_count', 0)}**",
        f"- Repeatable retention signals: **{report.get('repeatable_retention_signals')}**",
    ]
    return "\n".join(lines)


def render_all_multi_customer_value_proof_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "MULTI_CUSTOMER_VALUE_PROOF_REPORT.md": render_multi_customer_value_proof_report(payload),
        "CUSTOMER_SUCCESS_PATTERNS_REPORT.md": render_customer_success_patterns_report(payload),
        "CUSTOMER_RETENTION_ANALYSIS_REPORT.md": render_customer_retention_analysis_report(payload),
    }


def render_multi_customer_value_proof_program(
    payload: dict[str, Any],
    *,
    focus: str = "multi_customer_value_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Multi-Customer Value Proof Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 349')}",
        "",
        f"Repeatability score: **{metrics.get('repeatability_score')}** · "
        f"Adoption: **{metrics.get('adoption_rate')}** · "
        f"Retention: **{metrics.get('retention_rate')}**",
        "",
        "## Operator commands",
        "",
        "- `multi customer cohort: customer_id=..., use_case=..., delivery_type=..., environment=...`",
        "- `multi customer note: ...`",
        "- `multi customer review approve: ...`",
        "- `show multi customer value dashboard`",
        "",
    ]
    return "\n".join(lines)

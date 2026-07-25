# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G4 / FIX 357 — render platform maturity deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_enterprise_platform_maturity_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    inventory = _section(payload, "phase_1_platform_inventory", "platform_inventory_registry") or {}
    lines = [
        "# Enterprise Platform Maturity Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_G4')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 357')}",
        "",
        "## Core principle",
        "",
        "Platform maturity audit evaluates readiness. **Platform maturity audit ≠ launch authority.**",
        "",
        f"- Overall platform maturity score: **{metrics.get('overall_platform_maturity_score')}**",
        f"- Platform maturity level: **{metrics.get('platform_maturity_level')}**",
        f"- Architecture maturity: **{metrics.get('architecture_maturity_score')}**",
        f"- Execution maturity: **{metrics.get('execution_maturity_score')}**",
        f"- Operational maturity: **{metrics.get('operational_maturity_score')}**",
        f"- FIX 300–330 modules present: **{inventory.get('fix_300_330_present_count')}** / **{inventory.get('fix_300_330_total')}**",
        f"- Launch authority: **{payload.get('launch_authority')}**",
    ]
    return "\n".join(lines)


def render_platform_readiness_audit(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    success = payload.get("success_criteria") or {}
    customer = _section(payload, "phase_5_customer_commercial_maturity_audit", "customer_commercial_maturity_report") or {}
    evidence = _section(payload, "phase_6_evidence_trust_maturity_audit", "evidence_trust_maturity_report") or {}
    lines = [
        "# Platform Readiness Audit",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Customer maturity score: **{metrics.get('customer_maturity_score')}**",
        f"- Commercial maturity score: **{metrics.get('commercial_maturity_score')}**",
        f"- Evidence maturity score: **{metrics.get('evidence_maturity_score')}**",
        f"- Adoption maturity: **{customer.get('adoption_maturity')}**",
        f"- Business viability maturity: **{customer.get('business_viability_maturity')}**",
        f"- Evidence density: **{evidence.get('evidence_density')}**",
        f"- Enterprise readiness signals: **{success.get('enterprise_readiness_signals')}**",
        f"- Trust promotion performed: **{payload.get('trust_promotion')}**",
    ]
    return "\n".join(lines)


def render_platform_gap_analysis(payload: dict[str, Any]) -> str:
    gaps = _section(payload, "phase_7_platform_gap_registry", "platform_gap_registry") or {}
    lines = [
        "# Platform Gap Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Total gaps: **{gaps.get('gap_count')}**",
        f"- Maturity gaps: **{len(gaps.get('maturity_gaps') or [])}**",
        f"- Operational gaps: **{len(gaps.get('operational_gaps') or [])}**",
        f"- Adoption gaps: **{len(gaps.get('adoption_gaps') or [])}**",
        f"- Evidence gaps: **{len(gaps.get('evidence_gaps') or [])}**",
    ]
    return "\n".join(lines)


def render_all_platform_maturity_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "ENTERPRISE_PLATFORM_MATURITY_REPORT.md": render_enterprise_platform_maturity_report(payload),
        "PLATFORM_READINESS_AUDIT.md": render_platform_readiness_audit(payload),
        "PLATFORM_GAP_ANALYSIS.md": render_platform_gap_analysis(payload),
    }


def render_enterprise_platform_maturity_readiness_audit_program(
    payload: dict[str, Any],
    *,
    focus: str = "enterprise_platform_maturity_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Enterprise Platform Maturity & Readiness Audit",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_G4')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 357')}",
        "",
        f"Overall maturity: **{metrics.get('overall_platform_maturity_score')}** · "
        f"Level: **{metrics.get('platform_maturity_level')}** · "
        f"Architecture: **{metrics.get('architecture_maturity_score')}**",
        "",
        "## Operator commands",
        "",
        "- `platform maturity note: ...`",
        "- `platform maturity review approve: ...`",
        "- `show enterprise platform maturity dashboard`",
        "",
    ]
    return "\n".join(lines)

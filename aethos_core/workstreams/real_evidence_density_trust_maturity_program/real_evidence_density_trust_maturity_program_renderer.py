# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G1 / FIX 354 — render evidence maturity deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_real_evidence_density_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_2_evidence_density_analysis", "evidence_density_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Real Evidence Density Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_G1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 354')}",
        "",
        "## Core principle",
        "",
        "Evidence density measures confidence. **Evidence density ≠ trust authority.**",
        "",
        f"- Real evidence count: **{report.get('real_evidence_count', 0)}**",
        f"- Derived evidence count: **{report.get('derived_evidence_count', 0)}**",
        f"- Synthetic evidence count: **{report.get('synthetic_evidence_count', 0)}**",
        f"- Operational evidence count: **{report.get('operational_evidence_count', 0)}**",
        f"- Independent evidence count: **{report.get('independent_evidence_count', 0)}**",
        f"- Evidence density score: **{metrics.get('evidence_density_score')}**",
        f"- Trust promotion: **{payload.get('trust_promotion')}**",
    ]
    return "\n".join(lines)


def render_trust_maturity_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_trust_maturity_analysis", "trust_maturity_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Trust Maturity Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Trust maturity score: **{metrics.get('trust_maturity_score')}**",
        f"- Trust freeze coverage: **{report.get('trust_freeze_coverage')}**",
        f"- Trust decision coverage: **{report.get('trust_decision_coverage')}**",
        f"- Operational proof coverage: **{metrics.get('operational_proof_coverage')}**",
        f"- Independent validation coverage: **{report.get('independent_validation_coverage')}**",
        f"- Trust authority granted: **{report.get('trust_authority_granted')}**",
    ]
    return "\n".join(lines)


def render_evidence_gap_analysis(payload: dict[str, Any]) -> str:
    gaps = _section(payload, "phase_6_evidence_gap_registry", "evidence_gap_registry") or {}
    freshness = _section(payload, "phase_3_evidence_freshness_analysis", "evidence_freshness_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Evidence Gap Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Gap count: **{gaps.get('gap_count', 0)}**",
        f"- Missing evidence gaps: **{len(gaps.get('missing_evidence') or [])}**",
        f"- Sparse evidence gaps: **{len(gaps.get('sparse_evidence') or [])}**",
        f"- Weak evidence gaps: **{len(gaps.get('weak_evidence') or [])}**",
        f"- Unsupported assumptions: **{len(gaps.get('unsupported_assumptions') or [])}**",
        f"- Evidence freshness score: **{metrics.get('evidence_freshness_score')}**",
        f"- Stale evidence count: **{freshness.get('stale_evidence_count', 0)}**",
    ]
    return "\n".join(lines)


def render_all_evidence_maturity_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "REAL_EVIDENCE_DENSITY_REPORT.md": render_real_evidence_density_report(payload),
        "TRUST_MATURITY_REPORT.md": render_trust_maturity_report(payload),
        "EVIDENCE_GAP_ANALYSIS.md": render_evidence_gap_analysis(payload),
    }


def render_real_evidence_density_trust_maturity_program(
    payload: dict[str, Any],
    *,
    focus: str = "evidence_maturity_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Real Evidence Density & Trust Maturity Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_G1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 354')}",
        "",
        f"Density: **{metrics.get('evidence_density_score')}** · "
        f"Freshness: **{metrics.get('evidence_freshness_score')}** · "
        f"Trust maturity: **{metrics.get('trust_maturity_score')}**",
        "",
        "## Operator commands",
        "",
        "- `evidence maturity domain: domain=customer, source=f1`",
        "- `evidence maturity note: ...`",
        "- `evidence maturity review approve: ...`",
        "- `show evidence maturity dashboard`",
        "",
    ]
    return "\n".join(lines)

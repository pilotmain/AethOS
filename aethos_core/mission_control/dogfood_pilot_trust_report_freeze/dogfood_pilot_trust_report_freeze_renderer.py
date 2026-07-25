# SPDX-License-Identifier: Apache-2.0
"""FIX 186 — Markdown renderer for dogfood pilot trust report freeze."""

from __future__ import annotations

from typing import Any


def render_dogfood_pilot_trust_report_freeze(dogfood_pilot_trust_report_freeze: dict[str, Any]) -> str:
    sections = dogfood_pilot_trust_report_freeze.get("sections") or {}

    lines = [
        "# Dogfood Pilot Trust Report Freeze (FIX 186 — trust_report_freeze ≠ pilot_execution)",
        "",
        f"- session_id: `{dogfood_pilot_trust_report_freeze.get('session_id', '')}`",
        f"- repo/issue: `{dogfood_pilot_trust_report_freeze.get('repo_issue') or 'none'}`",
        f"- trust status: **{dogfood_pilot_trust_report_freeze.get('trust_status', 'none')}**",
        f"- pilot 3 complete: **{dogfood_pilot_trust_report_freeze.get('pilot_3_complete', False)}**",
        f"- freeze recorded: **{dogfood_pilot_trust_report_freeze.get('trust_report_freeze_recorded', False)}**",
        f"- expansion approved: **{dogfood_pilot_trust_report_freeze.get('expansion_approved', False)}**",
        f"- multi-repo expansion blocked: **{dogfood_pilot_trust_report_freeze.get('multi_repo_expansion_blocked', True)}**",
        f"- pilot re-execution performed: **{dogfood_pilot_trust_report_freeze.get('pilot_reexecution_performed', False)}** _(always false)_",
        "",
        dogfood_pilot_trust_report_freeze.get("invariant", ""),
        "",
        "_Trust report composes Pilots 1–3 artifacts only — never re-runs pilots._",
        "",
        "## Frozen evidence timeline",
        "",
    ]

    for item in sections.get("frozen_evidence_timeline") or []:
        lines.append(f"### {item.get('pilot_id')} — Phase {item.get('phase')}")
        lines.append(f"- Question: {item.get('question')}")
        lines.append(f"- Answer: **{item.get('answer')}**")
        lines.append(f"- Finding: {item.get('finding')}")
        if item.get("fix_applied"):
            lines.append(f"- Fix applied: {item.get('fix_applied')}")
        if item.get("audit_id"):
            lines.append(f"- Audit: `{item.get('audit_id')}` outcome `{item.get('pilot_outcome')}`")
        if item.get("pr_metadata"):
            lines.append(f"- PR: {item.get('pr_metadata')}")
        lines.append("")

    lines.extend(["## Trust boundary", ""])
    for matrix in sections.get("trust_boundary_matrix") or []:
        lines.append(f"### {matrix.get('status')}")
        lines.append(f"Scope: {matrix.get('scope')}")
        for cap in matrix.get("capabilities") or []:
            lines.append(f"- {cap}")
        lines.append("")

    rec = (sections.get("dogfood_trust_recommendation") or [{}])[0]
    lines.extend(
        [
            "## Trust recommendation",
            "",
            f"- Status: **{rec.get('trust_status')}**",
            f"- Scope: {rec.get('scope')}",
            f"- Rationale: {rec.get('trust_rationale')}",
            "",
        ]
    )

    expansion = (sections.get("expansion_recommendation") or [{}])[0]
    lines.extend(
        [
            "## Expansion recommendation",
            "",
            f"- Proceed: **{expansion.get('proceed')}**",
            f"- Reason: {expansion.get('reason')}",
            f"- Proposed order: {', '.join(expansion.get('proposed_order') or [])}",
            "",
        ]
    )

    lines.extend(["## Evidence index", ""])
    for entry in sections.get("evidence_index") or []:
        lines.append(f"- `{entry.get('ref_id')}` ({entry.get('kind')}): {entry}")
    lines.append("")

    metrics = (sections.get("fix_183_metrics_composition") or [{}])[0]
    lines.extend(
        [
            "## FIX 183 metrics (composed)",
            "",
            f"- approval count: **{metrics.get('approval_count')}**",
            f"- re-engagement count: **{metrics.get('re_engagement_count')}**",
            f"- human effort score: **{metrics.get('human_effort_score')}**",
            "",
        ]
    )

    lines.append("_Trust report freeze ≠ pilot execution — evidence baseline for AethOS dogfood Phase 1._")
    return "\n".join(lines)

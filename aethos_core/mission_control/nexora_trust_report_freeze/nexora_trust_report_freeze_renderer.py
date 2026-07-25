# SPDX-License-Identifier: Apache-2.0
"""FIX 196 — Markdown renderer for Nexora trust report freeze."""

from __future__ import annotations

from typing import Any


def render_nexora_trust_report_freeze(nexora_trust_report_freeze: dict[str, Any]) -> str:
    sections = nexora_trust_report_freeze.get("sections") or {}
    report = (sections.get("nexora_trust_report") or [{}])[0]

    lines = [
        "# Nexora Trust Report Freeze (FIX 196 — trust_freeze ≠ trust_granting)",
        "",
        f"- repository: `{nexora_trust_report_freeze.get('repository', '')}`",
        f"- repo/issue: `{nexora_trust_report_freeze.get('repo_issue') or 'none'}`",
        f"- arc state: **{nexora_trust_report_freeze.get('arc_state', 'UNPROVEN')}**",
        f"- trust status: **{nexora_trust_report_freeze.get('trust_status', 'none')}**",
        f"- pilot 3 complete: **{nexora_trust_report_freeze.get('pilot_3_complete', False)}**",
        f"- freeze recorded: **{nexora_trust_report_freeze.get('trust_report_freeze_recorded', False)}**",
        f"- human trust approved: **{nexora_trust_report_freeze.get('human_trust_decision_approve', False)}**",
        f"- multi-repo baseline complete: **{nexora_trust_report_freeze.get('multi_repo_trust_baseline_complete', False)}**",
        "",
        report.get("executive_summary", ""),
        "",
        nexora_trust_report_freeze.get("invariant", ""),
        "",
        "## Nexora evidence timeline",
        "",
    ]

    for item in sections.get("nexora_evidence_timeline") or []:
        lines.append(f"### {item.get('pilot_id')} — Phase {item.get('phase')}")
        lines.append(f"- Question: {item.get('question')}")
        lines.append(f"- Answer: **{item.get('answer')}**")
        lines.append(f"- Finding: {item.get('finding')}")
        if item.get("audit_id"):
            lines.append(f"- Audit: `{item.get('audit_id')}` outcome `{item.get('pilot_outcome')}`")
        lines.append("")

    lines.extend(["## Trust boundary", ""])
    for matrix in sections.get("trust_boundary_matrix") or []:
        lines.append(f"### {matrix.get('status')}")
        lines.append(f"Scope: {matrix.get('scope')}")
        for cap in matrix.get("capabilities") or []:
            lines.append(f"- {cap}")
        lines.append("")

    rec = (sections.get("nexora_trust_recommendation") or [{}])[0]
    lines.extend(
        [
            "## Trust recommendation",
            "",
            f"- Status: **{rec.get('trust_status')}**",
            f"- Rationale: {rec.get('trust_rationale')}",
            "",
        ]
    )

    expansion = (sections.get("expansion_recommendation") or [{}])[0]
    lines.extend(
        [
            "## Expansion recommendation",
            "",
            f"- Recommendation: **{expansion.get('recommendation')}**",
            f"- Reason: {expansion.get('reason')}",
            "",
        ]
    )

    lines.extend(["## Evidence index", ""])
    for entry in sections.get("evidence_index") or []:
        lines.append(f"- `{entry.get('ref_id')}` ({entry.get('kind')})")
    lines.append("")

    lines.extend(
        [
            "## Human trust decision",
            "",
            "Record with:",
            "- `nexora trust decision approve: …`",
            "- `nexora trust decision hold: …`",
            "- `nexora trust decision reject: …`",
            "- `nexora trust decision defer: …`",
            "",
            "_Trust freeze composes Nexora pilot arc evidence only — never re-runs pilots or grants trust automatically._",
        ]
    )
    return "\n".join(lines)

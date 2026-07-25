# SPDX-License-Identifier: Apache-2.0
"""FIX 192 — Markdown renderer for PilotOS UI trust report freeze."""

from __future__ import annotations

from typing import Any


def render_pilotos_ui_trust_report_freeze(pilotos_ui_trust_report_freeze: dict[str, Any]) -> str:
    sections = pilotos_ui_trust_report_freeze.get("sections") or {}
    report = (sections.get("pilotos_ui_trust_report") or [{}])[0]

    lines = [
        "# PilotOS UI Trust Report Freeze (FIX 192 — trust_freeze ≠ trust_granting)",
        "",
        f"- repository: `{pilotos_ui_trust_report_freeze.get('repository', '')}`",
        f"- repo/issue: `{pilotos_ui_trust_report_freeze.get('repo_issue') or 'none'}`",
        f"- arc state: **{pilotos_ui_trust_report_freeze.get('arc_state', 'UNPROVEN')}**",
        f"- trust status: **{pilotos_ui_trust_report_freeze.get('trust_status', 'none')}**",
        f"- pilot 3 complete: **{pilotos_ui_trust_report_freeze.get('pilot_3_complete', False)}**",
        f"- freeze recorded: **{pilotos_ui_trust_report_freeze.get('trust_report_freeze_recorded', False)}**",
        f"- human trust approved: **{pilotos_ui_trust_report_freeze.get('human_trust_decision_approve', False)}**",
        f"- atlas expansion blocked: **{pilotos_ui_trust_report_freeze.get('atlas_expansion_blocked', True)}**",
        "",
        report.get("executive_summary", ""),
        "",
        pilotos_ui_trust_report_freeze.get("invariant", ""),
        "",
        "## PilotOS UI evidence timeline",
        "",
    ]

    for item in sections.get("pilotos_ui_evidence_timeline") or []:
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

    rec = (sections.get("pilotos_ui_trust_recommendation") or [{}])[0]
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
            "- `pilotos trust decision approve: …`",
            "- `pilotos trust decision hold: …`",
            "- `pilotos trust decision reject: …`",
            "- `pilotos trust decision defer: …`",
            "",
            "_Trust freeze composes PilotOS UI pilot arc evidence only — never re-runs pilots or grants trust automatically._",
        ]
    )
    return "\n".join(lines)

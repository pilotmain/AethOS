# SPDX-License-Identifier: Apache-2.0
"""FIX 195 — Markdown renderer for Nexora pilot arc orchestrator."""

from __future__ import annotations

from typing import Any


def render_nexora_pilot_arc_orchestrator(nexora_pilot_arc_orchestrator: dict[str, Any]) -> str:
    sections = nexora_pilot_arc_orchestrator.get("sections") or {}
    arc_state = nexora_pilot_arc_orchestrator.get("arc_state", "UNPROVEN")

    lines = [
        "# Nexora Pilot Arc Orchestrator (FIX 195 — orchestration ≠ trust granting)",
        "",
        f"- repository: `{nexora_pilot_arc_orchestrator.get('repository')}`",
        f"- repo/issue: `{nexora_pilot_arc_orchestrator.get('repo_issue')}`",
        f"- arc state: **{arc_state}**",
        f"- trust inheritance: **{nexora_pilot_arc_orchestrator.get('trust_inheritance_enabled', False)}** _(always false)_",
        f"- trust granting: **{nexora_pilot_arc_orchestrator.get('trust_granting_authority', False)}** _(always false)_",
        "",
        nexora_pilot_arc_orchestrator.get("invariant", ""),
        "",
        "## Nexora pilot dashboard",
        "",
    ]

    dashboard = (sections.get("nexora_pilot_dashboard") or [{}])[0]
    lines.append(f"- current stage: **{dashboard.get('arc_state')}**")
    lines.append(f"- evidence completeness: **{dashboard.get('evidence_completeness')}**")
    lines.append(f"- trust readiness: **{dashboard.get('trust_readiness')}**")
    last = dashboard.get("last_pilot_result") or {}
    if last:
        lines.append(f"- last audit: `{last.get('audit_id')}` outcome `{last.get('outcome')}`")
    lines.append("")

    gates = (sections.get("expansion_gates") or [{}])[0]
    lines.extend(
        [
            "## Expansion gates",
            "",
            f"- FIX 186 AethOS baseline: **{gates.get('aethos_trust_baseline_satisfied')}**",
            f"- FIX 192 PilotOS UI baseline: **{gates.get('pilotos_ui_trust_baseline_satisfied')}**",
            f"- FIX 194 Atlas Trader baseline: **{gates.get('atlas_trader_trust_baseline_satisfied')}**",
            f"- FIX 187 Nexora approved: **{gates.get('fix_187_expansion_approved')}**",
            f"- FIX 182 readiness: **{gates.get('fix_182_readiness_ok')}**",
            f"- eligible to start pilot 1: **{gates.get('eligible_to_start_pilot_1')}**",
            "",
            "## Nexora evidence registry",
            "",
        ]
    )
    for entry in sections.get("nexora_evidence_registry") or []:
        lines.append(f"- `{entry.get('evidence_id')}`: {entry.get('audit_id') or entry.get('kind')}")
    lines.append("")

    rec = (sections.get("nexora_trust_recommendation") or [{}])[0]
    lines.extend(
        [
            "## Trust recommendation",
            "",
            f"- status: **{rec.get('trust_status')}**",
            f"- rationale: {rec.get('rationale')}",
            "",
            "_Human trust decision occurs in FIX 196 — not here._",
        ]
    )
    return "\n".join(lines)

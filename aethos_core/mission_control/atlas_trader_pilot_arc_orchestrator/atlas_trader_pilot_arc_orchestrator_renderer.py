# SPDX-License-Identifier: Apache-2.0
"""FIX 193 — Markdown renderer for Atlas Trader pilot arc orchestrator."""

from __future__ import annotations

from typing import Any


def render_atlas_trader_pilot_arc_orchestrator(atlas_trader_pilot_arc_orchestrator: dict[str, Any]) -> str:
    sections = atlas_trader_pilot_arc_orchestrator.get("sections") or {}
    arc_state = atlas_trader_pilot_arc_orchestrator.get("arc_state", "UNPROVEN")

    lines = [
        "# Atlas Trader Pilot Arc Orchestrator (FIX 193 — orchestration ≠ trust granting)",
        "",
        f"- repository: `{atlas_trader_pilot_arc_orchestrator.get('repository')}`",
        f"- repo/issue: `{atlas_trader_pilot_arc_orchestrator.get('repo_issue')}`",
        f"- arc state: **{arc_state}**",
        f"- trust inheritance: **{atlas_trader_pilot_arc_orchestrator.get('trust_inheritance_enabled', False)}** _(always false)_",
        f"- trust granting: **{atlas_trader_pilot_arc_orchestrator.get('trust_granting_authority', False)}** _(always false)_",
        "",
        atlas_trader_pilot_arc_orchestrator.get("invariant", ""),
        "",
        "## Atlas pilot dashboard",
        "",
    ]

    dashboard = (sections.get("atlas_pilot_dashboard") or [{}])[0]
    lines.append(f"- current state: **{dashboard.get('arc_state')}**")
    last = dashboard.get("last_pilot_result") or {}
    if last:
        lines.append(f"- last audit: `{last.get('audit_id')}` outcome `{last.get('outcome')}`")
    lines.append("")

    gates = (sections.get("expansion_gates") or [{}])[0]
    lines.extend(
        [
            "## Expansion gates",
            "",
            f"- FIX 187 Atlas approved: **{gates.get('fix_187_expansion_approved')}**",
            f"- PilotOS UI baseline: **{gates.get('pilotos_ui_trust_baseline_satisfied')}**",
            f"- FIX 182 readiness: **{gates.get('fix_182_readiness_ok')}**",
            f"- eligible to start pilot 1: **{gates.get('eligible_to_start_pilot_1')}**",
            "",
            "## Atlas evidence registry",
            "",
        ]
    )
    for entry in sections.get("atlas_evidence_registry") or []:
        lines.append(f"- `{entry.get('evidence_id')}`: {entry.get('audit_id') or entry.get('kind')}")
    lines.append("")

    rec = (sections.get("atlas_trust_recommendation") or [{}])[0]
    lines.extend(
        [
            "## Trust recommendation",
            "",
            f"- status: **{rec.get('trust_status')}**",
            f"- rationale: {rec.get('rationale')}",
            "",
            "_Human trust decision occurs in FIX 194 — not here._",
        ]
    )
    return "\n".join(lines)

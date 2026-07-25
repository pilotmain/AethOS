# SPDX-License-Identifier: Apache-2.0
"""FIX 188 — Markdown renderer for PilotOS UI pilot arc orchestrator."""

from __future__ import annotations

from typing import Any


def render_pilotos_ui_pilot_arc_orchestrator(pilotos_ui_pilot_arc_orchestrator: dict[str, Any]) -> str:
    sections = pilotos_ui_pilot_arc_orchestrator.get("sections") or {}
    arc_state = pilotos_ui_pilot_arc_orchestrator.get("arc_state", "UNPROVEN")

    lines = [
        "# PilotOS UI Pilot Arc Orchestrator (FIX 188 — orchestration ≠ trust granting)",
        "",
        f"- repository: `{pilotos_ui_pilot_arc_orchestrator.get('repository')}`",
        f"- repo/issue: `{pilotos_ui_pilot_arc_orchestrator.get('repo_issue')}`",
        f"- arc state: **{arc_state}**",
        f"- trust transfer: **{pilotos_ui_pilot_arc_orchestrator.get('trust_transfer_enabled', False)}** _(always false)_",
        f"- automatic trust granting: **{pilotos_ui_pilot_arc_orchestrator.get('automatic_trust_granting_enabled', False)}** _(always false)_",
        "",
        pilotos_ui_pilot_arc_orchestrator.get("invariant", ""),
        "",
        "## State machine",
        "",
    ]

    sm = (sections.get("pilot_arc_state_machine") or [{}])[0]
    lines.append(f"- current: **{sm.get('current_state')}**")
    lines.append(f"- pilot 1 complete: **{sm.get('pilot_1_complete')}**")
    lines.append(f"- pilot 2 complete: **{sm.get('pilot_2_complete')}**")
    lines.append(f"- pilot 3 complete: **{sm.get('pilot_3_complete')}**")
    lines.append("")

    gates = (sections.get("expansion_gates") or [{}])[0]
    lines.extend(
        [
            "## Expansion gates",
            "",
            f"- FIX 187 approved: **{gates.get('fix_187_expansion_approved')}**",
            f"- FIX 182 readiness: **{gates.get('fix_182_readiness_ok')}**",
            f"- eligible to start pilot 1: **{gates.get('eligible_to_start_pilot_1')}**",
            "",
            "## Pilot evidence registry",
            "",
        ]
    )
    for entry in sections.get("pilot_evidence_registry") or []:
        lines.append(f"- `{entry.get('evidence_id')}`: {entry.get('audit_id') or entry.get('kind')}")
    lines.append("")

    rec = (sections.get("pilotos_ui_trust_recommendation") or [{}])[0]
    lines.extend(
        [
            "## Trust recommendation",
            "",
            f"- status: **{rec.get('trust_status')}**",
            f"- rationale: {rec.get('trust_rationale') or rec.get('rationale')}",
            "",
            "_Record trust with `pilot arc trust: CONDITIONALLY_TRUSTED — operator review complete`_",
        ]
    )
    return "\n".join(lines)

# SPDX-License-Identifier: Apache-2.0
"""FIX 154 — Markdown renderer for governance resilience."""

from __future__ import annotations

from typing import Any


def render_governance_resilience(resilience: dict[str, Any]) -> str:
    sections = resilience.get("sections") or {}
    scoring = sections.get("institutional_resilience_scoring") or {}

    lines = [
        "# Governance Resilience + Stress Simulation (FIX 154 — institutional resilience cognition)",
        "",
        f"- session_id: `{resilience.get('session_id', '')}`",
        f"- resilience records: **{resilience.get('resilience_record_count', 0)}**",
        f"- institutional resilience score: **{scoring.get('resilience_score', '—')}** ({scoring.get('resilience_label', '')})",
        f"- automatic governance adaptation: **{resilience.get('automatic_governance_adaptation_enabled', False)}** _(always false)_",
        f"- autonomous resilience correction: **{resilience.get('autonomous_resilience_correction_enabled', False)}** _(always false)_",
        "",
        resilience.get("invariant", ""),
        "",
        "_Institutional resilience cognition — simulation-only, never adaptive correction or override._",
        "",
    ]

    for title, key in (
        ("Governance stress scenarios", "governance_stress_scenarios"),
        ("Approval-chain overload simulation", "approval_chain_overload_simulation"),
        ("Incident surge resilience analysis", "incident_surge_resilience_analysis"),
        ("Quorum failure modeling", "quorum_failure_modeling"),
        ("Governance fragmentation stress", "governance_fragmentation_stress"),
        ("Operator loss/handoff resilience", "operator_loss_handoff_resilience"),
        ("Doctrine conflict escalation scenarios", "doctrine_conflict_escalation_scenarios"),
        ("Trust-boundary breach simulation", "trust_boundary_breach_simulation"),
        ("Governance recovery posture", "governance_recovery_posture"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None simulated._")
        for item in items:
            if item.get("scenario_id"):
                lines.append(f"- **{item.get('scenario_id')}** [{item.get('severity')}]: {item.get('description')}")
            elif item.get("simulated_pending") is not None:
                lines.append(
                    f"- overload simulated: current={item.get('current_pending')}, "
                    f"stress={item.get('simulated_pending')} — {item.get('impact')}"
                )
            elif item.get("surge_level"):
                lines.append(f"- surge **{item.get('surge_level')}** (incidents={item.get('open_incidents')}): {item.get('detail')}")
            elif item.get("quorum_risk"):
                lines.append(f"- quorum risk **{item.get('quorum_risk')}**: {item.get('detail')}")
            elif item.get("fragmentation_level"):
                lines.append(f"- fragmentation **{item.get('fragmentation_level')}**: {item.get('detail')}")
            elif item.get("handoff_id") or item.get("scenario"):
                lines.append(f"- **{item.get('scenario', item.get('handoff_id'))}**: {item.get('detail')}")
            elif item.get("escalation_level"):
                lines.append(f"- escalation [{item.get('escalation_level')}]: {item.get('detail')}")
            elif item.get("breach_simulated") is not None and item.get("simulation_id"):
                lines.append(f"- `{item.get('simulation_id')}` breach_simulated={item.get('breach_simulated')}: {item.get('detail')}")
            elif item.get("recovery_posture"):
                lines.append(
                    f"- posture **{item.get('recovery_posture')}** (integrity={item.get('integrity_score')}): {item.get('detail')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append(f"## Institutional resilience scoring")
    lines.append("")
    lines.append(f"- score **{scoring.get('resilience_score')}** ({scoring.get('resilience_label')})")
    lines.append(f"- {scoring.get('scoring_note', '')}")
    lines.append("")
    lines.append("_All stress simulations are `executable: false` and require human governance sovereignty._")
    return "\n".join(lines)

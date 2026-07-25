# SPDX-License-Identifier: Apache-2.0
"""FIX 144 — Markdown renderer for governance simulation."""

from __future__ import annotations

from typing import Any


def render_governance_simulation(simulation: dict[str, Any]) -> str:
    baseline = simulation.get("baseline_metrics") or {}
    lines = [
        "# Governance Simulation Sandbox (FIX 144 — hypothetical only)",
        "",
        f"- session_id: `{simulation.get('session_id', '')}`",
        f"- scenarios run: **{(simulation.get('impact_summary') or {}).get('scenarios_run', 0)}**",
        f"- live policy mutation: **{simulation.get('live_policy_mutation_enabled', False)}** _(always false)_",
        f"- auto policy update: **{simulation.get('auto_policy_update_enabled', False)}** _(always false)_",
        "",
        simulation.get("invariant", ""),
        "",
        "## Baseline (observed, not applied)",
        "",
        f"- governance friction index: **{baseline.get('governance_friction_index', '—')}**",
        f"- mission latency (est. hours): **{baseline.get('mission_latency_hours_est', '—')}**",
        f"- risk exposure: **{baseline.get('risk_exposure_label', '—')}** ({baseline.get('risk_exposure_score', '')})",
        "",
        "## Side-by-side comparison",
        "",
        "| configuration | friction | latency (h) | risk | Δ friction | Δ latency |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for row in simulation.get("side_by_side_comparison") or []:
        lines.append(
            f"| {row.get('title', row.get('configuration_id', ''))} "
            f"| {row.get('governance_friction', '—')} "
            f"| {row.get('mission_latency_hours', '—')} "
            f"| {row.get('risk_exposure', '—')} "
            f"| {row.get('friction_delta', '—')} "
            f"| {row.get('latency_delta_hours', '—')} |"
        )

    lines.extend(["", "## Scenario details", ""])
    for sim in simulation.get("simulations") or []:
        lines.append(f"### {sim.get('title', sim.get('scenario_id', ''))}")
        lines.append(f"_{sim.get('description', '')}_")
        impacts = sim.get("estimated_impacts") or {}
        fr = impacts.get("governance_friction") or {}
        lat = impacts.get("mission_latency_hours") or {}
        risk = impacts.get("risk_exposure") or {}
        lines.append(
            f"- friction: {fr.get('baseline')} → **{fr.get('simulated')}** (Δ {fr.get('delta')})"
        )
        lines.append(
            f"- latency: {lat.get('baseline')}h → **{lat.get('simulated')}h** (Δ {lat.get('delta')}h)"
        )
        lines.append(
            f"- risk: {risk.get('baseline')} → **{risk.get('simulated')}** (Δ score {risk.get('delta_score')})"
        )
        lines.append(f"- applied_to_live_policy: **{sim.get('applied_to_live_policy', False)}**")
        lines.append("")

    lines.append("_All simulations are `executable: false` — governance experimentation without mutation._")
    return "\n".join(lines)

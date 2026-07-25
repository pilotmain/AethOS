# SPDX-License-Identifier: Apache-2.0
"""FIX 144 — run governance simulations (hypothetical only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_insights.governance_insights_collectors import collect_governance_signals
from aethos_core.mission_control.governance_insights.governance_insights_service import build_governance_insights
from aethos_core.mission_control.governance_simulation.governance_simulation_contract import (
    AUTOMATIC_GOVERNANCE_TUNING_ENABLED_FIX_144,
    AUTO_POLICY_UPDATE_ENABLED_FIX_144,
    DEFAULT_SCENARIO_IDS,
    GOVERNANCE_SIMULATION_FIX,
    GOVERNANCE_SIMULATION_INVARIANT,
    GOVERNANCE_SIMULATION_SCHEMA_VERSION,
    LIVE_POLICY_MUTATION_ENABLED_FIX_144,
    MUTATION_PERFORMED_FIX_144,
    SIMULATION_EXECUTABLE,
)
from aethos_core.mission_control.governance_simulation.governance_simulation_scenarios import (
    _BASELINE_GATE_WEIGHTS,
    baseline_configuration,
    scenario_by_id,
    scenario_catalog,
)


@dataclass(frozen=True)
class GovernanceSimulationResult:
    ok: bool
    session_id: str
    simulation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _risk_label(score: float) -> str:
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _baseline_metrics(*, signals: dict[str, Any], insights: dict[str, Any]) -> dict[str, Any]:
    health = ((insights.get("insights") or {}).get("governance_health_metrics") or {})
    latency_rows = ((insights.get("insights") or {}).get("mission_completion_latency") or [])
    avg_latency = 0.0
    if latency_rows:
        avg_latency = sum(float(r.get("latency_hours") or 0) for r in latency_rows) / len(latency_rows)

    gate_counter = signals.get("gate_counter") or {}
    friction = min(
        100.0,
        float(health.get("governance_health_score") or 70) * -1 + 100
        + len(signals.get("rollbacks") or []) * 8
        + sum(gate_counter.values()) * 0.5,
    )
    risk = min(
        1.0,
        0.25
        + len([i for i in signals.get("incidents") or [] if str(i.get("status", "")).lower() not in {"closed", "resolved"}])
        * 0.15
        + len(signals.get("rollbacks") or []) * 0.08,
    )
    return {
        "governance_friction_index": round(friction, 2),
        "mission_latency_hours_est": round(avg_latency or 2.0, 2),
        "risk_exposure_score": round(risk, 3),
        "risk_exposure_label": _risk_label(risk),
        "approval_gate_weight_sum": round(sum(_BASELINE_GATE_WEIGHTS.values()), 2),
        "read_only": True,
    }


def _simulate_scenario(
    *,
    scenario: dict[str, Any],
    baseline_metrics: dict[str, Any],
    signals: dict[str, Any],
) -> dict[str, Any]:
    friction = float(baseline_metrics.get("governance_friction_index") or 0)
    latency = float(baseline_metrics.get("mission_latency_hours_est") or 0)
    risk = float(baseline_metrics.get("risk_exposure_score") or 0)

    sim_friction = max(0.0, min(100.0, friction * (1.0 + float(scenario.get("friction_bias") or 0))))
    sim_latency = max(0.0, latency + float(scenario.get("latency_bias_hours") or 0))
    sim_risk = max(0.0, min(1.0, risk + float(scenario.get("risk_bias") or 0)))

    open_incidents = len(
        [i for i in signals.get("incidents") or [] if str(i.get("status", "")).lower() not in {"closed", "resolved"}]
    )
    if scenario.get("configuration", {}).get("require_zero_open_incidents") and open_incidents:
        sim_friction += open_incidents * 5

    return {
        "scenario_id": scenario.get("scenario_id"),
        "title": scenario.get("title"),
        "description": scenario.get("description"),
        "configuration": scenario.get("configuration"),
        "estimated_impacts": {
            "governance_friction": {
                "baseline": baseline_metrics.get("governance_friction_index"),
                "simulated": round(sim_friction, 2),
                "delta": round(sim_friction - friction, 2),
            },
            "mission_latency_hours": {
                "baseline": baseline_metrics.get("mission_latency_hours_est"),
                "simulated": round(sim_latency, 2),
                "delta": round(sim_latency - latency, 2),
            },
            "risk_exposure": {
                "baseline": baseline_metrics.get("risk_exposure_label"),
                "simulated": _risk_label(sim_risk),
                "baseline_score": baseline_metrics.get("risk_exposure_score"),
                "simulated_score": round(sim_risk, 3),
                "delta_score": round(sim_risk - risk, 3),
            },
        },
        "executable": SIMULATION_EXECUTABLE,
        "applied_to_live_policy": False,
        "read_only": True,
    }


def _side_by_side(results: list[dict[str, Any]], *, baseline_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "configuration_id": "baseline_observed",
            "title": "Baseline (observed, not applied)",
            "governance_friction": baseline_metrics.get("governance_friction_index"),
            "mission_latency_hours": baseline_metrics.get("mission_latency_hours_est"),
            "risk_exposure": baseline_metrics.get("risk_exposure_label"),
            "read_only": True,
        }
    ]
    for sim in results:
        impacts = sim.get("estimated_impacts") or {}
        rows.append(
            {
                "configuration_id": sim.get("scenario_id"),
                "title": sim.get("title"),
                "governance_friction": impacts.get("governance_friction", {}).get("simulated"),
                "mission_latency_hours": impacts.get("mission_latency_hours", {}).get("simulated"),
                "risk_exposure": impacts.get("risk_exposure", {}).get("simulated"),
                "friction_delta": impacts.get("governance_friction", {}).get("delta"),
                "latency_delta_hours": impacts.get("mission_latency_hours", {}).get("delta"),
                "risk_delta_score": impacts.get("risk_exposure", {}).get("delta_score"),
                "read_only": True,
            }
        )
    return rows


def run_governance_simulation(
    *,
    session_id: str,
    scenario_ids: list[str] | None = None,
) -> GovernanceSimulationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    ids = scenario_ids or list(DEFAULT_SCENARIO_IDS)

    signals = collect_governance_signals(session_id=sid)
    insights_result = build_governance_insights(session_id=sid)
    insights = insights_result.insights if insights_result.ok else {}

    baseline_cfg = baseline_configuration(signals=signals)
    baseline_metrics = _baseline_metrics(signals=signals, insights=insights)

    results: list[dict[str, Any]] = []
    for sid_key in ids:
        scenario = scenario_by_id(sid_key.strip())
        if not scenario:
            continue
        results.append(_simulate_scenario(scenario=scenario, baseline_metrics=baseline_metrics, signals=signals))

    if not results:
        return GovernanceSimulationResult(
            ok=False,
            session_id=sid,
            blockers=["no_valid_scenarios"],
            detail="Provide valid scenario_ids from the governance simulation catalog.",
        )

    simulation: dict[str, Any] = {
        "schema_version": GOVERNANCE_SIMULATION_SCHEMA_VERSION,
        "fix": GOVERNANCE_SIMULATION_FIX,
        "exported_at": _exported_at(),
        "simulation_only": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_144,
        "live_policy_mutation_enabled": LIVE_POLICY_MUTATION_ENABLED_FIX_144,
        "auto_policy_update_enabled": AUTO_POLICY_UPDATE_ENABLED_FIX_144,
        "automatic_governance_tuning_enabled": AUTOMATIC_GOVERNANCE_TUNING_ENABLED_FIX_144,
        "invariant": GOVERNANCE_SIMULATION_INVARIANT,
        "session_id": sid,
        "baseline_configuration": baseline_cfg,
        "baseline_metrics": baseline_metrics,
        "scenario_catalog": [{"scenario_id": s["scenario_id"], "title": s["title"]} for s in scenario_catalog()],
        "simulations": results,
        "side_by_side_comparison": _side_by_side(results, baseline_metrics=baseline_metrics),
        "impact_summary": {
            "lowest_simulated_friction": min(
                (r.get("estimated_impacts") or {}).get("governance_friction", {}).get("simulated", 999) for r in results
            ),
            "highest_simulated_friction": max(
                (r.get("estimated_impacts") or {}).get("governance_friction", {}).get("simulated", 0) for r in results
            ),
            "scenarios_run": len(results),
            "executable": SIMULATION_EXECUTABLE,
        },
        "sources": {
            "governance_insights_fix_143": insights_result.ok,
            "governance_signals": True,
        },
    }
    return GovernanceSimulationResult(
        ok=True,
        session_id=sid,
        simulation=simulation,
        detail="Governance simulation complete (hypothetical only — no live policy mutation).",
    )

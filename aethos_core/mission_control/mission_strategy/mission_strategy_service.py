# SPDX-License-Identifier: Apache-2.0
"""FIX 145 — strategic operational reasoning from memory, insights, and simulations."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_insights.governance_insights_service import build_governance_insights
from aethos_core.mission_control.governance_simulation.governance_simulation_service import run_governance_simulation
from aethos_core.mission_control.mission_strategy.mission_strategy_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_145,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_145,
    AUTONOMOUS_PLANNING_ENABLED_FIX_145,
    AUTONOMOUS_REPRIORITIZATION_ENABLED_FIX_145,
    MISSION_STRATEGY_FIX,
    MISSION_STRATEGY_INVARIANT,
    MISSION_STRATEGY_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_145,
    ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145,
    STRATEGY_RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_service import (
    build_cross_session_operational_memory,
)
from aethos_core.mission_control.operational_memory.operational_memory_service import build_operational_memory_graph


@dataclass(frozen=True)
class MissionStrategyResult:
    ok: bool
    session_id: str
    strategy: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _rec(*, kind: str, recommendation: str, rationale: str = "", priority: str = "medium", **extra: Any) -> dict[str, Any]:
    return {
        "kind": kind,
        "recommendation": recommendation,
        "rationale": rationale,
        "priority": priority,
        "executable": STRATEGY_RECOMMENDATION_EXECUTABLE,
        "read_only": True,
        **extra,
    }


def _long_running_mission_themes(*, cross_session: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []
    org = cross_session.get("organizational_memory") or {}
    for row in org.get("missions_across_sessions") or []:
        if int(row.get("record_count") or 0) >= 2:
            themes.append(
                {
                    "theme": f"recurring_mission:{row.get('key', '')}",
                    "kind": row.get("kind"),
                    "session_ids": row.get("session_ids"),
                    "record_count": row.get("record_count"),
                    "read_only": True,
                }
            )
    gate_themes: Counter[str] = Counter()
    for rec in records:
        for gate in rec.get("gate_keys") or []:
            gate_themes[str(gate)] += 1
    for gate, count in gate_themes.most_common(5):
        if count >= 2:
            themes.append(
                {
                    "theme": f"governance_gate:{gate}",
                    "occurrences": count,
                    "read_only": True,
                }
            )
    return themes[:12]


def _operational_drift(*, graph: dict[str, Any], insights: dict[str, Any]) -> list[dict[str, Any]]:
    drift: list[dict[str, Any]] = []
    health = ((insights.get("insights") or {}).get("governance_health_metrics") or {})
    if int(health.get("governance_health_score") or 100) < 75:
        drift.append(
            {
                "signal": "governance_health_degraded",
                "detail": f"Meta-governance health score {health.get('governance_health_score')}.",
                "severity": "medium",
                "read_only": True,
            }
        )
    blockers = len(graph.get("recurring_blockers") or [])
    if blockers >= 3:
        drift.append(
            {
                "signal": "elevated_session_blockers",
                "detail": f"{blockers} recurring blocker pattern(s) in session graph.",
                "severity": "medium",
                "read_only": True,
            }
        )
    pending = int(health.get("pending_approvals_focal_session") or 0)
    if pending >= 2:
        drift.append(
            {
                "signal": "approval_queue_drift",
                "detail": f"{pending} pending approvals vs historical baseline.",
                "severity": "medium",
                "read_only": True,
            }
        )
    return drift


def _strategic_bottlenecks(*, cross_session: dict[str, Any], insights: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    org = cross_session.get("organizational_memory") or {}
    for row in org.get("historical_blockers") or []:
        if row.get("cross_session") or int(row.get("occurrences") or 0) >= 2:
            out.append(
                {
                    "bottleneck": row.get("blocker"),
                    "occurrences": row.get("occurrences"),
                    "cross_session": row.get("cross_session"),
                    "strategic_weight": "high" if row.get("cross_session") else "medium",
                    "read_only": True,
                }
            )
    for item in ((insights.get("insights") or {}).get("approval_bottlenecks") or []):
        out.append(
            {
                "bottleneck": item.get("insight"),
                "gate_id": item.get("gate_id"),
                "strategic_weight": item.get("severity", "medium"),
                "read_only": True,
            }
        )
    return out[:15]


def _mission_outcome_comparison(*, cross_session: dict[str, Any]) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    for chain in (cross_session.get("organizational_memory") or {}).get("mission_ancestry") or []:
        comparisons.append(
            {
                "plan_id": chain.get("plan_id"),
                "depth": chain.get("depth"),
                "ancestry_span": len(chain.get("ancestry") or []),
                "read_only": True,
            }
        )
    for row in (cross_session.get("organizational_memory") or {}).get("mission_completion_latency") or []:
        comparisons.append(
            {
                "plan_id": row.get("plan_id"),
                "latency_hours": row.get("latency_hours"),
                "record_snapshots": row.get("record_snapshots"),
                "outcome_signal": "slow" if float(row.get("latency_hours") or 0) > 4 else "normal",
                "read_only": True,
            }
        )
    return comparisons[:15]


def _governance_maturity_priorities(*, simulation: dict[str, Any], insights: dict[str, Any]) -> list[dict[str, Any]]:
    priorities: list[dict[str, Any]] = []
    sims = simulation.get("simulations") or []
    if sims:
        lowest_friction = min(
            sims,
            key=lambda s: float((s.get("estimated_impacts") or {}).get("governance_friction", {}).get("simulated", 999)),
        )
        priorities.append(
            _rec(
                kind="governance_maturity",
                recommendation=(
                    f"Study scenario `{lowest_friction.get('scenario_id')}` in simulation sandbox before any "
                    "future policy change — lowest estimated friction among hypotheticals."
                ),
                rationale="From FIX 144 governance simulation (not applied).",
                priority="medium",
            )
        )
    friction = ((insights.get("insights") or {}).get("governance_friction") or [])
    if friction:
        priorities.append(
            _rec(
                kind="governance_maturity",
                recommendation="Address view-only gates and chat-governance friction before expanding UI approval surface.",
                rationale="Meta-governance friction signals observed.",
                priority="high",
            )
        )
    return priorities


def _operational_hardening(*, graph: dict[str, Any], insights: dict[str, Any]) -> list[dict[str, Any]]:
    areas: list[dict[str, Any]] = []
    ver_gaps = ((insights.get("insights") or {}).get("verification_gaps") or [])
    if ver_gaps:
        areas.append(
            _rec(
                kind="operational_hardening",
                recommendation="Harden workspace verification evidence collection before PR lifecycle stages.",
                rationale=f"{len(ver_gaps)} verification gap signal(s).",
                priority="high",
            )
        )
    if int((graph.get("graph") or {}).get("stats", {}).get("node_count") or 0) < 5:
        areas.append(
            _rec(
                kind="operational_hardening",
                recommendation="Increase evidence bundle export and replay usage to enrich operational graph depth.",
                rationale="Thin session operational graph.",
                priority="medium",
            )
        )
    return areas


def _unstable_rollout_patterns(*, insights: dict[str, Any], cross_session: dict[str, Any]) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    for row in ((insights.get("insights") or {}).get("high_risk_rollout_sequences") or []):
        patterns.append(
            {
                "pattern": row.get("insight"),
                "severity": row.get("severity"),
                "execution_id": row.get("execution_id"),
                "read_only": True,
            }
        )
    for row in (cross_session.get("organizational_memory") or {}).get("rollout_lineage") or []:
        stage = str(row.get("current_stage") or "").lower()
        if stage in {"rollback", "incident", "canary", "promote"}:
            patterns.append(
                {
                    "pattern": f"rollout_stage:{stage}",
                    "recorded_at": row.get("recorded_at"),
                    "read_only": True,
                }
            )
    return patterns[:10]


def _risk_concentration(*, cross_session: dict[str, Any], insights: dict[str, Any]) -> dict[str, Any]:
    org = cross_session.get("organizational_memory") or {}
    open_incidents = len(org.get("recurring_incidents") or [])
    rollbacks = len(((insights.get("insights") or {}).get("rollback_patterns") or []))
    cross_blockers = len([b for b in org.get("historical_blockers") or [] if b.get("cross_session")])
    score = min(1.0, 0.2 + open_incidents * 0.1 + rollbacks * 0.12 + cross_blockers * 0.08)
    label = "high" if score >= 0.55 else "medium" if score >= 0.35 else "low"
    return {
        "concentration_score": round(score, 3),
        "concentration_label": label,
        "factors": {
            "recurring_incidents": open_incidents,
            "rollback_signals": rollbacks,
            "cross_session_blockers": cross_blockers,
        },
        "read_only": True,
    }


def _high_friction_archetypes(*, simulation: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    archetypes: list[dict[str, Any]] = []
    baseline_friction = float((simulation.get("baseline_metrics") or {}).get("governance_friction_index") or 0)
    if baseline_friction >= 40:
        archetypes.append(
            {
                "archetype": "high_friction_governed_delivery",
                "friction_index": baseline_friction,
                "detail": "Session baseline friction elevated — typical of multi-gate software delivery missions.",
                "read_only": True,
            }
        )
    plan_counts: Counter[str] = Counter(str(r.get("plan_id") or "") for r in records if r.get("plan_id"))
    for plan_id, count in plan_counts.items():
        if count >= 3:
            archetypes.append(
                {
                    "archetype": "long_running_plan",
                    "plan_id": plan_id,
                    "memory_snapshots": count,
                    "detail": "Repeated memory ingests suggest extended mission duration.",
                    "read_only": True,
                }
            )
    return archetypes


def build_mission_strategy(*, session_id: str) -> MissionStrategyResult:
    sid = (session_id or "default").strip()[:64] or "default"

    graph_result = build_operational_memory_graph(session_id=sid)
    graph = graph_result.graph if graph_result.ok else {}

    cross_result = build_cross_session_operational_memory(session_id=sid, ingest_current=True)
    cross_session = cross_result.memory if cross_result.ok else {}

    insights_result = build_governance_insights(session_id=sid)
    insights = insights_result.insights if insights_result.ok else {}

    simulation_result = run_governance_simulation(session_id=sid)
    simulation = simulation_result.simulation if simulation_result.ok else {}

    records = []
    from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
        list_operational_memory_records,
    )

    records = list_operational_memory_records(limit=200)

    sections = {
        "long_running_mission_themes": _long_running_mission_themes(cross_session=cross_session, records=records),
        "operational_drift": _operational_drift(graph=graph, insights=insights),
        "strategic_bottlenecks": _strategic_bottlenecks(cross_session=cross_session, insights=insights),
        "mission_outcome_comparison": _mission_outcome_comparison(cross_session=cross_session),
        "governance_maturity_priorities": _governance_maturity_priorities(
            simulation=simulation, insights=insights
        ),
        "operational_hardening_areas": _operational_hardening(graph=graph, insights=insights),
        "unstable_rollout_patterns": _unstable_rollout_patterns(
            insights=insights, cross_session=cross_session
        ),
        "organizational_risk_concentration": _risk_concentration(
            cross_session=cross_session, insights=insights
        ),
        "high_friction_mission_archetypes": _high_friction_archetypes(
            simulation=simulation, records=records
        ),
    }

    recs: list[dict[str, Any]] = []
    for key in ("governance_maturity_priorities", "operational_hardening_areas"):
        recs.extend(sections.get(key) or [])

    strategy: dict[str, Any] = {
        "schema_version": MISSION_STRATEGY_SCHEMA_VERSION,
        "fix": MISSION_STRATEGY_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_145,
        "autonomous_planning_enabled": AUTONOMOUS_PLANNING_ENABLED_FIX_145,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_145,
        "autonomous_reprioritization_enabled": AUTONOMOUS_REPRIORITIZATION_ENABLED_FIX_145,
        "organizational_self_direction_enabled": ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_145,
        "invariant": MISSION_STRATEGY_INVARIANT,
        "session_id": sid,
        "sections": sections,
        "strategic_recommendations": recs,
        "recommendation_count": len(recs),
        "all_recommendations_executable": False,
        "sources": {
            "operational_memory": graph_result.ok,
            "cross_session_memory": cross_result.ok,
            "governance_insights": insights_result.ok,
            "governance_simulation": simulation_result.ok,
        },
    }
    return MissionStrategyResult(
        ok=True,
        session_id=sid,
        strategy=strategy,
        detail="Mission strategy analysis complete (read-only strategic cognition).",
    )

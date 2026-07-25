# SPDX-License-Identifier: Apache-2.0
"""FIX 343 / WORKSTREAM_E1 — intelligence performance analysis executor."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    BASELINE_COMPOSE_TIMINGS_SEC,
    INTELLIGENCE_COMPOSE_DEPENDENCIES,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_store import (
    list_compose_hotspot_registry_entries,
    list_compose_timing_registry_entries,
    list_performance_opportunity_registry_entries,
    register_compose_hotspot,
    register_compose_timing,
    register_performance_opportunity,
)


def _filter_session(rows: list[dict[str, Any]], *, session_id: str | None) -> list[dict[str, Any]]:
    if not session_id:
        return rows
    return [row for row in rows if str(row.get("session_id") or "") == session_id]


def _dependency_fan_in() -> dict[str, int]:
    fan_in: dict[str, int] = {}
    for module, deps in INTELLIGENCE_COMPOSE_DEPENDENCIES.items():
        fan_in.setdefault(module, 0)
        for dep in deps:
            fan_in[dep] = fan_in.get(dep, 0) + 1
    return fan_in


def _dependency_fan_out() -> dict[str, int]:
    return {module: len(deps) for module, deps in INTELLIGENCE_COMPOSE_DEPENDENCIES.items()}


def _duplicate_compose_paths() -> list[dict[str, Any]]:
    shared: dict[str, list[str]] = {}
    for module, deps in INTELLIGENCE_COMPOSE_DEPENDENCIES.items():
        for dep in deps:
            shared.setdefault(dep, []).append(module)

    duplicates: list[dict[str, Any]] = []
    for dep, consumers in sorted(shared.items(), key=lambda item: len(item[1]), reverse=True):
        if len(consumers) >= 2:
            duplicates.append(
                {
                    "dependency": dep,
                    "consumer_count": len(consumers),
                    "consumers": consumers,
                    "recomputation_risk": len(consumers) >= 3,
                }
            )
    return duplicates


def _recursive_fan_in_chains() -> list[dict[str, Any]]:
    chains: list[dict[str, Any]] = []
    if "FIX 322" in INTELLIGENCE_COMPOSE_DEPENDENCIES.get("FIX 323", ()):
        chains.append(
            {
                "chain": ["FIX 323", "FIX 322", "FIX 319", "FIX 295"],
                "description": "Value realization re-composes PMF which re-composes feedback and capability registry",
                "recursive": True,
            }
        )
    if "FIX 319" in INTELLIGENCE_COMPOSE_DEPENDENCIES.get("FIX 322", ()):
        chains.append(
            {
                "chain": ["FIX 322", "FIX 319", "FIX 295"],
                "description": "PMF compose pulls full feedback intelligence chain",
                "recursive": False,
            }
        )
    return chains


def sync_compose_timing_registry(*, session_id: str, use_live_probe: bool = False) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    fan_in = _dependency_fan_in()
    fan_out = _dependency_fan_out()

    live_timings: dict[str, float] = {}
    if use_live_probe:
        live_timings = _probe_fast_modules(session_id=session_id)

    for module in sorted(INTELLIGENCE_COMPOSE_DEPENDENCIES):
        duration_sec = live_timings.get(module) or BASELINE_COMPOSE_TIMINGS_SEC.get(module, 0.0)
        entry = register_compose_timing(
            entry={
                "timing_id": f"timing-{module.replace(' ', '-').lower()}",
                "session_id": session_id,
                "module": module,
                "duration_sec": round(duration_sec, 3),
                "dependency_fan_in": fan_in.get(module, 0),
                "dependency_fan_out": fan_out.get(module, 0),
                "source": "live_probe" if module in live_timings else "baseline_measurement",
                "truth_reduction_performed": False,
            }
        )
        entries.append(entry)

    return entries


def _probe_fast_modules(*, session_id: str) -> dict[str, float]:
    """Measure only fast leaf modules — avoids multi-hour test runs."""
    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
        build_autonomous_capability_registry,
    )
    from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
        build_capability_registry_runtime_integration,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
        build_tenant_onboarding_activation,
    )

    probes = {
        "FIX 295": build_autonomous_capability_registry,
        "FIX 296": build_capability_registry_runtime_integration,
        "FIX 301": build_tenant_onboarding_activation,
    }
    timings: dict[str, float] = {}
    for module, builder in probes.items():
        start = time.time()
        builder(session_id=session_id)
        timings[module] = round(time.time() - start, 3)
    return timings


def build_compose_timing_registry(*, session_id: str) -> dict[str, Any]:
    entries = sync_compose_timing_registry(session_id=session_id)
    stored = _filter_session(list_compose_timing_registry_entries(), session_id=session_id)
    total_duration = sum(float(row.get("duration_sec") or 0.0) for row in stored)

    return {
        "registry_id": "compose-timing-registry",
        "timing_count": len(stored),
        "total_compose_duration_sec": round(total_duration, 3),
        "timings": stored,
        "truth_reduction_performed": False,
        "read_only": True,
    }


def build_compose_dependency_report(*, session_id: str) -> dict[str, Any]:
    _ = session_id
    duplicates = _duplicate_compose_paths()
    chains = _recursive_fan_in_chains()
    fan_in = _dependency_fan_in()

    expensive = []
    for module, duration in BASELINE_COMPOSE_TIMINGS_SEC.items():
        if duration >= 60.0:
            expensive.append(
                {
                    "module": module,
                    "duration_sec": duration,
                    "fan_in": fan_in.get(module, 0),
                    "consumers": [
                        consumer
                        for consumer, deps in INTELLIGENCE_COMPOSE_DEPENDENCIES.items()
                        if module in deps
                    ],
                }
            )

    return {
        "report_id": "compose-dependency-report",
        "duplicate_compose_paths": duplicates,
        "recursive_fan_in_chains": chains,
        "expensive_evidence_chains": sorted(expensive, key=lambda row: row["duration_sec"], reverse=True),
        "dependency_graph": {
            module: {"depends_on": list(deps), "fan_out": len(deps), "fan_in": fan_in.get(module, 0)}
            for module, deps in INTELLIGENCE_COMPOSE_DEPENDENCIES.items()
        },
        "read_only": True,
    }


def build_evidence_cache_report(*, session_id: str) -> dict[str, Any]:
    _ = session_id
    return {
        "report_id": "evidence-cache-report",
        "reusable_evidence": [
            {"module": "FIX 295", "class": "slow_changing_evidence", "cacheable": True, "ttl_recommendation": "session"},
            {"module": "FIX 296", "class": "slow_changing_evidence", "cacheable": True, "ttl_recommendation": "session"},
            {"module": "FIX 301", "class": "slow_changing_evidence", "cacheable": True, "ttl_recommendation": "session"},
            {"module": "FIX 318", "class": "slow_changing_evidence", "cacheable": True, "ttl_recommendation": "hourly"},
        ],
        "immutable_evidence": [
            {"module": "governance_contract", "class": "static_evidence", "cacheable": True, "ttl_recommendation": "permanent"},
            {"module": "certification_requirements", "class": "static_evidence", "cacheable": True, "ttl_recommendation": "permanent"},
        ],
        "dynamic_evidence": [
            {"module": "FIX 319", "class": "dynamic_evidence", "cacheable": False, "stale_boundary": "on_feedback_intake"},
            {"module": "FIX 322", "class": "dynamic_evidence", "cacheable": "partial", "stale_boundary": "on_pmf_review"},
            {"module": "FIX 323", "class": "dynamic_evidence", "cacheable": "partial", "stale_boundary": "on_value_outcome"},
        ],
        "truth_reduction_performed": False,
        "read_only": True,
    }


def build_incremental_compose_strategy(*, session_id: str) -> dict[str, Any]:
    cache_report = build_evidence_cache_report(session_id=session_id)
    return {
        "strategy_id": "incremental-compose-strategy",
        "static_evidence": [row for row in cache_report.get("immutable_evidence") or []],
        "slow_changing_evidence": [row for row in cache_report.get("reusable_evidence") or []],
        "dynamic_evidence": [row for row in cache_report.get("dynamic_evidence") or []],
        "recommendations": [
            "Memoize FIX 295/296/301 at session boundary before FIX 322/323 compose",
            "Store composed PMF artifact for FIX 323 instead of full re-compose",
            "Invalidate dynamic modules only on review-record or intake events",
        ],
        "truth_reduction_performed": False,
        "read_only": True,
    }


def build_compose_hotspot_registry(*, session_id: str) -> dict[str, Any]:
    sync_compose_timing_registry(session_id=session_id)
    stored = _filter_session(list_compose_timing_registry_entries(), session_id=session_id)
    fan_in = _dependency_fan_in()

    hotspots: list[dict[str, Any]] = []
    for row in stored:
        module = str(row.get("module") or "")
        duration = float(row.get("duration_sec") or 0.0)
        if duration < 60.0 and fan_in.get(module, 0) < 2:
            continue
        hotspot = register_compose_hotspot(
            entry={
                "hotspot_id": f"hotspot-{module.replace(' ', '-').lower()}",
                "session_id": session_id,
                "module": module,
                "duration_sec": duration,
                "fan_in": fan_in.get(module, 0),
                "recomputation_count": fan_in.get(module, 0),
                "severity": "CRITICAL" if duration >= 3600 else "HIGH" if duration >= 300 else "MEDIUM",
            }
        )
        hotspots.append(hotspot)

    ranked = sorted(hotspots, key=lambda row: float(row.get("duration_sec") or 0.0), reverse=True)
    return {
        "registry_id": "compose-hotspot-registry",
        "hotspot_count": len(ranked),
        "hotspots": ranked,
        "slowest_module": ranked[0].get("module") if ranked else None,
        "read_only": True,
    }


def _build_opportunities(*, session_id: str) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    duplicates = _duplicate_compose_paths()

    for dup in duplicates[:3]:
        if dup.get("recomputation_risk"):
            opportunities.append(
                register_performance_opportunity(
                    entry={
                        "opportunity_id": f"e1-opp-dedup-{uuid4().hex[:6]}",
                        "session_id": session_id,
                        "title": f"Deduplicate {dup['dependency']} composition",
                        "description": (
                            f"{dup['dependency']} recomposed across {dup['consumer_count']} intelligence modules"
                        ),
                        "impact": "HIGH",
                        "effort": "MEDIUM",
                        "confidence": 0.85,
                        "category": "evidence_deduplication",
                        "truth_reduction_performed": False,
                    }
                )
            )

    for chain in _recursive_fan_in_chains():
        opportunities.append(
            register_performance_opportunity(
                entry={
                    "opportunity_id": f"e1-opp-chain-{uuid4().hex[:6]}",
                    "session_id": session_id,
                    "title": "Break recursive PMF/value realization compose chain",
                    "description": chain.get("description"),
                    "impact": "HIGH",
                    "effort": "HIGH",
                    "confidence": 0.8,
                    "category": "incremental_compose",
                    "truth_reduction_performed": False,
                }
            )
        )

    for module, duration in sorted(BASELINE_COMPOSE_TIMINGS_SEC.items(), key=lambda item: item[1], reverse=True)[:2]:
        opportunities.append(
            register_performance_opportunity(
                entry={
                    "opportunity_id": f"e1-opp-hotspot-{uuid4().hex[:6]}",
                    "session_id": session_id,
                    "title": f"Optimize {module} compose latency",
                    "description": f"Baseline compose duration {duration}s dominates platform reasoning cost",
                    "impact": "HIGH",
                    "effort": "HIGH" if duration >= 3600 else "MEDIUM",
                    "confidence": 0.9,
                    "category": "hotspot_optimization",
                    "truth_reduction_performed": False,
                }
            )
        )

    if not opportunities:
        opportunities.append(
            register_performance_opportunity(
                entry={
                    "opportunity_id": f"e1-opp-baseline-{uuid4().hex[:6]}",
                    "session_id": session_id,
                    "title": "Establish intelligence performance baseline",
                    "description": "Run compose timing probe to enrich performance registry",
                    "impact": "MEDIUM",
                    "effort": "LOW",
                    "confidence": 0.95,
                    "category": "baseline",
                    "truth_reduction_performed": False,
                }
            )
        )

    return opportunities


def build_performance_opportunity_registry(*, session_id: str) -> dict[str, Any]:
    _build_opportunities(session_id=session_id)
    stored = _filter_session(list_performance_opportunity_registry_entries(), session_id=session_id)
    return {
        "registry_id": "performance-opportunity-registry",
        "opportunity_count": len(stored),
        "opportunities": stored[-20:],
        "recommendation_only": True,
        "truth_reduction_performed": False,
        "read_only": True,
    }


def build_performance_priority_matrix(*, session_id: str) -> dict[str, Any]:
    build_performance_opportunity_registry(session_id=session_id)
    opportunities = _filter_session(list_performance_opportunity_registry_entries(), session_id=session_id)

    impact_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    effort_rank = {"LOW": 3, "MEDIUM": 2, "HIGH": 1}

    ranked: list[dict[str, Any]] = []
    for opp in opportunities:
        impact = str(opp.get("impact") or "MEDIUM")
        effort = str(opp.get("effort") or "MEDIUM")
        confidence = float(opp.get("confidence") or 0.5)
        score = impact_rank.get(impact, 2) * effort_rank.get(effort, 2) * confidence
        ranked.append({**opp, "priority_score": round(score, 3)})

    ranked.sort(key=lambda row: row.get("priority_score", 0), reverse=True)

    return {
        "matrix_id": "performance-priority-matrix",
        "ranked_opportunities": ranked[:10],
        "human_adoption_required": True,
        "truth_reduction_performed": False,
        "read_only": True,
    }


def compute_latency_trends(*, session_id: str) -> dict[str, Any]:
    registry = build_compose_timing_registry(session_id=session_id)
    hotspots = build_compose_hotspot_registry(session_id=session_id)
    total = float(registry.get("total_compose_duration_sec") or 0.0)
    slowest = hotspots.get("slowest_module")

    return {
        "total_compose_duration_sec": total,
        "slowest_module": slowest,
        "scalability_risk": total >= 3600 or slowest in {"FIX 322", "FIX 323"},
        "optimization_opportunity_count": build_performance_opportunity_registry(session_id=session_id).get(
            "opportunity_count", 0
        ),
        "read_only": True,
    }


def run_intelligence_performance_analysis(*, session_id: str, use_live_probe: bool = False) -> dict[str, Any]:
    sync_compose_timing_registry(session_id=session_id, use_live_probe=use_live_probe)
    timing = build_compose_timing_registry(session_id=session_id)
    dependencies = build_compose_dependency_report(session_id=session_id)
    cache = build_evidence_cache_report(session_id=session_id)
    incremental = build_incremental_compose_strategy(session_id=session_id)
    hotspots = build_compose_hotspot_registry(session_id=session_id)
    opportunities = build_performance_opportunity_registry(session_id=session_id)
    matrix = build_performance_priority_matrix(session_id=session_id)
    trends = compute_latency_trends(session_id=session_id)

    return {
        "ok": True,
        "session_id": session_id,
        "compose_timing_registry": timing,
        "compose_dependency_report": dependencies,
        "evidence_cache_report": cache,
        "incremental_compose_strategy": incremental,
        "compose_hotspot_registry": hotspots,
        "performance_opportunity_registry": opportunities,
        "performance_priority_matrix": matrix,
        "latency_trends": trends,
        "truth_reduction_performed": False,
        "detail": "Intelligence performance analysis complete — optimization preserves evidence integrity",
    }

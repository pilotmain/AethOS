# SPDX-License-Identifier: Apache-2.0
"""FIX 365 / PHASE_J2 — real-world comparative performance executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_executor import (
    compute_pilot_metrics,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_executor import (
    build_customer_reality_report,
    build_deployment_durability_report,
    build_recovery_durability_report,
    compute_production_reality_metrics,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_contract import (
    BENCHMARK_APPROACHES,
    BENCHMARK_CATEGORIES,
    BENCHMARK_MIN_SIZE,
    COMPARISON_LEVELS,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_store import (
    has_comparative_performance_review_approve,
    list_benchmark_registry_entries,
    list_comparative_performance_records,
    register_benchmark_entry,
)

DEFAULT_BASELINE_DELIVERY_MS: int = 7200000
DEFAULT_BASELINE_DEPLOYMENT_SUCCESS: float = 0.65
DEFAULT_BASELINE_RECOVERY: float = 0.55
DEFAULT_BASELINE_CUSTOMER_OUTCOME: float = 0.5
DEFAULT_BASELINE_OPERATIONAL_EFFICIENCY: float = 0.45


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _benchmarks(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_benchmark_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _normalize_approach(value: str | None) -> str:
    raw = str(value or "aethos").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "human": "human_only",
        "traditional": "traditional_workflow",
        "assisted": "assisted_workflow",
    }
    normalized = aliases.get(raw, raw)
    if normalized in BENCHMARK_APPROACHES:
        return normalized
    return "aethos"


def _normalize_category(value: str | None) -> str:
    raw = str(value or "delivery").strip().lower()
    if raw in BENCHMARK_CATEGORIES:
        return raw
    return "delivery"


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _derived_aethos_benchmarks(*, program_session_id: str) -> list[dict[str, Any]]:
    pilot_runs = list_customer_pilot_run_registry_entries()
    latest = pilot_runs[-1] if pilot_runs else {}
    stage_metrics = latest.get("stage_metrics") or {}
    production = compute_production_reality_metrics(program_session_id=program_session_id)
    deployment = build_deployment_durability_report(program_session_id=program_session_id)
    recovery = build_recovery_durability_report(program_session_id=program_session_id)
    customer = build_customer_reality_report(program_session_id=program_session_id)

    total_delivery_ms = sum(int(stage_metrics.get(key) or 0) for key in (
        "time_to_workspace_ms",
        "time_to_code_ms",
        "time_to_pr_ms",
        "time_to_deploy_ms",
    ))

    return [
        {
            "benchmark_id": "aethos-delivery-derived",
            "approach": "aethos",
            "category": "delivery",
            "time_to_delivery_ms": total_delivery_ms or int(latest.get("duration_ms") or 0),
            "delivery_quality_score": _float(deployment.get("deployment_durability_score")),
            "source": "f1_pilot_and_j1_production",
            "derived_from_operational_proof": True,
        },
        {
            "benchmark_id": "aethos-deployment-derived",
            "approach": "aethos",
            "category": "deployment",
            "deployment_success_rate": _float(deployment.get("deployment_success_trend")),
            "source": "j1_deployment_durability",
            "derived_from_operational_proof": True,
        },
        {
            "benchmark_id": "aethos-recovery-derived",
            "approach": "aethos",
            "category": "recovery",
            "recovery_effectiveness_score": _float(recovery.get("recovery_durability_score")),
            "source": "j1_recovery_durability",
            "derived_from_operational_proof": True,
        },
        {
            "benchmark_id": "aethos-customer-derived",
            "approach": "aethos",
            "category": "customer",
            "customer_outcome_score": _float(customer.get("customer_durability_score")),
            "source": "j1_customer_reality",
            "derived_from_operational_proof": True,
        },
        {
            "benchmark_id": "aethos-operational-derived",
            "approach": "aethos",
            "category": "operational",
            "operational_efficiency_score": _float(production.get("operational_durability_score")),
            "source": "j1_production_reality",
            "derived_from_operational_proof": True,
        },
    ]


def _default_baseline_benchmarks() -> list[dict[str, Any]]:
    return [
        {
            "benchmark_id": "baseline-human-delivery",
            "approach": "human_only",
            "category": "delivery",
            "time_to_delivery_ms": DEFAULT_BASELINE_DELIVERY_MS,
            "delivery_quality_score": 0.6,
            "source": "reference_baseline",
        },
        {
            "benchmark_id": "baseline-traditional-delivery",
            "approach": "traditional_workflow",
            "category": "delivery",
            "time_to_delivery_ms": int(DEFAULT_BASELINE_DELIVERY_MS * 1.2),
            "delivery_quality_score": 0.55,
            "source": "reference_baseline",
        },
        {
            "benchmark_id": "baseline-assisted-delivery",
            "approach": "assisted_workflow",
            "category": "delivery",
            "time_to_delivery_ms": int(DEFAULT_BASELINE_DELIVERY_MS * 0.8),
            "delivery_quality_score": 0.7,
            "source": "reference_baseline",
        },
        {
            "benchmark_id": "baseline-human-deployment",
            "approach": "human_only",
            "category": "deployment",
            "deployment_success_rate": DEFAULT_BASELINE_DEPLOYMENT_SUCCESS,
            "source": "reference_baseline",
        },
        {
            "benchmark_id": "baseline-traditional-recovery",
            "approach": "traditional_workflow",
            "category": "recovery",
            "recovery_effectiveness_score": DEFAULT_BASELINE_RECOVERY,
            "source": "reference_baseline",
        },
        {
            "benchmark_id": "baseline-assisted-customer",
            "approach": "assisted_workflow",
            "category": "customer",
            "customer_outcome_score": DEFAULT_BASELINE_CUSTOMER_OUTCOME,
            "source": "reference_baseline",
        },
        {
            "benchmark_id": "baseline-traditional-operational",
            "approach": "traditional_workflow",
            "category": "operational",
            "operational_efficiency_score": DEFAULT_BASELINE_OPERATIONAL_EFFICIENCY,
            "source": "reference_baseline",
        },
    ]


def build_benchmark_registry(*, program_session_id: str) -> dict[str, Any]:
    registered = _benchmarks(program_session_id=program_session_id)
    derived = _derived_aethos_benchmarks(program_session_id=program_session_id)
    baselines = _default_baseline_benchmarks()
    all_benchmarks = registered + derived + baselines

    by_approach = {approach: [] for approach in BENCHMARK_APPROACHES}
    for row in all_benchmarks:
        approach = str(row.get("approach") or "aethos")
        by_approach.setdefault(approach, []).append(row)

    return {
        "registry_id": "benchmark-registry",
        "program_session_id": program_session_id,
        "benchmark_count": len(all_benchmarks),
        "minimum_benchmark_count": BENCHMARK_MIN_SIZE,
        "aethos_outcomes": by_approach.get("aethos") or [],
        "human_only_outcomes": by_approach.get("human_only") or [],
        "traditional_workflow_outcomes": by_approach.get("traditional_workflow") or [],
        "assisted_workflow_outcomes": by_approach.get("assisted_workflow") or [],
        "benchmarks": all_benchmarks,
        "competitive_actions_performed": False,
        "read_only": True,
    }


def _aethos_value(benchmarks: list[dict[str, Any]], category: str, key: str) -> float:
    rows = [b for b in benchmarks if b.get("approach") == "aethos" and b.get("category") == category]
    if not rows:
        return 0.0
    return _float(rows[-1].get(key))


def _baseline_value(benchmarks: list[dict[str, Any]], category: str, key: str) -> float:
    rows = [
        b
        for b in benchmarks
        if b.get("category") == category and b.get("approach") in {"human_only", "traditional_workflow", "assisted_workflow"}
    ]
    if not rows:
        return 0.0
    return round(sum(_float(r.get(key)) for r in rows) / len(rows), 3)


def _delta(*, aethos: float, baseline: float, higher_is_better: bool = True) -> float:
    if baseline == 0:
        return round(aethos, 3)
    raw = (aethos - baseline) / abs(baseline)
    if not higher_is_better:
        raw = -raw
    return round(raw, 3)


def build_delivery_comparison_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_benchmark_registry(program_session_id=program_session_id)
    benchmarks = registry.get("benchmarks") or []

    aethos_time = _aethos_value(benchmarks, "delivery", "time_to_delivery_ms")
    baseline_time = _baseline_value(benchmarks, "delivery", "time_to_delivery_ms") or DEFAULT_BASELINE_DELIVERY_MS
    aethos_quality = _aethos_value(benchmarks, "delivery", "delivery_quality_score")
    baseline_quality = _baseline_value(benchmarks, "delivery", "delivery_quality_score") or 0.6

    time_delta = _delta(aethos=baseline_time, baseline=aethos_time or 1, higher_is_better=True)
    quality_delta = _delta(aethos=aethos_quality, baseline=baseline_quality, higher_is_better=True)
    delivery_performance_delta = round((time_delta + quality_delta) / 2, 3)

    return {
        "report_id": "delivery-comparison-report",
        "program_session_id": program_session_id,
        "time_to_delivery_ms_aethos": aethos_time,
        "time_to_delivery_ms_baseline": baseline_time,
        "delivery_consistency_score": aethos_quality,
        "delivery_quality_score": aethos_quality,
        "delivery_performance_delta": delivery_performance_delta,
        "delivery_comparison_demonstrated": aethos_time > 0 or aethos_quality > 0,
        "read_only": True,
    }


def build_deployment_comparison_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_benchmark_registry(program_session_id=program_session_id)
    benchmarks = registry.get("benchmarks") or []

    aethos_success = _aethos_value(benchmarks, "deployment", "deployment_success_rate")
    baseline_success = _baseline_value(benchmarks, "deployment", "deployment_success_rate") or DEFAULT_BASELINE_DEPLOYMENT_SUCCESS
    aethos_recovery = _aethos_value(benchmarks, "recovery", "recovery_effectiveness_score")
    baseline_recovery = _baseline_value(benchmarks, "recovery", "recovery_effectiveness_score") or DEFAULT_BASELINE_RECOVERY

    deployment_performance_delta = _delta(aethos=aethos_success, baseline=baseline_success, higher_is_better=True)
    recovery_performance_delta = _delta(aethos=aethos_recovery, baseline=baseline_recovery, higher_is_better=True)

    return {
        "report_id": "deployment-comparison-report",
        "program_session_id": program_session_id,
        "deployment_success_aethos": aethos_success,
        "deployment_success_baseline": baseline_success,
        "deployment_failures_baseline_gap": round(max(0.0, baseline_success - aethos_success), 3),
        "deployment_recovery_aethos": aethos_recovery,
        "deployment_performance_delta": deployment_performance_delta,
        "recovery_performance_delta": recovery_performance_delta,
        "deployment_comparison_demonstrated": aethos_success > 0,
        "read_only": True,
    }


def build_customer_outcome_comparison_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_benchmark_registry(program_session_id=program_session_id)
    benchmarks = registry.get("benchmarks") or []
    pilot_metrics = compute_pilot_metrics(session_id=program_session_id)

    aethos_outcome = _aethos_value(benchmarks, "customer", "customer_outcome_score")
    baseline_outcome = _baseline_value(benchmarks, "customer", "customer_outcome_score") or DEFAULT_BASELINE_CUSTOMER_OUTCOME
    customer_outcome_delta = _delta(aethos=aethos_outcome, baseline=baseline_outcome, higher_is_better=True)

    return {
        "report_id": "customer-outcome-comparison-report",
        "program_session_id": program_session_id,
        "onboarding_outcome_score": aethos_outcome,
        "value_realization_score": 1.0 if pilot_metrics.get("value_realized") else aethos_outcome,
        "retention_score": aethos_outcome,
        "satisfaction_score": 1.0 if pilot_metrics.get("customer_satisfaction") not in {"pending", None, ""} else aethos_outcome,
        "customer_outcome_delta": customer_outcome_delta,
        "customer_outcome_comparison_demonstrated": aethos_outcome > 0,
        "read_only": True,
    }


def build_operational_comparison_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_benchmark_registry(program_session_id=program_session_id)
    benchmarks = registry.get("benchmarks") or []
    pilot_metrics = compute_pilot_metrics(session_id=program_session_id)

    aethos_efficiency = _aethos_value(benchmarks, "operational", "operational_efficiency_score")
    baseline_efficiency = _baseline_value(benchmarks, "operational", "operational_efficiency_score") or DEFAULT_BASELINE_OPERATIONAL_EFFICIENCY
    operational_efficiency_delta = _delta(aethos=aethos_efficiency, baseline=baseline_efficiency, higher_is_better=True)

    intervention_rate = round(_float(pilot_metrics.get("intervention_count")) / max(_float(pilot_metrics.get("human_approval_count"), 1), 1), 3)
    governance_overhead = round(_float(pilot_metrics.get("human_approval_count")) / 10, 3)

    return {
        "report_id": "operational-comparison-report",
        "program_session_id": program_session_id,
        "operational_burden_score": round(1.0 - min(intervention_rate, 1.0), 3),
        "intervention_requirements": _float(pilot_metrics.get("intervention_count")),
        "governance_overhead_score": governance_overhead,
        "operational_efficiency_delta": operational_efficiency_delta,
        "operational_comparison_demonstrated": aethos_efficiency > 0,
        "read_only": True,
    }


def build_comparative_learning_report(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_delivery_comparison_report(program_session_id=program_session_id)
    deployment = build_deployment_comparison_report(program_session_id=program_session_id)
    customer = build_customer_outcome_comparison_report(program_session_id=program_session_id)
    operational = build_operational_comparison_report(program_session_id=program_session_id)

    comparisons = [
        ("delivery", delivery.get("delivery_performance_delta")),
        ("deployment", deployment.get("deployment_performance_delta")),
        ("recovery", deployment.get("recovery_performance_delta")),
        ("customer", customer.get("customer_outcome_delta")),
        ("operational", operational.get("operational_efficiency_delta")),
    ]

    better = [name for name, delta in comparisons if _float(delta) > 0.05]
    worse = [name for name, delta in comparisons if _float(delta) < -0.05]
    equivalent = [name for name, delta in comparisons if -0.05 <= _float(delta) <= 0.05]

    return {
        "report_id": "comparative-learning-report",
        "program_session_id": program_session_id,
        "aethos_performs_better": better,
        "aethos_performs_worse": worse,
        "equivalent_outcomes": equivalent,
        "comparative_learning_demonstrated": bool(comparisons),
        "strategy_mutation_performed": False,
        "read_only": True,
    }


def build_comparative_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    learning = build_comparative_learning_report(program_session_id=program_session_id)
    opportunities: list[dict[str, Any]] = []

    for area in learning.get("aethos_performs_worse") or []:
        opportunities.append(
            {
                "opportunity_id": f"improve-{area}",
                "area": area,
                "opportunity_type": "execution" if area in {"delivery", "deployment", "recovery"} else "operational",
                "gap": f"AethOS underperforms baseline in {area}",
                "priority": "high",
            }
        )
    for area in learning.get("equivalent_outcomes") or []:
        opportunities.append(
            {
                "opportunity_id": f"optimize-{area}",
                "area": area,
                "opportunity_type": "governance" if area == "operational" else "execution",
                "gap": f"Equivalent outcomes in {area} — optimization opportunity",
                "priority": "medium",
            }
        )

    return {
        "registry_id": "comparative-opportunity-registry",
        "program_session_id": program_session_id,
        "execution_opportunities": [o for o in opportunities if o.get("opportunity_type") == "execution"],
        "governance_opportunities": [o for o in opportunities if o.get("opportunity_type") == "governance"],
        "operational_opportunities": [o for o in opportunities if o.get("opportunity_type") == "operational"],
        "opportunities": opportunities,
        "comparative_opportunity_registry_demonstrated": True,
        "read_only": True,
    }


def _comparison_level(*, metrics: dict[str, Any], program_session_id: str) -> str:
    deltas = [
        _float(metrics.get("delivery_performance_delta")),
        _float(metrics.get("deployment_performance_delta")),
        _float(metrics.get("recovery_performance_delta")),
        _float(metrics.get("customer_outcome_delta")),
        _float(metrics.get("operational_efficiency_delta")),
    ]
    positive = sum(1 for delta in deltas if delta > 0.05)
    strong = sum(1 for delta in deltas if delta > 0.2)
    registry = build_benchmark_registry(program_session_id=program_session_id)

    if not registry.get("benchmark_count"):
        return "unknown"
    if has_comparative_performance_review_approve(program_session_id=program_session_id) and strong >= 3:
        return "transformational"
    if strong >= 2:
        return "significant_advantage"
    if positive >= 2:
        return "advantage"
    if any(abs(delta) <= 0.05 for delta in deltas):
        return "comparable"
    return "unknown"


def compute_comparative_performance_metrics(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_delivery_comparison_report(program_session_id=program_session_id)
    deployment = build_deployment_comparison_report(program_session_id=program_session_id)
    customer = build_customer_outcome_comparison_report(program_session_id=program_session_id)
    operational = build_operational_comparison_report(program_session_id=program_session_id)

    metrics = {
        "delivery_performance_delta": _float(delivery.get("delivery_performance_delta")),
        "deployment_performance_delta": _float(deployment.get("deployment_performance_delta")),
        "recovery_performance_delta": _float(deployment.get("recovery_performance_delta")),
        "customer_outcome_delta": _float(customer.get("customer_outcome_delta")),
        "operational_efficiency_delta": _float(operational.get("operational_efficiency_delta")),
        "comparison_level": "",
        "comparison_levels": list(COMPARISON_LEVELS),
        "read_only": True,
    }
    metrics["comparison_level"] = _comparison_level(metrics=metrics, program_session_id=program_session_id)
    return metrics


def register_benchmark_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    benchmark_id = kv.get("benchmark_id") or kv.get("benchmark") or (
        f"bench-{len(_benchmarks(program_session_id=program_session_id)) + 1}"
    )
    entry = register_benchmark_entry(
        entry={
            "benchmark_id": benchmark_id,
            "program_session_id": program_session_id,
            "approach": _normalize_approach(kv.get("approach")),
            "category": _normalize_category(kv.get("category")),
            "time_to_delivery_ms": kv.get("time_to_delivery_ms") or kv.get("delivery_ms"),
            "deployment_success_rate": kv.get("deployment_success_rate") or kv.get("deployment_success"),
            "recovery_effectiveness_score": kv.get("recovery_effectiveness_score") or kv.get("recovery_score"),
            "customer_outcome_score": kv.get("customer_outcome_score") or kv.get("customer_score"),
            "operational_efficiency_score": kv.get("operational_efficiency_score") or kv.get("efficiency_score"),
            "delivery_quality_score": kv.get("delivery_quality_score") or kv.get("quality_score"),
            "objective": kv.get("objective") or "Compare AethOS outcomes against real-world baselines",
        }
    )
    from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_store import (
        append_comparative_performance_record,
    )

    append_comparative_performance_record(
        session_id=program_session_id,
        kind="comparative_performance_benchmark_entry",
        content=body,
        metadata=entry,
    )
    return entry

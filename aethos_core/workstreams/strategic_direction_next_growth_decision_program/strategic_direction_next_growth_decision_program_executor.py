# SPDX-License-Identifier: Apache-2.0
"""FIX 358 / WORKSTREAM_H1 — strategic direction & next-growth decision executor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    compute_validation_metrics,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    list_usage_observation_registry_entries,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_executor import (
    compute_platform_maturity_metrics,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_executor import (
    compute_evidence_maturity_metrics,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_executor import (
    compute_usage_adoption_metrics,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_executor import (
    compute_revenue_density_metrics,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_contract import (
    STRATEGIC_OUTCOME_CATEGORIES,
)

_AETHOS_CORE = Path(__file__).resolve().parents[2]
_WORKSTREAMS = _AETHOS_CORE / "workstreams"
_EXECUTION_TRACKS = _AETHOS_CORE / "execution_tracks"

GROWTH_PATHS: tuple[tuple[str, str], ...] = (
    ("customer_acquisition_expansion", "Acquire more customers via proven delivery and adoption loops"),
    ("enterprise_expansion", "Focus on governance-heavy enterprise deployments"),
    ("self_serve_expansion", "Expand self-serve onboarding and product-led growth"),
    ("partner_expansion", "Grow through provider and integration partners"),
)

PRODUCT_EXPANSION_AREAS: tuple[tuple[str, str], ...] = (
    ("aethos_core_expansion", "Deepen governed execution and delivery core"),
    ("mission_control_expansion", "Expand Mission Control intelligence and operator surfaces"),
    ("execution_expansion", "Extend ET1–ET5 reliability and certification coverage"),
    ("provider_expansion", "Broaden provider execution and operational proof"),
)

PROVIDER_STRATEGY_TARGETS: tuple[tuple[str, str], ...] = (
    ("railway_vercel", "Railway/Vercel maturity from governed deployment evidence"),
    ("aws", "AWS opportunity from multi-cloud operational proof patterns"),
    ("kubernetes", "Kubernetes opportunity from execution track composability"),
    ("azure", "Azure opportunity from enterprise provider expansion"),
    ("gcp", "GCP opportunity from ecosystem and partner expansion"),
)


def _load_store_rows(module_path: str, list_fn: str) -> list[dict[str, Any]]:
    try:
        mod = __import__(module_path, fromlist=[list_fn])
        rows = getattr(mod, list_fn)()
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []
    return []


def _g_baselines(*, program_session_id: str) -> dict[str, Any]:
    g1 = compute_evidence_maturity_metrics(program_session_id=program_session_id)
    g2 = compute_usage_adoption_metrics(program_session_id=program_session_id)
    g3 = compute_revenue_density_metrics(program_session_id=program_session_id)
    g4 = compute_platform_maturity_metrics(program_session_id=program_session_id)
    return {"g1": g1, "g2": g2, "g3": g3, "g4": g4}


def build_strategic_baseline_registry(*, program_session_id: str) -> dict[str, Any]:
    baselines = _g_baselines(program_session_id=program_session_id)
    return {
        "registry_id": "strategic-baseline-registry",
        "program_session_id": program_session_id,
        "g1_evidence_maturity": {
            "workstream": "WORKSTREAM_G1",
            "evidence_density_score": baselines["g1"].get("evidence_density_score"),
            "trust_maturity_score": baselines["g1"].get("trust_maturity_score"),
            "composed_read_only": True,
        },
        "g2_adoption_maturity": {
            "workstream": "WORKSTREAM_G2",
            "workflow_adoption_rate": baselines["g2"].get("workflow_adoption_rate"),
            "platform_dependence_score": baselines["g2"].get("platform_dependence_score"),
            "composed_read_only": True,
        },
        "g3_viability_maturity": {
            "workstream": "WORKSTREAM_G3",
            "business_viability_score": baselines["g3"].get("business_viability_score"),
            "revenue_density_score": baselines["g3"].get("revenue_density_score"),
            "composed_read_only": True,
        },
        "g4_readiness_maturity": {
            "workstream": "WORKSTREAM_G4",
            "overall_platform_maturity_score": baselines["g4"].get("overall_platform_maturity_score"),
            "platform_maturity_level": baselines["g4"].get("platform_maturity_level"),
            "composed_read_only": True,
        },
        "validation_chain_composed": True,
        "read_only": True,
    }


def _path_score(*, path_id: str, baselines: dict[str, dict[str, Any]]) -> float:
    g1 = baselines["g1"]
    g2 = baselines["g2"]
    g3 = baselines["g3"]
    g4 = baselines["g4"]

    if path_id == "customer_acquisition_expansion":
        return round(
            (
                float(g2.get("workflow_adoption_rate") or 0)
                + float(g3.get("expansion_score") or 0)
                + float(g3.get("adoption_strength") or 0)
            )
            / 3,
            3,
        )
    if path_id == "enterprise_expansion":
        return round(
            (
                float(g1.get("trust_maturity_score") or 0)
                + float(g4.get("evidence_maturity_score") or 0)
                + float(g4.get("architecture_maturity_score") or 0)
            )
            / 3,
            3,
        )
    if path_id == "self_serve_expansion":
        active_signal = min(1.0, int(g2.get("active_users") or 0) / 3)
        return round(
            (
                active_signal
                + float(g3.get("plan_utilization_score") or 0)
                + float(g4.get("customer_maturity_score") or 0)
            )
            / 3,
            3,
        )
    if path_id == "partner_expansion":
        return round(
            (
                float(g4.get("operational_maturity_score") or 0)
                + float(g3.get("expansion_score") or 0)
                + float(g2.get("workflow_adoption_rate") or 0)
            )
            / 3,
            3,
        )
    return 0.0


def build_growth_path_report(*, program_session_id: str) -> dict[str, Any]:
    baselines = _g_baselines(program_session_id=program_session_id)
    paths: list[dict[str, Any]] = []
    for path_id, description in GROWTH_PATHS:
        score = _path_score(path_id=path_id, baselines=baselines)
        paths.append(
            {
                "path_id": path_id,
                "description": description,
                "opportunity_score": score,
                "advisory_only": True,
            }
        )

    ranked = sorted(paths, key=lambda item: float(item.get("opportunity_score") or 0), reverse=True)
    return {
        "report_id": "growth-path-report",
        "program_session_id": program_session_id,
        "growth_paths": paths,
        "highest_opportunity_path": ranked[0]["path_id"] if ranked else None,
        "growth_opportunities_evaluated": len(paths) == len(GROWTH_PATHS),
        "strategy_execution_performed": False,
        "read_only": True,
    }


def build_product_expansion_report(*, program_session_id: str) -> dict[str, Any]:
    baselines = _g_baselines(program_session_id=program_session_id)
    g4 = baselines["g4"]
    areas: list[dict[str, Any]] = []

    area_scores = {
        "aethos_core_expansion": float(g4.get("execution_maturity_score") or 0),
        "mission_control_expansion": float(g4.get("architecture_maturity_score") or 0),
        "execution_expansion": float(g4.get("execution_maturity_score") or 0),
        "provider_expansion": float(g4.get("operational_maturity_score") or 0),
    }

    for area_id, description in PRODUCT_EXPANSION_AREAS:
        areas.append(
            {
                "area_id": area_id,
                "description": description,
                "expansion_score": round(area_scores.get(area_id, 0.0), 3),
                "advisory_only": True,
            }
        )

    return {
        "report_id": "product-expansion-report",
        "program_session_id": program_session_id,
        "expansion_areas": areas,
        "product_expansion_evaluated": len(areas) == len(PRODUCT_EXPANSION_AREAS),
        "roadmap_mutation_performed": False,
        "read_only": True,
    }


def build_provider_strategy_report(*, program_session_id: str) -> dict[str, Any]:
    deployment_rows = _load_store_rows(
        "aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store",
        "list_governed_deployment_execution_records",
    )
    railway_vercel_maturity = round(
        sum(1 for row in deployment_rows if row.get("passed") is True) / max(len(deployment_rows), 1),
        3,
    )

    d1_present = (_WORKSTREAMS / "phase2_provider_execution_expansion_program").is_dir()
    d2_present = (_WORKSTREAMS / "multi_cloud_operational_proof_program").is_dir()
    et_present = all(
        (_EXECUTION_TRACKS / slug).is_dir()
        for slug in (
            "governed_workspace_creation_repository_bootstrap",
            "governed_deployment_execution",
        )
    )

    providers: list[dict[str, Any]] = [
        {
            "provider": "railway_vercel",
            "maturity_score": railway_vercel_maturity,
            "deployment_evidence_count": len(deployment_rows),
            "status": "proven" if railway_vercel_maturity >= 0.5 else "emerging",
        },
        {
            "provider": "aws",
            "opportunity_score": 0.7 if d2_present else 0.4,
            "status": "opportunity",
            "advisory_only": True,
        },
        {
            "provider": "kubernetes",
            "opportunity_score": 0.65 if et_present else 0.35,
            "status": "opportunity",
            "advisory_only": True,
        },
        {
            "provider": "azure",
            "opportunity_score": 0.55 if d1_present else 0.3,
            "status": "opportunity",
            "advisory_only": True,
        },
        {
            "provider": "gcp",
            "opportunity_score": 0.5 if d2_present else 0.25,
            "status": "opportunity",
            "advisory_only": True,
        },
    ]

    return {
        "report_id": "provider-strategy-report",
        "program_session_id": program_session_id,
        "provider_targets": providers,
        "railway_vercel_maturity": railway_vercel_maturity,
        "provider_strategy_evaluated": len(providers) == len(PROVIDER_STRATEGY_TARGETS),
        "provider_mutation_performed": False,
        "read_only": True,
    }


def build_customer_strategy_report(*, program_session_id: str) -> dict[str, Any]:
    pilot_runs = list_customer_pilot_run_registry_entries()
    observations = list_usage_observation_registry_entries()

    segments: dict[str, dict[str, Any]] = {}
    for run in pilot_runs:
        session_id = str(run.get("session_id") or "")
        use_case = str(run.get("request_type") or run.get("use_case") or "health_check_endpoint")
        metrics = compute_validation_metrics(session_id=session_id) if session_id else {}
        segment = "startup" if use_case == "health_check_endpoint" else "growth"
        bucket = segments.setdefault(
            segment,
            {"segment": segment, "customers": 0, "retention_total": 0.0, "value_total": 0.0},
        )
        bucket["customers"] += 1
        bucket["retention_total"] += float(metrics.get("retention_rate") or 0)
        bucket["value_total"] += float(metrics.get("value_realization_score") or 0)

    segment_profiles: list[dict[str, Any]] = []
    for segment, stats in segments.items():
        count = stats["customers"] or 1
        segment_profiles.append(
            {
                "segment": segment,
                "customer_count": stats["customers"],
                "avg_retention": round(stats["retention_total"] / count, 3),
                "avg_value": round(stats["value_total"] / count, 3),
            }
        )

    strongest_use_cases = sorted(
        {str(run.get("request_type") or run.get("use_case") or "health_check_endpoint") for run in pilot_runs}
    )
    highest_retention = max(segment_profiles, key=lambda s: s.get("avg_retention", 0), default={})
    highest_value = max(segment_profiles, key=lambda s: s.get("avg_value", 0), default={})

    return {
        "report_id": "customer-strategy-report",
        "program_session_id": program_session_id,
        "ideal_customer_profile": highest_value.get("segment") or "startup",
        "strongest_use_cases": strongest_use_cases,
        "highest_retention_segment": highest_retention.get("segment"),
        "highest_value_segment": highest_value.get("segment"),
        "segment_profiles": segment_profiles,
        "usage_observation_count": len(observations),
        "composed_from_f1_f7_g2_g3_patterns": True,
        "customer_strategy_evaluated": bool(pilot_runs) or bool(observations),
        "read_only": True,
    }


def _outcome_scores(*, program_session_id: str) -> dict[str, float]:
    baselines = _g_baselines(program_session_id=program_session_id)
    g1 = baselines["g1"]
    g2 = baselines["g2"]
    g3 = baselines["g3"]
    g4 = baselines["g4"]
    growth = build_growth_path_report(program_session_id=program_session_id)
    top_path_score = float((growth.get("growth_paths") or [{}])[0].get("opportunity_score") or 0)

    return {
        "option_a_customer_growth": round(
            (
                float(g2.get("workflow_adoption_rate") or 0)
                + float(g3.get("expansion_score") or 0)
                + top_path_score
            )
            / 3,
            3,
        ),
        "option_b_product_depth": round(
            (
                float(g4.get("architecture_maturity_score") or 0)
                + float(g4.get("execution_maturity_score") or 0)
            )
            / 2,
            3,
        ),
        "option_c_ecosystem_expansion": round(
            (
                float(g4.get("operational_maturity_score") or 0)
                + float(g3.get("expansion_score") or 0)
            )
            / 2,
            3,
        ),
        "option_d_enterprise_expansion": round(
            (
                float(g1.get("trust_maturity_score") or 0)
                + float(g4.get("evidence_maturity_score") or 0)
                + float(g4.get("overall_platform_maturity_score") or 0)
            )
            / 3,
            3,
        ),
    }


def build_strategic_tradeoff_report(*, program_session_id: str) -> dict[str, Any]:
    outcomes = _outcome_scores(program_session_id=program_session_id)
    baselines = _g_baselines(program_session_id=program_session_id)
    g4 = baselines["g4"]
    execution_risk = round(1.0 - float(g4.get("execution_maturity_score") or 0), 3)
    confidence = round(
        (
            float(baselines["g1"].get("evidence_density_score") or 0)
            + float(g4.get("overall_platform_maturity_score") or 0)
        )
        / 2,
        3,
    )

    tradeoffs: list[dict[str, Any]] = []
    for category in STRATEGIC_OUTCOME_CATEGORIES:
        impact = outcomes.get(category, 0.0)
        effort = round(1.0 - impact * 0.6, 3)
        risk = execution_risk if category in {"option_c_ecosystem_expansion", "option_d_enterprise_expansion"} else round(execution_risk * 0.8, 3)
        tradeoffs.append(
            {
                "outcome_category": category,
                "effort": effort,
                "risk": risk,
                "impact": impact,
                "confidence": confidence,
                "advisory_only": True,
            }
        )

    return {
        "report_id": "strategic-tradeoff-report",
        "program_session_id": program_session_id,
        "tradeoffs": tradeoffs,
        "execution_risk_score": execution_risk,
        "confidence_score": confidence,
        "strategic_tradeoffs_analyzed": len(tradeoffs) == len(STRATEGIC_OUTCOME_CATEGORIES),
        "automatic_prioritization_performed": False,
        "read_only": True,
    }


def build_strategic_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    growth = build_growth_path_report(program_session_id=program_session_id)
    product = build_product_expansion_report(program_session_id=program_session_id)
    provider = build_provider_strategy_report(program_session_id=program_session_id)
    customer = build_customer_strategy_report(program_session_id=program_session_id)
    outcomes = _outcome_scores(program_session_id=program_session_id)

    growth_opportunities = [
        {"source": "growth_path", "path": path, "advisory_only": True}
        for path in growth.get("growth_paths") or []
        if float(path.get("opportunity_score") or 0) >= 0.3
    ]
    product_opportunities = [
        {"source": "product_expansion", "area": area, "advisory_only": True}
        for area in product.get("expansion_areas") or []
        if float(area.get("expansion_score") or 0) >= 0.3
    ]
    execution_opportunities = [
        {
            "source": "execution_maturity",
            "opportunity": "Increase ET certification reliability before scale-out",
            "advisory_only": True,
        }
    ]
    ecosystem_opportunities = [
        {"source": "provider_strategy", "provider": item, "advisory_only": True}
        for item in provider.get("provider_targets") or []
        if item.get("status") == "opportunity"
    ]

    ranked_outcomes = sorted(outcomes.items(), key=lambda item: item[1], reverse=True)
    if ranked_outcomes:
        growth_opportunities.append(
            {
                "source": "outcome_category",
                "leading_outcome": ranked_outcomes[0][0],
                "score": ranked_outcomes[0][1],
                "advisory_only": True,
            }
        )

    if customer.get("highest_value_segment"):
        growth_opportunities.append(
            {
                "source": "customer_strategy",
                "segment": customer.get("highest_value_segment"),
                "advisory_only": True,
            }
        )

    opportunities = growth_opportunities + product_opportunities + execution_opportunities + ecosystem_opportunities
    return {
        "registry_id": "strategic-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "growth_opportunities": growth_opportunities,
        "product_opportunities": product_opportunities,
        "execution_opportunities": execution_opportunities,
        "ecosystem_opportunities": ecosystem_opportunities,
        "budget_allocation_performed": False,
        "read_only": True,
    }


def compute_strategic_direction_metrics(*, program_session_id: str) -> dict[str, Any]:
    growth = build_growth_path_report(program_session_id=program_session_id)
    tradeoffs = build_strategic_tradeoff_report(program_session_id=program_session_id)
    opportunities = build_strategic_opportunity_registry(program_session_id=program_session_id)
    outcomes = _outcome_scores(program_session_id=program_session_id)

    path_scores = [float(p.get("opportunity_score") or 0) for p in growth.get("growth_paths") or []]
    opportunity_score = round(sum(path_scores) / max(len(path_scores), 1), 3)
    strategic_leverage_score = round(max(outcomes.values()) if outcomes else 0.0, 3)
    execution_risk_score = float(tradeoffs.get("execution_risk_score") or 0)
    confidence_score = float(tradeoffs.get("confidence_score") or 0)
    growth_potential_score = round(
        (opportunity_score + strategic_leverage_score + confidence_score) / 3,
        3,
    )

    return {
        "opportunity_score": opportunity_score,
        "strategic_leverage_score": strategic_leverage_score,
        "execution_risk_score": execution_risk_score,
        "confidence_score": confidence_score,
        "growth_potential_score": growth_potential_score,
        "leading_outcome_category": max(outcomes.items(), key=lambda item: item[1])[0] if outcomes else None,
        "open_opportunity_count": opportunities.get("opportunity_count"),
        "read_only": True,
    }

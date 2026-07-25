# SPDX-License-Identifier: Apache-2.0
"""FIX 326 — strategic planning intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_contract import (
    COMPARISON_MATRIX_DIMENSIONS,
    PRIVACY_REQUIREMENTS,
    RESOURCE_PLANNING_DIMENSIONS,
    SCENARIO_IMPACT_DIMENSIONS,
    STRATEGIC_OPPORTUNITY_FORECAST_TYPES,
    STRATEGIC_PLANNING_CORE_PRINCIPLE,
    STRATEGIC_PLAN_STATUSES,
    STRATEGIC_RISK_FORECAST_CATEGORIES,
    STRATEGIC_SCENARIO_TYPES,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_store import (
    classify_plan_status,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def build_strategic_planning_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    records = list(evidence.get("planning_review_records") or [])
    active: list[dict[str, Any]] = []
    proposed: list[dict[str, Any]] = []
    archived: list[dict[str, Any]] = []

    for record in records:
        kind = str(record.get("kind") or "")
        status = classify_plan_status(kind)
        row = {
            "plan_id": f"{kind}-{str(record.get('recorded_at') or 'unknown')}",
            "kind": kind,
            "content": record.get("content"),
            "status": status,
            "session_id": record.get("session_id"),
        }
        if status == "active":
            active.append(row)
        elif status == "archived":
            archived.append(row)
        else:
            proposed.append(row)

    plan_registry = _composed_section(evidence, "fix_325", "executive_recommendation_report")
    for rec in (plan_registry.get("recommendations") or [])[:3]:
        proposed.append(
            {
                "plan_id": f"proposed-{str(rec.get('title'))[:24]}",
                "kind": "generated_plan_candidate",
                "content": str(rec.get("title")),
                "status": "proposed",
                "source": "FIX 325",
            }
        )

    return {
        "active_plans": active[:12],
        "proposed_plans": proposed[:12],
        "archived_plans": archived[:12],
        "active_count": len(active),
        "proposed_count": len(proposed),
        "archived_count": len(archived),
        "plan_statuses": list(STRATEGIC_PLAN_STATUSES),
        "cross_tenant_planning_visibility_forbidden": True,
        "validated": bool(active or proposed or archived or plan_registry),
    }


def build_strategic_scenario_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    portfolio = _composed_section(evidence, "fix_324", "strategic_value_report")
    executive = _composed_section(evidence, "fix_325", "executive_decision_dashboard")
    business_value = float(portfolio.get("business_value_score") or 0.5)

    scenarios: list[dict[str, Any]] = []
    scenario_defs = {
        "conservative_growth": {
            "title": "Conservative growth",
            "growth_rate": 0.05,
            "investment_intensity": "low",
            "timeline": "long",
        },
        "balanced_growth": {
            "title": "Balanced growth",
            "growth_rate": 0.12,
            "investment_intensity": "medium",
            "timeline": "medium",
        },
        "aggressive_growth": {
            "title": "Aggressive growth",
            "growth_rate": 0.22,
            "investment_intensity": "high",
            "timeline": "short",
        },
        "efficiency_optimization": {
            "title": "Efficiency optimization",
            "growth_rate": 0.08,
            "investment_intensity": "low",
            "timeline": "medium",
        },
        "customer_expansion": {
            "title": "Customer expansion",
            "growth_rate": 0.15,
            "investment_intensity": "medium",
            "timeline": "medium",
        },
    }

    for scenario_type in STRATEGIC_SCENARIO_TYPES:
        definition = scenario_defs[scenario_type]
        scenarios.append(
            {
                "scenario_id": scenario_type,
                "scenario_type": scenario_type,
                "title": definition["title"],
                "baseline_value_score": business_value,
                "projected_value_score": round(business_value + definition["growth_rate"], 3),
                "investment_intensity": definition["investment_intensity"],
                "timeline": definition["timeline"],
                "recommendation_count": executive.get("recommendation_count", 0),
                "automatic_strategy_execution_forbidden": True,
            }
        )

    return {
        "scenarios": scenarios,
        "count": len(scenarios),
        "scenario_types": list(STRATEGIC_SCENARIO_TYPES),
        "validated": bool(scenarios),
    }


def build_scenario_impact_report(*, scenario_report: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    value = _composed_section(evidence, "fix_324", "strategic_value_report")
    resource = _composed_section(evidence, "fix_324", "resource_allocation_report")

    impacts: list[dict[str, Any]] = []
    for scenario in scenario_report.get("scenarios") or []:
        intensity = str(scenario.get("investment_intensity") or "medium")
        risk_multiplier = {"low": 0.8, "medium": 1.0, "high": 1.3}.get(intensity, 1.0)
        impacts.append(
            {
                "scenario_id": scenario.get("scenario_id"),
                "title": scenario.get("title"),
                "customer_impact": round(float(value.get("customer_value_score") or 0.5) * risk_multiplier, 3),
                "product_impact": round(float(value.get("strategic_value_score") or 0.5) * risk_multiplier, 3),
                "operational_impact": round(
                    len(portfolio_risk.get("operational_risk") or []) * 0.1 * risk_multiplier,
                    3,
                ),
                "commercial_impact": round(float(value.get("business_value_score") or 0.5) * risk_multiplier, 3),
                "support_load_delta": resource.get("support_effort_units", 0),
            }
        )

    return {
        "impacts": impacts,
        "count": len(impacts),
        "impact_dimensions": list(SCENARIO_IMPACT_DIMENSIONS),
        "validated": bool(impacts),
    }


def build_strategic_risk_forecast(*, evidence: dict[str, Any]) -> dict[str, Any]:
    launch_risks = _composed_section(evidence, "fix_309", "launch_risk_registry")
    launch_blockers = _composed_section(evidence, "fix_313", "launch_blocker_registry")
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    decision_risk = _composed_section(evidence, "fix_325", "decision_risk_report")

    operational = list(launch_blockers.get("blockers") or launch_blockers.get("items") or [])
    operational.extend(portfolio_risk.get("operational_risk") or [])
    operational.extend(decision_risk.get("operational_risk_signals") or [])

    commercial = list(portfolio_risk.get("commercial_risk") or [])
    commercial.extend(decision_risk.get("commercial_risk_signals") or [])

    adoption = list(portfolio_risk.get("customer_risk") or [])
    adoption.extend(launch_risks.get("risks") or launch_risks.get("items") or [])

    execution = [
        str(item.get("title") or item)
        for item in (decision_risk.get("highest_risk_decisions") or [])[:6]
    ]

    return {
        "sources": ["FIX 309", "FIX 313", "FIX 324", "FIX 325"],
        "operational_risks": operational[:8],
        "commercial_risks": commercial[:8],
        "adoption_risks": adoption[:8],
        "execution_risks": execution[:8],
        "risk_categories": list(STRATEGIC_RISK_FORECAST_CATEGORIES),
        "validated": bool(operational or commercial or adoption or execution),
    }


def build_strategic_opportunity_forecast(*, evidence: dict[str, Any]) -> dict[str, Any]:
    portfolio = _composed_section(evidence, "fix_324", "investment_opportunity_report")
    executive = _composed_section(evidence, "fix_325", "executive_opportunity_registry")
    opportunities = _composed_section(evidence, "fix_324", "portfolio_opportunity_registry")

    growth = [
        {"title": str(item.get("title")), "source": item.get("source", "FIX 324")}
        for item in (portfolio.get("high_value_opportunities") or [])[:6]
    ]
    expansion = [
        {"title": str(item.get("title")), "source_type": item.get("source_type", "strategic")}
        for item in (executive.get("opportunities") or [])
        if item.get("source_type") in {"growth", "strategic", "pmf"}
    ][:6]
    efficiency = [
        {"title": str(item.get("title")), "source": item.get("source", "FIX 324")}
        for item in (portfolio.get("underinvested_areas") or [])[:6]
    ]
    for opp in (opportunities.get("opportunities") or []):
        if opp.get("opportunity_type") == "efficiency" and len(efficiency) < 6:
            efficiency.append({"title": str(opp.get("title")), "source_type": "efficiency"})

    return {
        "growth_opportunities": growth,
        "expansion_opportunities": expansion or growth[:3],
        "efficiency_opportunities": efficiency,
        "forecast_types": list(STRATEGIC_OPPORTUNITY_FORECAST_TYPES),
        "validated": bool(growth or expansion or efficiency),
    }


def build_resource_planning_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    resource = _composed_section(evidence, "fix_324", "resource_allocation_report")
    tradeoffs = _composed_section(evidence, "fix_325", "tradeoff_analysis_report")
    recommendations = _composed_section(evidence, "fix_325", "executive_recommendation_report")

    engineering = int(resource.get("engineering_effort_units") or 3)
    operational = int(resource.get("operational_effort_units") or 2)
    support = int(resource.get("support_effort_units") or 1)
    investment = len(recommendations.get("recommendations") or []) + len(tradeoffs.get("tradeoffs") or [])

    return {
        "engineering_allocation": engineering,
        "operational_allocation": operational,
        "support_allocation": support,
        "investment_allocation": min(investment, 12),
        "allocation_summary": {
            "engineering": engineering,
            "operational": operational,
            "support": support,
            "investment": min(investment, 12),
        },
        "planning_dimensions": list(RESOURCE_PLANNING_DIMENSIONS),
        "validated": True,
    }


def build_strategic_plan_registry(
    *,
    scenario_report: dict[str, Any],
    impact_report: dict[str, Any],
    risk_forecast: dict[str, Any],
    opportunity_forecast: dict[str, Any],
) -> dict[str, Any]:
    impact_by_id = {str(row.get("scenario_id")): row for row in impact_report.get("impacts") or []}
    plans: list[dict[str, Any]] = []

    for scenario in scenario_report.get("scenarios") or []:
        scenario_id = str(scenario.get("scenario_id"))
        impact = impact_by_id.get(scenario_id) or {}
        risk_count = len(risk_forecast.get("operational_risks") or []) + len(
            risk_forecast.get("execution_risks") or []
        )
        opp_count = (
            len(opportunity_forecast.get("growth_opportunities") or [])
            + len(opportunity_forecast.get("efficiency_opportunities") or [])
        )
        intensity = str(scenario.get("investment_intensity") or "medium")
        confidence = {"low": 0.82, "medium": 0.74, "high": 0.66}.get(intensity, 0.7)

        plans.append(
            {
                "plan_id": f"plan-{scenario_id}",
                "scenario": scenario.get("title"),
                "scenario_type": scenario_id,
                "objectives": [
                    f"Reach projected value score {scenario.get('projected_value_score', 0)}",
                    f"Execute {scenario.get('title')} over {scenario.get('timeline', 'medium')} timeline",
                ],
                "assumptions": [
                    f"Investment intensity remains {intensity}",
                    "Tenant isolation and human plan approval preserved",
                ],
                "risks": (risk_forecast.get("operational_risks") or [])[:3],
                "opportunities": (opportunity_forecast.get("growth_opportunities") or [])[:3],
                "confidence": confidence,
                "customer_impact": impact.get("customer_impact", 0),
                "commercial_impact": impact.get("commercial_impact", 0),
                "risk_signal_count": risk_count,
                "opportunity_signal_count": opp_count,
                "automatic_strategy_execution_forbidden": True,
            }
        )

    return {
        "plans": plans,
        "count": len(plans),
        "core_principle": STRATEGIC_PLANNING_CORE_PRINCIPLE,
    }


def _comparison_score(plan: dict[str, Any]) -> float:
    value = float(plan.get("commercial_impact") or plan.get("projected_value_score") or 0.5)
    confidence = float(plan.get("confidence") or 0.5)
    risk_penalty = min(1.0, float(plan.get("risk_signal_count") or 0) * 0.08)
    timeline_bonus = {"short": 0.15, "medium": 0.08, "long": 0.0}.get(str(plan.get("timeline") or "medium"), 0.0)
    effort_penalty = {"low": 0.0, "medium": 0.1, "high": 0.2}.get(str(plan.get("investment_intensity") or "medium"), 0.1)
    return round(value * 3.0 + confidence * 2.0 - risk_penalty - effort_penalty + timeline_bonus, 3)


def build_strategic_comparison_matrix(
    *,
    plan_registry: dict[str, Any],
    scenario_report: dict[str, Any],
    risk_forecast: dict[str, Any],
) -> dict[str, Any]:
    scenario_by_id = {str(s.get("scenario_id")): s for s in scenario_report.get("scenarios") or []}
    comparisons: list[dict[str, Any]] = []

    for plan in plan_registry.get("plans") or []:
        scenario = scenario_by_id.get(str(plan.get("scenario_type"))) or {}
        comparisons.append(
            {
                "plan_id": plan.get("plan_id"),
                "scenario": plan.get("scenario"),
                "value": float(plan.get("commercial_impact") or scenario.get("projected_value_score") or 0.5),
                "effort": scenario.get("investment_intensity", "medium"),
                "risk": round(min(1.0, float(plan.get("risk_signal_count") or 0) * 0.12 + 0.15), 3),
                "confidence": float(plan.get("confidence") or 0.5),
                "timeline": scenario.get("timeline", "medium"),
                "comparison_score": _comparison_score({**plan, **scenario}),
                "automatic_strategy_execution_forbidden": True,
            }
        )

    comparisons.sort(key=lambda row: row.get("comparison_score", 0), reverse=True)
    strongest = comparisons[0] if comparisons else {}

    return {
        "comparisons": comparisons,
        "strongest_plan": strongest,
        "comparison_dimensions": list(COMPARISON_MATRIX_DIMENSIONS),
        "risk_forecast_present": bool(risk_forecast),
        "automatic_strategy_execution_forbidden": True,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
    }


def build_strategic_planning_dashboard(
    *,
    planning_registry: dict[str, Any],
    scenario_report: dict[str, Any],
    impact_report: dict[str, Any],
    risk_forecast: dict[str, Any],
    opportunity_forecast: dict[str, Any],
    resource_report: dict[str, Any],
    plan_registry: dict[str, Any],
    comparison_matrix: dict[str, Any],
) -> dict[str, Any]:
    strongest = comparison_matrix.get("strongest_plan") or {}
    return {
        "active_plan_count": planning_registry.get("active_count", 0),
        "proposed_plan_count": planning_registry.get("proposed_count", 0),
        "scenario_count": scenario_report.get("count", 0),
        "impact_scenario_count": impact_report.get("count", 0),
        "operational_risk_count": len(risk_forecast.get("operational_risks") or []),
        "growth_opportunity_count": len(opportunity_forecast.get("growth_opportunities") or []),
        "engineering_allocation": resource_report.get("engineering_allocation", 0),
        "generated_plan_count": plan_registry.get("count", 0),
        "strongest_plan": strongest.get("scenario"),
        "strongest_plan_score": strongest.get("comparison_score", 0),
        "core_principle": STRATEGIC_PLANNING_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_strategy_execution_forbidden": True,
    }

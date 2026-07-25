# SPDX-License-Identifier: Apache-2.0
"""FIX 324 — strategic portfolio intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evidence import (
    _section_block,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_contract import (
    PORTFOLIO_ASSET_TYPES,
    PORTFOLIO_OPPORTUNITY_TYPES,
    PORTFOLIO_RISK_CATEGORIES,
    PRIVACY_REQUIREMENTS,
    STRATEGIC_CORE_PRINCIPLE,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def build_portfolio_asset_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    tenant = evidence.get("fix_300") or {}
    business = evidence.get("fix_290") or {}
    tenant_dashboard = _section_block(tenant, "tenant_dashboard")
    products = _composed_section(evidence, "fix_290", "product_portfolio_registry")
    projects = _composed_section(evidence, "fix_290", "project_portfolio_registry")
    portfolio_baseline = _composed_section(evidence, "fix_316", "portfolio_baseline")

    assets: list[dict[str, Any]] = [
        {
            "asset_id": "product-mission-control",
            "asset_type": "product",
            "name": "Mission Control",
            "tenant_scoped": True,
        },
        {
            "asset_id": "program-customer-intelligence",
            "asset_type": "program",
            "name": "Customer Intelligence Program (FIX 318-323)",
            "tenant_scoped": True,
        },
    ]
    for idx in range(int(tenant_dashboard.get("project_count") or 0)):
        assets.append(
            {
                "asset_id": f"project-{idx + 1}",
                "asset_type": "project",
                "name": f"Tenant project {idx + 1}",
                "tenant_scoped": True,
            }
        )
    for item in (products.get("products") or products.get("items") or [])[:4]:
        assets.append(
            {
                "asset_id": f"product-{str(item)[:24]}",
                "asset_type": "product",
                "name": str(item),
                "tenant_scoped": True,
            }
        )
    for item in (projects.get("projects") or projects.get("items") or [])[:4]:
        assets.append(
            {
                "asset_id": f"initiative-{str(item)[:24]}",
                "asset_type": "initiative",
                "name": str(item),
                "tenant_scoped": True,
            }
        )
    for item in (portfolio_baseline.get("repositories") or portfolio_baseline.get("items") or [])[:4]:
        assets.append(
            {
                "asset_id": f"repository-{str(item)[:24]}",
                "asset_type": "repository",
                "name": str(item),
                "tenant_scoped": True,
            }
        )
    assets.append(
        {
            "asset_id": "investment-value-realization",
            "asset_type": "strategic_investment",
            "name": "Value realization intelligence (FIX 323)",
            "tenant_scoped": True,
        }
    )

    return {
        "assets": assets[:20],
        "count": len(assets[:20]),
        "asset_types": list(PORTFOLIO_ASSET_TYPES),
        "cross_tenant_portfolio_visibility_forbidden": True,
        "validated": bool(assets),
    }


def build_strategic_value_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    pmf = _composed_section(evidence, "fix_322", "pmf_scorecard")
    value = _composed_section(evidence, "fix_323", "value_realization_scorecard")
    pmf_dashboard = _composed_section(evidence, "fix_322", "product_market_fit_dashboard")
    value_dashboard = _composed_section(evidence, "fix_323", "customer_value_dashboard")

    strategic_value = float(pmf.get("overall_score") or 0)
    customer_value = float(value.get("overall_score") or 0)
    business_value = round((strategic_value + customer_value) / 2.0, 3)

    return {
        "sources": ["FIX 322", "FIX 323"],
        "strategic_value_score": strategic_value,
        "customer_value_score": customer_value,
        "business_value_score": business_value,
        "pmf_level": pmf.get("overall_level", "UNKNOWN"),
        "value_realization_level": value.get("overall_level", "UNKNOWN"),
        "pmf_opportunity_count": pmf_dashboard.get("pmf_opportunity_count", 0),
        "value_opportunity_count": value_dashboard.get("value_opportunity_count", 0),
        "validated": bool(pmf or value),
    }


def build_investment_opportunity_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    pmf_ops = _composed_section(evidence, "fix_322", "pmf_opportunity_registry")
    value_ops = _composed_section(evidence, "fix_323", "value_opportunity_registry")
    business_ops = _composed_section(evidence, "fix_290", "business_opportunity_portfolio")

    high_value: list[dict[str, Any]] = []
    underinvested: list[dict[str, Any]] = []
    emerging: list[dict[str, Any]] = []

    for opp in (pmf_ops.get("opportunities") or [])[:6]:
        row = {"title": opp.get("title"), "source": "FIX 322", "category": opp.get("category")}
        if opp.get("impact") == "high":
            high_value.append(row)
        else:
            emerging.append(row)

    for opp in (value_ops.get("opportunities") or [])[:6]:
        row = {"title": opp.get("title"), "source": "FIX 323", "category": opp.get("opportunity_type")}
        if opp.get("impact") == "high":
            high_value.append(row)
        else:
            underinvested.append(row)

    for opp in (business_ops.get("opportunities") or business_ops.get("items") or [])[:4]:
        title = str(opp.get("title") or opp) if isinstance(opp, dict) else str(opp)
        emerging.append({"title": title, "source": "FIX 290", "category": "strategic"})

    return {
        "high_value_opportunities": high_value[:8],
        "underinvested_areas": underinvested[:8],
        "emerging_opportunities": emerging[:8],
        "validated": bool(high_value or underinvested or emerging),
    }


def build_portfolio_risk_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    launch = evidence.get("fix_309") or {}
    ops = evidence.get("fix_313") or {}
    baseline = evidence.get("fix_316") or {}

    launch_risks = _composed_section(evidence, "fix_309", "launch_risk_registry")
    launch_blockers = _composed_section(evidence, "fix_313", "launch_blocker_registry")
    platform_health = _composed_section(evidence, "fix_316", "platform_health_baseline")
    customer_health = _composed_section(evidence, "fix_316", "customer_health_baseline")
    commercial = _composed_section(evidence, "fix_316", "commercial_baseline")
    incident = _composed_section(evidence, "fix_316", "incident_baseline")

    operational_risk = list(launch_blockers.get("blockers") or launch_blockers.get("items") or [])
    operational_risk.extend(incident.get("active_incidents") or incident.get("incidents") or [])
    product_risk = list(launch_risks.get("risks") or launch_risks.get("items") or [])
    customer_risk = [f"customer_health:{customer_health.get('status', 'unknown')}"]
    commercial_risk = [f"commercial_status:{commercial.get('status', 'unknown')}"]

    if platform_health.get("status") in {"DEGRADED", "AT_RISK"}:
        operational_risk.append(f"platform_health:{platform_health.get('status')}")

    return {
        "sources": ["FIX 309", "FIX 313", "FIX 316"],
        "operational_risk": operational_risk[:8],
        "product_risk": product_risk[:8],
        "customer_risk": customer_risk[:8],
        "commercial_risk": commercial_risk[:8],
        "risk_categories": list(PORTFOLIO_RISK_CATEGORIES),
        "launch_assessment_present": bool(launch),
        "operations_center_present": bool(ops),
        "baseline_present": bool(baseline),
        "validated": bool(operational_risk or product_risk or customer_risk or commercial_risk),
    }


def build_resource_allocation_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    team = _composed_section(evidence, "fix_290", "team_operating_registry")
    operations = _composed_section(evidence, "fix_290", "business_operations_registry")
    support = _composed_section(evidence, "fix_316", "operations_baseline_registry")
    value_gap = _composed_section(evidence, "fix_323", "value_gap_report")

    engineering_effort = int(team.get("engineering_capacity") or team.get("headcount") or 3)
    operational_effort = int(operations.get("operational_load") or operations.get("active_workstreams") or 2)
    support_effort = int(support.get("support_load") or support.get("open_items") or 1)
    gap_pressure = len(value_gap.get("gaps") or [])

    return {
        "engineering_effort_units": engineering_effort,
        "operational_effort_units": operational_effort,
        "support_effort_units": support_effort,
        "value_gap_pressure": gap_pressure,
        "allocation_summary": {
            "engineering": engineering_effort,
            "operational": operational_effort,
            "support": support_effort,
        },
        "validated": True,
    }


def build_strategic_alignment_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    alignment = _composed_section(evidence, "fix_290", "strategic_alignment_graph")
    goals = _composed_section(evidence, "fix_290", "business_goal_registry")
    projects = _composed_section(evidence, "fix_290", "project_portfolio_registry")
    products = _composed_section(evidence, "fix_290", "product_portfolio_registry")
    tenant = evidence.get("fix_300") or {}
    tenant_dashboard = _section_block(tenant, "tenant_dashboard")

    goal_items = list(goals.get("objectives") or goals.get("goals") or [])
    initiative_items = list(projects.get("projects") or projects.get("items") or [])
    product_items = list(products.get("products") or products.get("items") or ["Mission Control"])
    project_count = int(tenant_dashboard.get("project_count") or len(initiative_items))

    aligned_pairs: list[dict[str, Any]] = []
    for goal in goal_items[:4]:
        aligned_pairs.append({"goal": str(goal), "aligned_initiatives": initiative_items[:3]})
    if not aligned_pairs and goal_items == []:
        aligned_pairs.append(
            {
                "goal": "Deliver tenant-scoped customer and platform value",
                "aligned_initiatives": initiative_items[:3] or ["Mission Control activation"],
            }
        )

    return {
        "sources": ["FIX 290"],
        "goals": goal_items[:8] or ["Deliver tenant-scoped platform value"],
        "initiatives": initiative_items[:8],
        "products": product_items[:8],
        "projects": project_count,
        "alignment_nodes": alignment.get("node_count", len(aligned_pairs)),
        "aligned_pairs": aligned_pairs,
        "validated": bool(alignment or goals or projects or products or tenant),
    }


def build_portfolio_opportunity_registry(
    *,
    investment_report: dict[str, Any],
    strategic_value: dict[str, Any],
    alignment_report: dict[str, Any],
    risk_report: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    for item in investment_report.get("high_value_opportunities") or []:
        opportunities.append(
            {
                "opportunity_id": f"growth-{str(item.get('title'))[:24]}",
                "title": str(item.get("title")),
                "opportunity_type": "growth",
                "value": strategic_value.get("business_value_score", 0.5),
                "effort": "medium",
                "confidence": 0.82,
                "strategic_alignment": "high" if alignment_report.get("aligned_pairs") else "medium",
                "automatic_strategy_execution_forbidden": True,
            }
        )

    for item in investment_report.get("underinvested_areas") or []:
        opportunities.append(
            {
                "opportunity_id": f"efficiency-{str(item.get('title'))[:24]}",
                "title": str(item.get("title")),
                "opportunity_type": "efficiency",
                "value": strategic_value.get("customer_value_score", 0.5),
                "effort": "low",
                "confidence": 0.75,
                "strategic_alignment": "medium",
                "automatic_strategy_execution_forbidden": True,
            }
        )

    for item in investment_report.get("emerging_opportunities") or []:
        opportunities.append(
            {
                "opportunity_id": f"strategic-{str(item.get('title'))[:24]}",
                "title": str(item.get("title")),
                "opportunity_type": "strategic",
                "value": strategic_value.get("strategic_value_score", 0.5),
                "effort": "high",
                "confidence": 0.7,
                "strategic_alignment": "high",
                "automatic_strategy_execution_forbidden": True,
            }
        )

    if risk_report.get("operational_risk"):
        opportunities.append(
            {
                "opportunity_id": "risk-mitigation-operational",
                "title": "Mitigate operational portfolio risk before acceleration",
                "opportunity_type": "strategic",
                "value": 0.9,
                "effort": "high",
                "confidence": 0.88,
                "strategic_alignment": "high",
                "automatic_strategy_execution_forbidden": True,
            }
        )

    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "opportunity_types": list(PORTFOLIO_OPPORTUNITY_TYPES),
        "core_principle": STRATEGIC_CORE_PRINCIPLE,
    }


def _priority_score(opportunity: dict[str, Any], *, risk_weight: float = 0.0) -> float:
    value = float(opportunity.get("value") or 0.5)
    confidence = float(opportunity.get("confidence") or 0.5)
    effort_penalty = {"low": 0.0, "medium": 0.3, "high": 0.6}.get(str(opportunity.get("effort") or "medium"), 0.3)
    alignment_bonus = 0.2 if opportunity.get("strategic_alignment") == "high" else 0.0
    return round(value * 3.0 + confidence * 2.0 - effort_penalty + alignment_bonus + risk_weight, 3)


def build_strategic_priority_matrix(
    *,
    registry: dict[str, Any],
    investment_report: dict[str, Any],
    risk_report: dict[str, Any],
) -> dict[str, Any]:
    ranked = [{**opp, "priority_score": _priority_score(opp)} for opp in registry.get("opportunities") or []]
    ranked.sort(key=lambda row: row["priority_score"], reverse=True)

    highest_value = sorted(ranked, key=lambda row: float(row.get("value") or 0), reverse=True)[:5]
    highest_risk = [
        {**opp, "priority_score": _priority_score(opp, risk_weight=0.5), "risk_signal": "elevated"}
        for opp in ranked[:3]
    ]
    if risk_report.get("operational_risk") or risk_report.get("product_risk"):
        highest_risk.insert(
            0,
            {
                "opportunity_id": "portfolio-risk-attention",
                "title": "Address portfolio risk before highest-ROI acceleration",
                "priority_score": 9.0,
                "risk_signal": "portfolio_risk",
                "automatic_strategy_execution_forbidden": True,
            },
        )

    highest_roi = ranked[:5]

    return {
        "ranked_opportunities": ranked[:12],
        "highest_value_opportunities": highest_value,
        "highest_risk_opportunities": highest_risk[:5],
        "highest_roi_opportunities": highest_roi,
        "automatic_strategy_execution_forbidden": True,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
    }


def build_strategic_portfolio_dashboard(
    *,
    asset_registry: dict[str, Any],
    strategic_value: dict[str, Any],
    investment_report: dict[str, Any],
    risk_report: dict[str, Any],
    resource_report: dict[str, Any],
    alignment_report: dict[str, Any],
    opportunity_registry: dict[str, Any],
    priority_matrix: dict[str, Any],
) -> dict[str, Any]:
    return {
        "portfolio_asset_count": asset_registry.get("count", 0),
        "strategic_value_score": strategic_value.get("strategic_value_score", 0),
        "customer_value_score": strategic_value.get("customer_value_score", 0),
        "business_value_score": strategic_value.get("business_value_score", 0),
        "high_value_opportunity_count": len(investment_report.get("high_value_opportunities") or []),
        "underinvested_area_count": len(investment_report.get("underinvested_areas") or []),
        "operational_risk_count": len(risk_report.get("operational_risk") or []),
        "customer_risk_count": len(risk_report.get("customer_risk") or []),
        "engineering_effort_units": resource_report.get("engineering_effort_units", 0),
        "alignment_node_count": alignment_report.get("alignment_nodes", 0),
        "portfolio_opportunity_count": opportunity_registry.get("count", 0),
        "top_priority": (priority_matrix.get("ranked_opportunities") or [{}])[0],
        "core_principle": STRATEGIC_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_strategy_execution_forbidden": True,
    }

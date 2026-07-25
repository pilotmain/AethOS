# SPDX-License-Identifier: Apache-2.0
"""FIX 329 — enterprise operating review intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_contract import (
    ENTERPRISE_OPERATING_CORE_PRINCIPLE,
    ENTERPRISE_RISK_CATEGORIES,
    EXECUTIVE_ACTION_TYPES,
    EXECUTIVE_OPERATING_LEVELS,
    EXECUTIVE_OPERATING_SCORECARD_DIMENSIONS,
    ORGANIZATIONAL_HEALTH_DIMENSIONS,
    PRIVACY_REQUIREMENTS,
    PROGRAM_HEALTH_DIMENSIONS,
    STRATEGIC_HEALTH_DIMENSIONS,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def _level_from_score(score: float) -> str:
    if score >= 0.85:
        return "HIGH_PERFORMANCE"
    if score >= 0.7:
        return "HEALTHY"
    if score >= 0.55:
        return "STABLE"
    if score >= 0.4:
        return "NEEDS_ATTENTION"
    return "CRITICAL"


def build_executive_operating_snapshot(*, evidence: dict[str, Any]) -> dict[str, Any]:
    portfolio = _composed_section(evidence, "fix_324", "strategic_portfolio_dashboard")
    executive = _composed_section(evidence, "fix_325", "executive_decision_dashboard")
    planning = _composed_section(evidence, "fix_326", "strategic_planning_dashboard")
    programs = _composed_section(evidence, "fix_327", "enterprise_program_dashboard")
    organization = _composed_section(evidence, "fix_328", "organizational_effectiveness_dashboard")

    major_risks: list[str] = []
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    major_risks.extend((portfolio_risk.get("operational_risk") or [])[:2])
    major_risks.extend((programs.get("leadership_intervention_programs") or [])[:2])
    if organization.get("coordination_failure_count"):
        major_risks.append("Coordination failures detected across programs")

    major_opportunities: list[str] = []
    investment = _composed_section(evidence, "fix_324", "investment_opportunity_report")
    for item in (investment.get("high_value_opportunities") or [])[:3]:
        major_opportunities.append(str(item.get("title") or item))
    planning_ops = _composed_section(evidence, "fix_326", "strategic_opportunity_forecast")
    for item in (planning_ops.get("growth_opportunities") or [])[:2]:
        major_opportunities.append(str(item.get("title") or item))

    major_decisions: list[str] = []
    recommendations = _composed_section(evidence, "fix_325", "executive_recommendation_report")
    for rec in (recommendations.get("recommendations") or [])[:4]:
        major_decisions.append(
            f"{rec.get('recommendation_level', 'REVIEW')}: {rec.get('title')}"
        )

    return {
        "sources": ["FIX 324", "FIX 325", "FIX 326", "FIX 327", "FIX 328"],
        "current_state": {
            "business_value_score": portfolio.get("business_value_score", 0),
            "pending_decisions": executive.get("pending_decision_count", 0),
            "scenario_count": planning.get("scenario_count", 0),
            "program_count": programs.get("program_count", 0),
            "effectiveness_level": organization.get("overall_effectiveness_level", "STABLE"),
        },
        "major_risks": major_risks[:8],
        "major_opportunities": major_opportunities[:8],
        "major_decisions": major_decisions[:8],
        "validated": bool(portfolio or executive or planning or programs or organization),
    }


def build_strategic_health_review(*, evidence: dict[str, Any]) -> dict[str, Any]:
    portfolio_value = _composed_section(evidence, "fix_324", "strategic_value_report")
    alignment = _composed_section(evidence, "fix_324", "strategic_alignment_report")
    planning = _composed_section(evidence, "fix_326", "strategic_planning_dashboard")
    comparison = _composed_section(evidence, "fix_326", "strategic_comparison_matrix")
    strongest = comparison.get("strongest_plan") or {}

    strategy_health = float(portfolio_value.get("business_value_score") or 0.5)
    planning_health = min(1.0, int(planning.get("generated_plan_count") or 0) / 5.0 + 0.4)
    alignment_health = min(1.0, float(alignment.get("alignment_nodes") or 0) / 10.0 + 0.45)
    if strongest:
        planning_health = max(planning_health, float(strongest.get("comparison_score") or 0) / 10.0)

    dimensions = {
        "strategy_health": round(strategy_health, 3),
        "planning_health": round(planning_health, 3),
        "alignment_health": round(alignment_health, 3),
    }

    return {
        "sources": ["FIX 324", "FIX 326"],
        "dimensions": dimensions,
        "dimension_labels": list(STRATEGIC_HEALTH_DIMENSIONS),
        "overall_score": round(sum(dimensions.values()) / len(dimensions), 3),
        "validated": bool(portfolio_value or alignment or planning),
    }


def build_program_health_review(*, evidence: dict[str, Any]) -> dict[str, Any]:
    health = _composed_section(evidence, "fix_327", "program_health_report")
    dashboard = _composed_section(evidence, "fix_327", "enterprise_program_dashboard")
    counts = health.get("health_status_counts") or {}

    return {
        "sources": ["FIX 327"],
        "programs": health.get("programs") or [],
        "health_status_counts": {k: counts.get(k, 0) for k in PROGRAM_HEALTH_DIMENSIONS},
        "healthy_count": counts.get("healthy", dashboard.get("healthy_program_count", 0)),
        "blocked_count": counts.get("blocked", dashboard.get("blocked_program_count", 0)),
        "at_risk_count": counts.get("at_risk", dashboard.get("at_risk_program_count", 0)),
        "dimensions": list(PROGRAM_HEALTH_DIMENSIONS),
        "validated": bool(health or dashboard),
    }


def build_organizational_health_review(*, evidence: dict[str, Any]) -> dict[str, Any]:
    scorecard = _composed_section(evidence, "fix_328", "organizational_effectiveness_scorecard")
    dashboard = _composed_section(evidence, "fix_328", "organizational_effectiveness_dashboard")
    dimension_scores = scorecard.get("dimension_scores") or {}

    dimensions = {
        "governance": float(dimension_scores.get("governance") or 0.5),
        "coordination": float(dimension_scores.get("coordination") or 0.5),
        "capacity": float(dimension_scores.get("capacity") or 0.5),
        "decision_velocity": float(dimension_scores.get("decision_velocity") or 0.5),
    }

    return {
        "sources": ["FIX 328"],
        "dimensions": dimensions,
        "dimension_labels": list(ORGANIZATIONAL_HEALTH_DIMENSIONS),
        "overall_level": dashboard.get("overall_effectiveness_level", scorecard.get("overall_level", "STABLE")),
        "overall_score": scorecard.get("overall_score", 0),
        "friction_signal_count": dashboard.get("friction_signal_count", 0),
        "validated": bool(scorecard or dashboard),
    }


def build_enterprise_risk_review(*, evidence: dict[str, Any]) -> dict[str, Any]:
    launch_risks = _composed_section(evidence, "fix_309", "launch_risk_registry")
    launch_blockers = _composed_section(evidence, "fix_313", "launch_blocker_registry")
    baseline = _composed_section(evidence, "fix_316", "incident_baseline")
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    planning_risk = _composed_section(evidence, "fix_326", "strategic_risk_forecast")
    program_risk = _composed_section(evidence, "fix_327", "program_risk_report")
    org_risk = _composed_section(evidence, "fix_328", "organizational_risk_report")

    strategic = list(planning_risk.get("execution_risks") or [])
    strategic.extend(portfolio_risk.get("product_risk") or [])
    program = [str(r.get("title") or r.get("risk_signal") or r) for r in (program_risk.get("program_risks") or [])]
    organizational = list(org_risk.get("governance_risk") or []) + list(org_risk.get("dependency_risk") or [])
    operational = list(launch_blockers.get("blockers") or launch_blockers.get("items") or [])
    operational.extend(baseline.get("active_incidents") or baseline.get("incidents") or [])
    operational.extend(launch_risks.get("risks") or launch_risks.get("items") or [])

    return {
        "sources": ["FIX 309", "FIX 313", "FIX 316", "FIX 327", "FIX 328"],
        "strategic_risks": strategic[:8],
        "program_risks": program[:8],
        "organizational_risks": organizational[:8],
        "operational_risks": operational[:8],
        "risk_categories": list(ENTERPRISE_RISK_CATEGORIES),
        "validated": bool(strategic or program or organizational or operational),
    }


def build_enterprise_opportunity_review(*, evidence: dict[str, Any]) -> dict[str, Any]:
    portfolio_ops = _composed_section(evidence, "fix_324", "portfolio_opportunity_registry")
    executive_ops = _composed_section(evidence, "fix_325", "executive_opportunity_registry")
    planning_ops = _composed_section(evidence, "fix_326", "strategic_opportunity_forecast")
    program_ops = _composed_section(evidence, "fix_327", "program_opportunity_registry")
    org_ops = _composed_section(evidence, "fix_328", "organizational_opportunity_registry")

    opportunities: list[dict[str, Any]] = []
    for source, registry in (
        ("FIX 324", portfolio_ops),
        ("FIX 325", executive_ops),
        ("FIX 327", program_ops),
        ("FIX 328", org_ops),
    ):
        for opp in (registry.get("opportunities") or [])[:4]:
            opportunities.append(
                {
                    "title": str(opp.get("title")),
                    "source": source,
                    "opportunity_type": opp.get("opportunity_type") or opp.get("source_type"),
                }
            )

    for item in (planning_ops.get("growth_opportunities") or [])[:3]:
        opportunities.append({"title": str(item.get("title")), "source": "FIX 326", "opportunity_type": "growth"})
    for item in (planning_ops.get("efficiency_opportunities") or [])[:2]:
        opportunities.append(
            {"title": str(item.get("title")), "source": "FIX 326", "opportunity_type": "efficiency"}
        )

    return {
        "sources": ["FIX 324", "FIX 325", "FIX 326", "FIX 327", "FIX 328"],
        "opportunities": opportunities[:20],
        "count": len(opportunities[:20]),
        "validated": bool(opportunities),
    }


def build_executive_action_registry(
    *,
    snapshot: dict[str, Any],
    risk_review: dict[str, Any],
    opportunity_review: dict[str, Any],
    program_review: dict[str, Any],
    organization_review: dict[str, Any],
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []

    for risk in (snapshot.get("major_risks") or [])[:3]:
        actions.append(
            {
                "action_id": f"investigate-{str(risk)[:20]}",
                "title": f"Investigate risk: {risk}",
                "action_type": "investigate",
                "advisory_only": True,
                "automatic_decision_execution_forbidden": True,
            }
        )

    if int(program_review.get("blocked_count") or 0) >= 1:
        actions.append(
            {
                "action_id": "review-blocked-programs",
                "title": "Review blocked programs before acceleration",
                "action_type": "review",
                "advisory_only": True,
                "automatic_decision_execution_forbidden": True,
            }
        )

    for opp in (opportunity_review.get("opportunities") or [])[:3]:
        actions.append(
            {
                "action_id": f"prioritize-{str(opp.get('title'))[:20]}",
                "title": f"Prioritize opportunity review: {opp.get('title')}",
                "action_type": "prioritize",
                "advisory_only": True,
                "automatic_decision_execution_forbidden": True,
            }
        )

    if organization_review.get("friction_signal_count", 0) >= 3:
        actions.append(
            {
                "action_id": "monitor-governance-friction",
                "title": "Monitor governance friction and approval bottlenecks",
                "action_type": "monitor",
                "advisory_only": True,
                "automatic_decision_execution_forbidden": True,
            }
        )

    for category in ENTERPRISE_RISK_CATEGORIES:
        key = f"{category}_risks"
        if risk_review.get(key):
            actions.append(
                {
                    "action_id": f"monitor-{category}-risk",
                    "title": f"Monitor {category.replace('_', ' ')} risk signals",
                    "action_type": "monitor",
                    "advisory_only": True,
                    "automatic_decision_execution_forbidden": True,
                }
            )

    return {
        "actions": actions[:16],
        "count": len(actions[:16]),
        "action_types": list(EXECUTIVE_ACTION_TYPES),
        "core_principle": ENTERPRISE_OPERATING_CORE_PRINCIPLE,
    }


def build_executive_operating_scorecard(
    *,
    strategic_review: dict[str, Any],
    program_review: dict[str, Any],
    organization_review: dict[str, Any],
    risk_review: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    strategy_score = float(strategic_review.get("overall_score") or 0.5)
    program_score = min(
        1.0,
        float(program_review.get("healthy_count") or 0) / max(int(program_review.get("healthy_count") or 0) + int(program_review.get("at_risk_count") or 0) + 1, 1)
        + 0.35,
    )
    organization_score = float(organization_review.get("overall_score") or 0.5)
    risk_penalty = min(
        0.45,
        len(risk_review.get("strategic_risks") or [])
        + len(risk_review.get("program_risks") or [])
        + len(risk_review.get("organizational_risks") or [])
        + len(risk_review.get("operational_risks") or []),
    ) * 0.04
    risk_score = max(0.0, 1.0 - risk_penalty)
    execution_score = max(
        0.0,
        min(
            1.0,
            float(snapshot.get("current_state", {}).get("business_value_score") or 0.5)
            - int(program_review.get("blocked_count") or 0) * 0.08,
        ),
    )

    dimension_scores = {
        "strategy": round(strategy_score, 3),
        "programs": round(program_score, 3),
        "organization": round(organization_score, 3),
        "risk": round(risk_score, 3),
        "execution": round(execution_score, 3),
    }
    dimension_levels = {dim: _level_from_score(score) for dim, score in dimension_scores.items()}
    overall_score = round(sum(dimension_scores.values()) / len(dimension_scores), 3)

    return {
        "dimensions": list(EXECUTIVE_OPERATING_SCORECARD_DIMENSIONS),
        "dimension_scores": dimension_scores,
        "dimension_levels": dimension_levels,
        "overall_score": overall_score,
        "overall_level": _level_from_score(overall_score),
        "levels": list(EXECUTIVE_OPERATING_LEVELS),
        "automatic_decision_execution_forbidden": True,
        "validated": True,
    }


def build_enterprise_operating_dashboard(
    *,
    snapshot: dict[str, Any],
    strategic_review: dict[str, Any],
    program_review: dict[str, Any],
    organization_review: dict[str, Any],
    risk_review: dict[str, Any],
    opportunity_review: dict[str, Any],
    action_registry: dict[str, Any],
    scorecard: dict[str, Any],
) -> dict[str, Any]:
    attention_items = [
        action for action in (action_registry.get("actions") or []) if action.get("action_type") in {"review", "investigate"}
    ]
    return {
        "overall_operating_level": scorecard.get("overall_level", "STABLE"),
        "overall_operating_score": scorecard.get("overall_score", 0),
        "business_value_score": snapshot.get("current_state", {}).get("business_value_score", 0),
        "major_risk_count": len(snapshot.get("major_risks") or []),
        "major_opportunity_count": len(snapshot.get("major_opportunities") or []),
        "major_decision_count": len(snapshot.get("major_decisions") or []),
        "healthy_program_count": program_review.get("healthy_count", 0),
        "blocked_program_count": program_review.get("blocked_count", 0),
        "organization_effectiveness_level": organization_review.get("overall_level", "STABLE"),
        "strategic_health_score": strategic_review.get("overall_score", 0),
        "opportunity_count": opportunity_review.get("count", 0),
        "executive_action_count": action_registry.get("count", 0),
        "executive_attention_items": attention_items[:5],
        "core_principle": ENTERPRISE_OPERATING_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_decision_execution_forbidden": True,
    }

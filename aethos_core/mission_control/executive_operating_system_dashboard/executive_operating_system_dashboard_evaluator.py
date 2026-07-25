# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
    EXECUTIVE_DASHBOARD_CORE_PRINCIPLE,
    PRIVACY_REQUIREMENTS,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def _board_field(evidence: dict[str, Any], fix_key: str, field: str, default: Any = None) -> Any:
    payload = evidence.get(fix_key) or {}
    return payload.get(field, default)


def build_executive_summary_panel(*, evidence: dict[str, Any]) -> dict[str, Any]:
    operating_review = _composed_section(evidence, "fix_329", "enterprise_operating_dashboard")
    launch_readiness = _composed_section(evidence, "fix_309", "launch_readiness_dashboard")
    launch_freeze = _composed_section(evidence, "fix_314", "launch_readiness_freeze_dashboard")
    launch_decision = _composed_section(evidence, "fix_315", "launch_decision_dashboard")
    trust_freeze = _composed_section(evidence, "fix_314", "launch_trust_baseline_summary")
    trust_package = _composed_section(evidence, "fix_315", "launch_trust_evidence_summary")
    baseline = _composed_section(evidence, "fix_316", "post_launch_operations_dashboard")
    launch_ops = _composed_section(evidence, "fix_313", "launch_operations_dashboard")

    major_alerts: list[str] = []
    for item in operating_review.get("executive_attention_items") or []:
        major_alerts.append(str(item.get("title") or item))
    for blocker in (_composed_section(evidence, "fix_313", "launch_blocker_registry").get("blockers") or [])[:3]:
        major_alerts.append(str(blocker.get("detail") or blocker))
    for incident in (_composed_section(evidence, "fix_316", "incident_baseline").get("active_incidents") or [])[:3]:
        major_alerts.append(str(incident))

    return {
        "sources": ["FIX 309", "FIX 314", "FIX 315", "FIX 316", "FIX 329"],
        "overall_health": {
            "operating_level": operating_review.get("overall_operating_level", "STABLE"),
            "operating_score": operating_review.get("overall_operating_score", 0),
            "business_value_score": operating_review.get("business_value_score", 0),
        },
        "launch_state": {
            "overall_launch_status": _board_field(evidence, "fix_309", "overall_launch_status", "UNKNOWN"),
            "readiness_score": launch_readiness.get("readiness_score", 0),
            "freeze_status": launch_freeze.get("freeze_status", "UNKNOWN"),
            "decision_recommendation": launch_decision.get("recommendation", "REVIEW"),
            "operations_status": launch_ops.get("operations_status", "MONITORING"),
        },
        "trust_state": {
            "baseline_count": trust_freeze.get("baseline_count", trust_package.get("trust_baseline_count", 0)),
            "proven_items": len(trust_freeze.get("proven_items") or []),
            "unproven_items": len(trust_freeze.get("unproven_items") or []),
            "trust_summary": (trust_package.get("trust_summary") or trust_freeze.get("summary") or "Review trust baselines"),
        },
        "readiness_state": {
            "platform_health": baseline.get("platform_health_status", "UNKNOWN"),
            "customer_health": baseline.get("customer_health_status", "UNKNOWN"),
            "governance_health": baseline.get("governance_health_status", "UNKNOWN"),
            "readiness_level": launch_readiness.get("overall_readiness_level", "REVIEW"),
        },
        "major_alerts": major_alerts[:10],
        "validated": bool(operating_review or launch_readiness or launch_freeze),
    }


def build_strategy_panel(*, evidence: dict[str, Any]) -> dict[str, Any]:
    portfolio = _composed_section(evidence, "fix_324", "strategic_portfolio_dashboard")
    priorities = _composed_section(evidence, "fix_324", "strategic_priority_registry")
    executive = _composed_section(evidence, "fix_325", "executive_decision_dashboard")
    planning = _composed_section(evidence, "fix_326", "strategic_planning_dashboard")
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    planning_risk = _composed_section(evidence, "fix_326", "strategic_risk_forecast")
    portfolio_ops = _composed_section(evidence, "fix_324", "portfolio_opportunity_registry")
    executive_ops = _composed_section(evidence, "fix_325", "executive_opportunity_registry")
    planning_ops = _composed_section(evidence, "fix_326", "strategic_opportunity_forecast")

    top_priorities = list(priorities.get("priorities") or portfolio.get("top_priorities") or [])[:6]
    if not top_priorities:
        top_priorities = [
            rec.get("title")
            for rec in (_composed_section(evidence, "fix_325", "executive_recommendation_report").get("recommendations") or [])[:4]
            if rec.get("title")
        ]

    strategic_risks = list(portfolio_risk.get("product_risk") or [])
    strategic_risks.extend(planning_risk.get("execution_risks") or [])

    opportunities: list[dict[str, Any]] = []
    for registry, source in (
        (portfolio_ops, "FIX 324"),
        (executive_ops, "FIX 325"),
    ):
        for opp in (registry.get("opportunities") or [])[:3]:
            opportunities.append({"title": str(opp.get("title")), "source": source})
    for item in (planning_ops.get("growth_opportunities") or [])[:3]:
        opportunities.append({"title": str(item.get("title")), "source": "FIX 326"})

    return {
        "sources": ["FIX 324", "FIX 325", "FIX 326"],
        "top_priorities": top_priorities[:8],
        "strategic_plans": {
            "scenario_count": planning.get("scenario_count", 0),
            "generated_plan_count": planning.get("generated_plan_count", 0),
            "strongest_plan": (_composed_section(evidence, "fix_326", "strategic_comparison_matrix").get("strongest_plan") or {}),
        },
        "strategic_risks": strategic_risks[:8],
        "opportunities": opportunities[:10],
        "pending_decisions": executive.get("pending_decision_count", 0),
        "validated": bool(portfolio or executive or planning),
    }


def build_program_panel(*, evidence: dict[str, Any]) -> dict[str, Any]:
    dashboard = _composed_section(evidence, "fix_327", "enterprise_program_dashboard")
    health = _composed_section(evidence, "fix_327", "program_health_report")
    dependencies = _composed_section(evidence, "fix_327", "program_dependency_report")

    blocked_programs = [
        prog for prog in (health.get("programs") or []) if prog.get("health_status") == "blocked"
    ]
    if not blocked_programs:
        blocked_programs = [{"name": name} for name in (dashboard.get("blocked_programs") or [])[:6]]

    return {
        "sources": ["FIX 327"],
        "active_programs": health.get("programs") or [],
        "active_program_count": dashboard.get("program_count", len(health.get("programs") or [])),
        "blocked_programs": blocked_programs[:8],
        "blocked_program_count": dashboard.get("blocked_program_count", len(blocked_programs)),
        "critical_dependencies": (dependencies.get("dependencies") or dependencies.get("critical_dependencies") or [])[:8],
        "dependency_blockers": (dependencies.get("blockers") or [])[:8],
        "validated": bool(dashboard or health or dependencies),
    }


def build_organization_panel(*, evidence: dict[str, Any]) -> dict[str, Any]:
    dashboard = _composed_section(evidence, "fix_328", "organizational_effectiveness_dashboard")
    friction = _composed_section(evidence, "fix_328", "governance_friction_report")
    capacity = _composed_section(evidence, "fix_328", "organizational_capacity_report")
    coordination = _composed_section(evidence, "fix_328", "coordination_intelligence_report")

    return {
        "sources": ["FIX 328"],
        "effectiveness": {
            "overall_level": dashboard.get("overall_effectiveness_level", "STABLE"),
            "overall_score": (_composed_section(evidence, "fix_328", "organizational_effectiveness_scorecard").get("overall_score", 0)),
            "friction_signal_count": dashboard.get("friction_signal_count", 0),
        },
        "governance_friction": {
            "friction_signals": friction.get("friction_signals") or friction.get("signals") or [],
            "approval_delay_count": friction.get("approval_delay_count", 0),
            "bottleneck_count": friction.get("bottleneck_count", 0),
        },
        "capacity": {
            "capacity_level": capacity.get("capacity_level", "STABLE"),
            "initiative_load": capacity.get("initiative_load", 0),
            "review_burden": capacity.get("review_burden", 0),
        },
        "coordination": {
            "coordination_failures": coordination.get("coordination_failures") or [],
            "dependency_gaps": coordination.get("dependency_gaps") or [],
            "cross_program_gaps": coordination.get("cross_program_gaps") or [],
        },
        "validated": bool(dashboard or friction or capacity or coordination),
    }


def build_customer_panel(*, evidence: dict[str, Any]) -> dict[str, Any]:
    growth = _composed_section(evidence, "fix_320", "growth_adoption_dashboard")
    retention = _composed_section(evidence, "fix_320", "retention_intelligence_report")
    analytics = _composed_section(evidence, "fix_318", "analytics_dashboard")
    feedback = _composed_section(evidence, "fix_319", "customer_feedback_dashboard")
    journey = _composed_section(evidence, "fix_321", "customer_journey_dashboard")
    pmf = _composed_section(evidence, "fix_322", "product_market_fit_dashboard")
    value = _composed_section(evidence, "fix_323", "customer_value_dashboard")
    support = _composed_section(evidence, "fix_310", "customer_support_success_dashboard")
    beta = _composed_section(evidence, "fix_312", "beta_program_dashboard")

    return {
        "sources": ["FIX 310", "FIX 312", "FIX 318", "FIX 319", "FIX 320", "FIX 321", "FIX 322", "FIX 323"],
        "adoption": {
            "activated_customers": growth.get("activated_customers", analytics.get("activated_customers", 0)),
            "adoption_rate_percent": analytics.get("onboarding_completion_rate_percent", 0),
            "current_journey_stage": journey.get("current_stage", "unknown"),
        },
        "retention": {
            "retained_customers": retention.get("retained_customers", growth.get("retained_customers", 0)),
            "disengaged_customers": retention.get("disengaged_customers", growth.get("disengaged_customers", 0)),
            "retention_rate_percent": retention.get("retention_rate_percent", 0),
        },
        "pmf": {
            "fit_level": pmf.get("fit_level", "UNKNOWN"),
            "fit_score": pmf.get("overall_fit_score", 0),
            "signal_count": pmf.get("signal_count", 0),
        },
        "value_realization": {
            "realization_level": value.get("realization_level", "UNKNOWN"),
            "realization_score": value.get("overall_realization_score", 0),
            "outcome_count": value.get("outcome_count", 0),
        },
        "customer_health": {
            "health_level": support.get("overall_health_level", "STABLE"),
            "at_risk_customers": support.get("at_risk_customer_count", 0),
            "beta_participants": beta.get("participant_count", 0),
            "positive_sentiment": feedback.get("positive_sentiment_count", 0),
            "negative_sentiment": feedback.get("negative_sentiment_count", 0),
        },
        "validated": bool(growth or journey or pmf or value or support),
    }


def build_operations_panel(*, evidence: dict[str, Any]) -> dict[str, Any]:
    deploy = _composed_section(evidence, "fix_210", "deploy_readiness_assessment")
    monitoring = _composed_section(evidence, "fix_220", "monitoring_health_assessment")
    incident = _composed_section(evidence, "fix_220", "incident_detection")
    rollback = _composed_section(evidence, "fix_230", "rollback_assessment")
    recovery = evidence.get("fix_230", {}).get("sections", {}).get("recovery_timeline") or []
    launch_ops = _composed_section(evidence, "fix_313", "launch_operations_dashboard")
    baseline = _composed_section(evidence, "fix_316", "post_launch_operations_dashboard")
    merge = _composed_section(evidence, "fix_200", "merge_readiness_assessment")

    operational_risks: list[str] = []
    for risk in (_composed_section(evidence, "fix_313", "launch_risk_dashboard").get("risks") or [])[:4]:
        operational_risks.append(str(risk.get("detail") or risk))
    if baseline.get("platform_health_status") == "DEGRADED":
        operational_risks.append("Platform health degraded")

    return {
        "sources": ["FIX 200", "FIX 210", "FIX 220", "FIX 230", "FIX 313", "FIX 316"],
        "deploy_health": {
            "readiness_level": deploy.get("readiness_level", merge.get("readiness_level", "REVIEW")),
            "deploy_recommendation": (_composed_section(evidence, "fix_210", "deploy_recommendation").get("recommendation", "REVIEW")),
            "monitoring_health": monitoring.get("health_status", "UNKNOWN"),
        },
        "incidents": {
            "classification": incident.get("classification", "UNKNOWN"),
            "active_incidents": _composed_section(evidence, "fix_316", "incident_baseline").get("active_incidents") or [],
            "incident_count": baseline.get("incident_count", len(incident.get("signals") or [])),
        },
        "recovery_status": {
            "rollback_recommendation": (_composed_section(evidence, "fix_230", "rollback_recommendation").get("recommendation", "MONITOR")),
            "rollback_risk_level": rollback.get("risk_level", "UNKNOWN"),
            "recovery_timeline_events": len(recovery),
            "recovery_stage": rollback.get("recovery_stage", "observation"),
        },
        "operational_risks": operational_risks[:8],
        "operations_status": launch_ops.get("operations_status", baseline.get("operations_status", "MONITORING")),
        "validated": bool(deploy or monitoring or baseline or launch_ops),
    }


def build_commercial_panel(*, evidence: dict[str, Any]) -> dict[str, Any]:
    billing = _composed_section(evidence, "fix_305", "billing_dashboard")
    plans = _composed_section(evidence, "fix_305", "plan_registry")
    subscriptions = _composed_section(evidence, "fix_305", "subscription_registry")
    billing_readiness = _composed_section(evidence, "fix_305", "billing_readiness_report")
    payment = _composed_section(evidence, "fix_308", "payment_readiness_dashboard")
    commercial_governance = _composed_section(evidence, "fix_308", "commercial_governance_report")

    plan_distribution = plans.get("plans") or plans.get("items") or billing.get("plan_distribution") or []

    commercial_risks: list[str] = []
    for blocker in (billing_readiness.get("blockers") or billing_readiness.get("gaps") or [])[:4]:
        commercial_risks.append(str(blocker.get("detail") or blocker))
    for risk in (commercial_governance.get("commercial_risks") or [])[:4]:
        commercial_risks.append(str(risk.get("detail") or risk))

    return {
        "sources": ["FIX 305", "FIX 308"],
        "plan_distribution": plan_distribution[:8],
        "subscription_health": {
            "active_subscriptions": len(subscriptions.get("active_subscriptions") or subscriptions.get("items") or []),
            "subscription_status": billing.get("subscription_health_status", "REVIEW"),
            "usage_limit_alerts": len((_composed_section(evidence, "fix_305", "usage_limit_report").get("alerts") or [])),
        },
        "monetization_readiness": {
            "payment_readiness_level": payment.get("readiness_level", "REVIEW"),
            "billing_readiness_level": billing_readiness.get("readiness_level", "REVIEW"),
            "monetization_score": payment.get("monetization_score", 0),
        },
        "commercial_risks": commercial_risks[:8],
        "validated": bool(billing or payment or billing_readiness),
    }


def build_portfolio_panel(*, evidence: dict[str, Any]) -> dict[str, Any]:
    engineering = _composed_section(evidence, "fix_260", "portfolio_engineering_dashboard")
    portfolio = _composed_section(evidence, "fix_324", "strategic_portfolio_dashboard")
    investment = _composed_section(evidence, "fix_324", "investment_opportunity_report")
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    initiative_registry = _composed_section(evidence, "fix_324", "portfolio_initiative_registry")

    portfolio_summary = engineering.get("portfolio_summary") or {}
    products = portfolio_summary.get("repositories") or engineering.get("repository_health_rows") or []
    initiatives = initiative_registry.get("initiatives") or portfolio.get("active_initiatives") or []

    return {
        "sources": ["FIX 260", "FIX 324"],
        "products": products[:8],
        "initiatives": initiatives[:8],
        "investment_opportunities": (investment.get("high_value_opportunities") or investment.get("opportunities") or [])[:8],
        "portfolio_risks": {
            "product_risk": portfolio_risk.get("product_risk") or [],
            "operational_risk": portfolio_risk.get("operational_risk") or [],
            "engineering_risk_count": len(engineering.get("repository_health_rows") or []),
        },
        "business_value_score": portfolio.get("business_value_score", 0),
        "validated": bool(engineering or portfolio or investment),
    }


def build_executive_operating_system_dashboard(
    *,
    summary_panel: dict[str, Any],
    strategy_panel: dict[str, Any],
    program_panel: dict[str, Any],
    organization_panel: dict[str, Any],
    customer_panel: dict[str, Any],
    operations_panel: dict[str, Any],
    commercial_panel: dict[str, Any],
    portfolio_panel: dict[str, Any],
) -> dict[str, Any]:
    attention_items: list[dict[str, Any]] = []

    if int(program_panel.get("blocked_program_count") or 0) >= 1:
        attention_items.append(
            {
                "title": "Review blocked programs",
                "panel": "program_panel",
                "advisory_only": True,
            }
        )
    if summary_panel.get("major_alerts"):
        for alert in summary_panel.get("major_alerts")[:3]:
            attention_items.append({"title": str(alert), "panel": "executive_summary_panel", "advisory_only": True})
    if operations_panel.get("operational_risks"):
        attention_items.append(
            {
                "title": f"Operational risk signals: {len(operations_panel.get('operational_risks') or [])}",
                "panel": "operations_panel",
                "advisory_only": True,
            }
        )
    if int(customer_panel.get("customer_health", {}).get("at_risk_customers") or 0) >= 1:
        attention_items.append(
            {
                "title": "Review at-risk customers",
                "panel": "customer_panel",
                "advisory_only": True,
            }
        )
    if commercial_panel.get("commercial_risks"):
        attention_items.append(
            {
                "title": f"Commercial readiness gaps: {len(commercial_panel.get('commercial_risks') or [])}",
                "panel": "commercial_panel",
                "advisory_only": True,
            }
        )

    return {
        "overall_operating_level": summary_panel.get("overall_health", {}).get("operating_level", "STABLE"),
        "overall_operating_score": summary_panel.get("overall_health", {}).get("operating_score", 0),
        "launch_status": summary_panel.get("launch_state", {}).get("overall_launch_status", "UNKNOWN"),
        "customer_health_level": customer_panel.get("customer_health", {}).get("health_level", "STABLE"),
        "program_blocked_count": program_panel.get("blocked_program_count", 0),
        "organization_effectiveness_level": organization_panel.get("effectiveness", {}).get("overall_level", "STABLE"),
        "operations_status": operations_panel.get("operations_status", "MONITORING"),
        "pmf_fit_level": customer_panel.get("pmf", {}).get("fit_level", "UNKNOWN"),
        "business_value_score": portfolio_panel.get("business_value_score", 0),
        "executive_attention_items": attention_items[:8],
        "panel_count": 8,
        "core_principle": EXECUTIVE_DASHBOARD_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_execution_forbidden": True,
        "automatic_decision_forbidden": True,
    }

# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — growth & adoption intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_contract import (
    GROWTH_CORE_PRINCIPLE,
    GROWTH_OPPORTUNITY_TYPES,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evidence import (
    _section_block,
)


def _analytics_section(evidence: dict[str, Any], section: str) -> dict[str, Any]:
    fix318 = evidence.get("fix_318") or {}
    sections = fix318.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def _feedback_section(evidence: dict[str, Any], section: str) -> dict[str, Any]:
    fix319 = evidence.get("fix_319") or {}
    sections = fix319.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def build_adoption_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    tenant = evidence.get("fix_300") or {}
    onboarding = evidence.get("fix_301") or {}
    provider = evidence.get("fix_303") or {}
    channel = evidence.get("fix_304") or {}
    capability = _analytics_section(evidence, "capability_usage_report")

    tenant_dashboard = _section_block(tenant, "tenant_dashboard")
    progress = _section_block(onboarding, "onboarding_progress_registry")
    provider_dashboard = _section_block(provider, "provider_connection_dashboard")
    channel_dashboard = _section_block(channel, "channel_integration_dashboard")

    activated = int(progress.get("completed_count") or progress.get("completed_steps_count") or 0)
    if not activated:
        activated = int(tenant_dashboard.get("organization_count") or 0)

    adopted_capabilities = list(capability.get("capabilities_used") or [])[:12]
    provider_reports = (provider.get("sections") or {}).get("provider_connection_reports") or []
    adopted_providers = [
        str(row.get("provider"))
        for row in provider_reports
        if isinstance(row, dict) and int(row.get("connected_count") or row.get("connection_count") or 0) > 0
    ]
    if not adopted_providers and provider_dashboard.get("connected_provider_count"):
        adopted_providers = ["github"]

    adopted_channels = list(channel_dashboard.get("connected_channels") or channel_dashboard.get("channels") or [])
    if not adopted_channels:
        channel_registry = _section_block(channel, "channel_registry")
        adopted_channels = list(channel_registry.get("channels") or channel_registry.get("items") or [])[:8]

    return {
        "activated_customers": activated,
        "adopted_capabilities": adopted_capabilities,
        "adopted_providers": adopted_providers,
        "adopted_channels": adopted_channels,
        "tenant_scoped": True,
        "cross_tenant_aggregation_forbidden": True,
        "validated": bool(activated or adopted_capabilities or adopted_providers or adopted_channels),
    }


def build_adoption_analytics_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    onboarding_analytics = _analytics_section(evidence, "onboarding_analytics_report")
    provider_analytics = _analytics_section(evidence, "provider_analytics_report")
    capability_analytics = _analytics_section(evidence, "capability_usage_report")
    adoption_registry = build_adoption_registry(evidence=evidence)

    started = int(onboarding_analytics.get("users_started_onboarding") or 1)
    completed = int(onboarding_analytics.get("users_completed_onboarding") or 0)
    adoption_rate = round((completed / started) * 100, 1) if started else 0.0

    provider_count = int(provider_analytics.get("connected_provider_count") or len(adoption_registry["adopted_providers"]))
    capability_count = len(capability_analytics.get("capabilities_used") or adoption_registry["adopted_capabilities"])
    velocity_score = round((adoption_rate / 100.0) + (provider_count * 0.2) + (capability_count * 0.1), 2)

    return {
        "sources": ["FIX 318"],
        "adoption_rate_percent": adoption_rate,
        "adoption_velocity_score": velocity_score,
        "adoption_completion_percent": adoption_rate,
        "onboarding_completion_rate_percent": onboarding_analytics.get("average_completion_rate_percent", adoption_rate),
        "provider_adoption_count": provider_count,
        "capability_adoption_count": capability_count,
        "drop_off_points": list(onboarding_analytics.get("drop_off_points") or [])[:8],
        "validated": bool(onboarding_analytics or provider_analytics),
    }


def build_retention_intelligence_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    customer_success = _analytics_section(evidence, "customer_success_analytics_report")
    journey = _analytics_section(evidence, "user_journey_report")
    billing = evidence.get("fix_305") or {}
    subscriptions = _section_block(billing, "subscription_registry")

    retained = int(customer_success.get("healthy_customers") or 0)
    disengaged = int(customer_success.get("at_risk_customers") or 0)
    active_subscriptions = len(subscriptions.get("active_subscriptions") or subscriptions.get("items") or [])

    retention_stages = (journey.get("stages") or {}).get("retention") or {}
    cohorts = [
        {
            "cohort": "activated",
            "count": (journey.get("stages") or {}).get("activation", {}).get("onboarding_completed", 0),
        },
        {
            "cohort": "retained",
            "count": retained or retention_stages.get("retained_subscriptions", active_subscriptions),
        },
        {
            "cohort": "at_risk",
            "count": disengaged,
        },
    ]

    trend = customer_success.get("engagement_trends") or customer_success.get("engagement_trend") or "stable"

    return {
        "retained_customers": retained or active_subscriptions,
        "disengaged_customers": disengaged,
        "retention_cohorts": cohorts,
        "retention_trend": trend,
        "active_subscriptions": active_subscriptions,
        "validated": bool(customer_success or journey or billing),
    }


def build_expansion_intelligence_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    tenant = evidence.get("fix_300") or {}
    provider = evidence.get("fix_303") or {}
    channel = evidence.get("fix_304") or {}
    billing = evidence.get("fix_305") or {}
    payment = evidence.get("fix_308") or {}
    journey = _analytics_section(evidence, "user_journey_report")

    tenant_dashboard = _section_block(tenant, "tenant_dashboard")
    usage = _section_block(billing, "usage_registry")
    upgrade_paths = _section_block(payment, "upgrade_path_registry")
    expansion_stage = (journey.get("stages") or {}).get("expansion") or {}

    provider_reports = (provider.get("sections") or {}).get("provider_connection_reports") or []
    provider_expansion = [
        str(row.get("provider"))
        for row in provider_reports
        if isinstance(row, dict) and str(row.get("readiness") or "") in {"ready", "connected"}
    ]

    channel_dashboard = _section_block(channel, "channel_integration_dashboard")
    channel_expansion = list(channel_dashboard.get("connected_channels") or channel_dashboard.get("channels") or [])

    return {
        "workspace_growth": int(tenant_dashboard.get("workspace_count") or 0),
        "project_growth": int(tenant_dashboard.get("project_count") or 0),
        "provider_expansion": provider_expansion[:8],
        "channel_expansion": channel_expansion[:8],
        "plan_expansion": list(upgrade_paths.get("paths") or upgrade_paths.get("items") or [])[:8],
        "upgrade_candidates": list(usage.get("expansion_candidates") or expansion_stage.get("upgrade_candidates") or [])[
            :8
        ],
        "beta_participants": expansion_stage.get("beta_participants", 0),
        "validated": bool(tenant or provider or billing),
    }


def build_success_pattern_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    journey = _analytics_section(evidence, "user_journey_report")
    onboarding = _analytics_section(evidence, "onboarding_analytics_report")
    provider = _analytics_section(evidence, "provider_analytics_report")
    feedback_sentiment = _feedback_section(evidence, "feedback_sentiment_report")
    feedback_classification = _feedback_section(evidence, "feedback_classification_report")

    behaviors = list(journey.get("success_predictors") or [])
    positive_feedback = int((feedback_sentiment.get("counts_by_sentiment") or {}).get("positive", 0))
    if positive_feedback:
        behaviors.append("positive_customer_feedback")

    onboarding_paths = []
    if onboarding.get("users_completed_onboarding"):
        onboarding_paths.append("completed_onboarding")
    if not onboarding.get("drop_off_points"):
        onboarding_paths.append("low_drop_off_onboarding_path")

    provider_success = []
    most_connected = provider.get("most_connected_provider")
    if most_connected:
        provider_success.append(f"{most_connected}_connection_linked_to_success")

    positive_classifications = (feedback_classification.get("counts_by_classification") or {}).get(
        "positive_feedback", 0
    )

    return {
        "sources": ["FIX 318", "FIX 319"],
        "behaviors_linked_to_success": behaviors[:10],
        "onboarding_paths_linked_to_retention": onboarding_paths,
        "provider_usage_linked_to_success": provider_success,
        "positive_feedback_signals": positive_classifications,
        "validated": bool(behaviors or onboarding_paths or provider_success),
    }


def build_churn_risk_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    retention = build_retention_intelligence_report(evidence=evidence)
    adoption = build_adoption_analytics_report(evidence=evidence)
    feedback_sentiment = _feedback_section(evidence, "feedback_sentiment_report")
    support = evidence.get("fix_310") or {}
    risk_registry = _section_block(support, "customer_risk_registry")
    support_requests = _section_block(support, "support_request_registry")

    disengagement_patterns: list[str] = []
    if retention.get("disengaged_customers"):
        disengagement_patterns.append("at_risk_customer_status")
    if retention.get("retention_trend") in {"declining", "falling", "down"}:
        disengagement_patterns.append("declining_engagement_trend")

    adoption_failures: list[str] = []
    for point in adoption.get("drop_off_points") or []:
        adoption_failures.append(f"onboarding_drop_off:{point}")
    if adoption.get("adoption_rate_percent", 100) < 50:
        adoption_failures.append("low_adoption_rate")

    negative_sentiment = int((feedback_sentiment.get("counts_by_sentiment") or {}).get("negative", 0))
    feedback_deterioration: list[str] = []
    if negative_sentiment:
        feedback_deterioration.append(f"negative_feedback_count:{negative_sentiment}")

    support_escalations = list(support_requests.get("requests") or support_requests.get("items") or [])[:6]
    escalation_signals = [
        str(row.get("summary") or row.get("detail") or row)
        for row in support_escalations
        if isinstance(row, dict) or row
    ]

    risk_score = (
        len(disengagement_patterns) * 2
        + len(adoption_failures)
        + negative_sentiment
        + int(risk_registry.get("at_risk_count") or retention.get("disengaged_customers") or 0)
    )

    return {
        "disengagement_patterns": disengagement_patterns,
        "adoption_failures": adoption_failures[:8],
        "feedback_deterioration": feedback_deterioration,
        "support_escalation_signals": escalation_signals[:8],
        "at_risk_count": risk_registry.get("at_risk_count", retention.get("disengaged_customers", 0)),
        "churn_risk_score": risk_score,
        "validated": bool(disengagement_patterns or adoption_failures or feedback_deterioration or escalation_signals),
    }


def build_growth_opportunity_registry(
    *,
    adoption_report: dict[str, Any],
    retention_report: dict[str, Any],
    expansion_report: dict[str, Any],
    churn_report: dict[str, Any],
    success_report: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    if adoption_report.get("adoption_rate_percent", 100) < 70:
        opportunities.append(
            {
                "opportunity_id": "improve-adoption-rate",
                "title": f"Raise adoption rate from {adoption_report.get('adoption_rate_percent')}%",
                "opportunity_type": "adoption",
                "impact": "high",
                "confidence": 0.85,
                "effort": "medium",
                "automatic_growth_execution_forbidden": True,
            }
        )

    for point in adoption_report.get("drop_off_points") or []:
        opportunities.append(
            {
                "opportunity_id": f"adoption-drop-off-{str(point)[:24]}",
                "title": f"Reduce onboarding drop-off at {point}",
                "opportunity_type": "adoption",
                "impact": "high",
                "confidence": 0.8,
                "effort": "medium",
                "automatic_growth_execution_forbidden": True,
            }
        )

    if retention_report.get("disengaged_customers"):
        opportunities.append(
            {
                "opportunity_id": "retain-at-risk-customers",
                "title": f"Address {retention_report.get('disengaged_customers')} disengaged customers",
                "opportunity_type": "retention",
                "impact": "high",
                "confidence": 0.82,
                "effort": "high",
                "automatic_growth_execution_forbidden": True,
            }
        )

    for candidate in expansion_report.get("upgrade_candidates") or []:
        opportunities.append(
            {
                "opportunity_id": f"expansion-{str(candidate)[:24]}",
                "title": f"Expansion opportunity: {candidate}",
                "opportunity_type": "expansion",
                "impact": "medium",
                "confidence": 0.75,
                "effort": "low",
                "automatic_growth_execution_forbidden": True,
            }
        )

    for plan in expansion_report.get("plan_expansion") or []:
        opportunities.append(
            {
                "opportunity_id": f"plan-expansion-{str(plan)[:24]}",
                "title": f"Plan expansion path: {plan}",
                "opportunity_type": "expansion",
                "impact": "medium",
                "confidence": 0.78,
                "effort": "medium",
                "automatic_growth_execution_forbidden": True,
            }
        )

    if churn_report.get("churn_risk_score", 0) >= 2:
        opportunities.append(
            {
                "opportunity_id": "reduce-churn-risk",
                "title": "Mitigate churn risk signals before disengagement accelerates",
                "opportunity_type": "retention",
                "impact": "high",
                "confidence": 0.88,
                "effort": "high",
                "automatic_growth_execution_forbidden": True,
            }
        )

    for behavior in success_report.get("behaviors_linked_to_success") or []:
        opportunities.append(
            {
                "opportunity_id": f"amplify-success-{str(behavior)[:24]}",
                "title": f"Amplify success behavior: {behavior}",
                "opportunity_type": "adoption",
                "impact": "medium",
                "confidence": 0.7,
                "effort": "low",
                "automatic_growth_execution_forbidden": True,
            }
        )

    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "opportunity_types": list(GROWTH_OPPORTUNITY_TYPES),
        "core_principle": GROWTH_CORE_PRINCIPLE,
    }


def _roi_score(*, impact: str, confidence: float, effort: str, opportunity_type: str) -> float:
    impact_scores = {"high": 3.0, "medium": 2.0, "low": 1.0}
    effort_penalty = {"low": 0.0, "medium": 0.5, "high": 1.0}
    type_bonus = {"adoption": 0.3, "retention": 0.5, "expansion": 0.4}.get(opportunity_type, 0.0)
    return round(
        impact_scores.get(impact, 2.0) * 2.0 + confidence * 2.0 - effort_penalty.get(effort, 0.5) + type_bonus,
        3,
    )


def build_growth_priority_matrix(*, registry: dict[str, Any]) -> dict[str, Any]:
    ranked: list[dict[str, Any]] = []
    adoption_roi: list[dict[str, Any]] = []
    retention_roi: list[dict[str, Any]] = []
    expansion_roi: list[dict[str, Any]] = []

    for opp in registry.get("opportunities") or []:
        score = _roi_score(
            impact=str(opp.get("impact") or "medium"),
            confidence=float(opp.get("confidence") or 0.5),
            effort=str(opp.get("effort") or "medium"),
            opportunity_type=str(opp.get("opportunity_type") or "adoption"),
        )
        row = {**opp, "roi_score": score}
        ranked.append(row)
        bucket = str(opp.get("opportunity_type") or "")
        if bucket == "adoption":
            adoption_roi.append(row)
        elif bucket == "retention":
            retention_roi.append(row)
        elif bucket == "expansion":
            expansion_roi.append(row)

    ranked.sort(key=lambda row: row["roi_score"], reverse=True)
    adoption_roi.sort(key=lambda row: row["roi_score"], reverse=True)
    retention_roi.sort(key=lambda row: row["roi_score"], reverse=True)
    expansion_roi.sort(key=lambda row: row["roi_score"], reverse=True)

    return {
        "ranked_opportunities": ranked[:12],
        "highest_adoption_roi": adoption_roi[:5],
        "highest_retention_roi": retention_roi[:5],
        "highest_expansion_roi": expansion_roi[:5],
        "automatic_growth_execution_forbidden": True,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
    }

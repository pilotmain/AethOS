# SPDX-License-Identifier: Apache-2.0
"""FIX 322 — product-market fit intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_contract import (
    PMF_CORE_PRINCIPLE,
    PMF_FIT_LEVELS,
    PMF_SCORECARD_DIMENSIONS,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evidence import (
    _section_block,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def _fit_level(score: float) -> str:
    if score >= 0.85:
        return "ESTABLISHED"
    if score >= 0.7:
        return "STRONG"
    if score >= 0.5:
        return "DEVELOPING"
    if score >= 0.25:
        return "EARLY_SIGNAL"
    return "UNKNOWN"


def build_value_signal_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    analytics = _composed_section(evidence, "fix_318", "analytics_dashboard")
    feedback = _composed_section(evidence, "fix_319", "customer_feedback_dashboard")
    growth = _composed_section(evidence, "fix_320", "growth_adoption_dashboard")
    journey = _composed_section(evidence, "fix_321", "customer_journey_dashboard")

    signals: list[dict[str, Any]] = [
        {
            "signal_id": "behavioral-adoption",
            "source": "FIX 318",
            "category": "behavior",
            "detail": f"Onboarding completion {analytics.get('onboarding_completion_rate_percent', 0)}%",
            "tenant_scoped": True,
        },
        {
            "signal_id": "feedback-sentiment",
            "source": "FIX 319",
            "category": "feedback",
            "detail": f"Positive/negative sentiment {feedback.get('positive_sentiment_count', 0)}/{feedback.get('negative_sentiment_count', 0)}",
            "tenant_scoped": True,
        },
        {
            "signal_id": "growth-retention",
            "source": "FIX 320",
            "category": "growth",
            "detail": f"Retained/disengaged {growth.get('retained_customers', 0)}/{growth.get('disengaged_customers', 0)}",
            "tenant_scoped": True,
        },
        {
            "signal_id": "journey-progress",
            "source": "FIX 321",
            "category": "journey",
            "detail": f"Current stage {journey.get('current_stage', 'unknown')}",
            "tenant_scoped": True,
        },
    ]

    behavioral = _composed_section(evidence, "fix_318", "behavioral_opportunity_registry")
    for opp in (behavioral.get("opportunities") or [])[:3]:
        signals.append(
            {
                "signal_id": f"behavior-{str(opp.get('opportunity_id') or 'signal')[:24]}",
                "source": "FIX 318",
                "category": "behavior",
                "detail": str(opp.get("detail") or opp.get("signal") or "behavioral signal"),
                "tenant_scoped": True,
            }
        )

    return {
        "signals": signals,
        "count": len(signals),
        "sources": ["FIX 318", "FIX 319", "FIX 320", "FIX 321"],
        "cross_tenant_exposure_forbidden": True,
        "validated": bool(signals),
    }


def build_problem_solution_fit_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    feedback_registry = _composed_section(evidence, "fix_319", "customer_feedback_registry")
    classification = _composed_section(evidence, "fix_319", "feedback_classification_report")
    cap295 = evidence.get("fix_295") or {}
    cap296 = evidence.get("fix_296") or {}
    registry = _section_block(cap295, "capability_registry")
    proven = _section_block(cap296, "proven_capabilities")

    customer_problems: list[str] = []
    for item in classification.get("items") or []:
        if item.get("classification") in {"capability_gap", "feature_request", "usability_issue", "onboarding_issue"}:
            customer_problems.append(str(item.get("text") or "")[:120])
    for item in feedback_registry.get("items") or []:
        text = str(item.get("text") or "")
        if text and text not in customer_problems:
            customer_problems.append(text[:120])

    for label, count in (classification.get("counts_by_classification") or {}).items():
        if label in {"capability_gap", "feature_request", "usability_issue", "onboarding_issue"} and count:
            customer_problems.append(f"Recurring {label.replace('_', ' ')} ({count})")

    product_capabilities = list(proven.get("items") or [])
    product_capabilities.extend(
        str(cap.get("name") or cap)
        for cap in (registry.get("capabilities") or [])
        if isinstance(cap, dict)
    )

    resolution_evidence: list[str] = []
    success = _composed_section(evidence, "fix_321", "journey_success_report")
    for path in success.get("successful_paths") or []:
        resolution_evidence.append(f"Success path: {path}")
    positive = (classification.get("counts_by_classification") or {}).get("positive_feedback", 0)
    if positive:
        resolution_evidence.append(f"Positive feedback signals: {positive}")

    return {
        "customer_problems": customer_problems[:12],
        "product_capabilities": product_capabilities[:12],
        "problem_resolution_evidence": resolution_evidence[:8],
        "validated": bool(customer_problems or product_capabilities),
    }


def build_customer_value_realization_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    analytics = _composed_section(evidence, "fix_318", "capability_usage_report")
    feedback = _composed_section(evidence, "fix_319", "feedback_sentiment_report")
    growth = _composed_section(evidence, "fix_320", "adoption_registry")

    used = list(analytics.get("capabilities_used") or [])
    ignored = list(analytics.get("capabilities_ignored") or [])
    positive = int((feedback.get("counts_by_sentiment") or {}).get("positive", 0))
    negative = int((feedback.get("counts_by_sentiment") or {}).get("negative", 0))

    realized_value = [
        f"Adopted capabilities: {', '.join(used[:4])}" if used else "Limited capability adoption recorded",
        f"Activated customers: {growth.get('activated_customers', 0)}",
    ]
    unrealized_value = [
        f"Ignored or low-adoption capabilities: {', '.join(ignored[:4])}" if ignored else "No ignored capabilities flagged",
    ]
    gaps = _composed_section(evidence, "fix_319", "capability_gap_report").get("gaps") or []
    for gap in gaps[:4]:
        unrealized_value.append(str(gap.get("requested_capability") or gap))

    perceived_value = []
    if positive:
        perceived_value.append(f"Positive sentiment count: {positive}")
    if negative:
        perceived_value.append(f"Negative sentiment count: {negative}")
    if not perceived_value:
        perceived_value.append("Perceived value signals pending submitted feedback")

    return {
        "realized_value": realized_value,
        "unrealized_value": unrealized_value,
        "perceived_value": perceived_value,
        "validated": bool(realized_value or unrealized_value or perceived_value),
    }


def build_capability_demand_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    cap295 = evidence.get("fix_295") or {}
    cap296 = evidence.get("fix_296") or {}
    gap_report = _composed_section(evidence, "fix_319", "capability_gap_report")
    usage = _composed_section(evidence, "fix_318", "capability_usage_report")
    classification = _composed_section(evidence, "fix_319", "feedback_classification_report")

    requested: list[str] = list(gap_report.get("requested_capabilities") or [])
    for item in (_composed_section(evidence, "fix_319", "customer_feedback_registry").get("items") or []):
        if item.get("classification") in {"feature_request", "capability_gap"}:
            requested.append(str(item.get("text") or "")[:120])

    adopted = list(usage.get("capabilities_used") or [])
    ignored = list(usage.get("capabilities_ignored") or [])
    existing = list(_section_block(cap296, "proven_capabilities").get("items") or [])
    existing.extend(_section_block(cap296, "operational_capabilities").get("items") or [])

    return {
        "sources": ["FIX 295", "FIX 319"],
        "requested_capabilities": requested[:12],
        "adopted_capabilities": adopted[:12],
        "ignored_capabilities": ignored[:12],
        "existing_capabilities": existing[:12],
        "feature_request_count": (classification.get("counts_by_classification") or {}).get("feature_request", 0),
        "capability_registry_count": _section_block(cap295, "capability_registry").get("capability_count", 0),
        "validated": bool(requested or adopted or existing),
    }


def build_retention_value_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    retention = _composed_section(evidence, "fix_320", "retention_intelligence_report")
    success = _composed_section(evidence, "fix_320", "success_pattern_report")
    journey_success = _composed_section(evidence, "fix_321", "journey_success_report")
    usage = _composed_section(evidence, "fix_318", "capability_usage_report")

    retention_drivers = list(success.get("behaviors_linked_to_success") or [])
    retention_drivers.extend(journey_success.get("high_retention_paths") or [])

    capability_drivers = list(usage.get("capabilities_used") or [])[:6]
    journey_drivers = list(journey_success.get("successful_paths") or [])[:6]

    return {
        "sources": ["FIX 320"],
        "capabilities_driving_retention": capability_drivers,
        "journeys_driving_retention": journey_drivers,
        "retained_customers": retention.get("retained_customers", 0),
        "retention_trend": retention.get("retention_trend", "stable"),
        "retention_drivers": retention_drivers[:10],
        "validated": bool(capability_drivers or journey_drivers or retention),
    }


def build_expansion_value_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    expansion = _composed_section(evidence, "fix_320", "expansion_intelligence_report")
    commercial = _composed_section(evidence, "fix_318", "commercial_analytics_report")
    usage = _composed_section(evidence, "fix_318", "capability_usage_report")

    upgrade_capabilities = list(usage.get("capabilities_used") or [])[:6]
    expansion_paths = list(expansion.get("plan_expansion") or [])
    upgrade_candidates = list(expansion.get("upgrade_candidates") or [])

    return {
        "capabilities_driving_upgrades": upgrade_capabilities,
        "capabilities_driving_expansion": upgrade_capabilities[:4],
        "plan_expansion_paths": expansion_paths[:8],
        "upgrade_candidates": upgrade_candidates[:8],
        "active_subscriptions": commercial.get("active_subscription_count", 0),
        "validated": bool(expansion or commercial or usage),
    }


def build_pmf_opportunity_registry(
    *,
    problem_solution_report: dict[str, Any],
    value_report: dict[str, Any],
    capability_demand: dict[str, Any],
    retention_value: dict[str, Any],
    expansion_value: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    for gap in capability_demand.get("requested_capabilities") or []:
        if gap not in (capability_demand.get("adopted_capabilities") or []):
            opportunities.append(
                {
                    "opportunity_id": f"missing-capability-{str(gap)[:24]}",
                    "title": f"Unmet capability demand: {gap}",
                    "category": "missing_capabilities",
                    "impact": "high",
                    "automatic_product_strategy_forbidden": True,
                }
            )

    for item in value_report.get("unrealized_value") or []:
        opportunities.append(
            {
                "opportunity_id": f"unrealized-value-{len(opportunities) + 1}",
                "title": str(item)[:120],
                "category": "unmet_demand",
                "impact": "medium",
                "automatic_product_strategy_forbidden": True,
            }
        )

    if not retention_value.get("capabilities_driving_retention"):
        opportunities.append(
            {
                "opportunity_id": "weak-retention-drivers",
                "title": "Weak retention driver signals — clarify value-creating capabilities",
                "category": "weak_retention_drivers",
                "impact": "high",
                "automatic_product_strategy_forbidden": True,
            }
        )

    for ignored in capability_demand.get("ignored_capabilities") or []:
        opportunities.append(
            {
                "opportunity_id": f"low-value-workflow-{str(ignored)[:24]}",
                "title": f"Low-value or ignored workflow: {ignored}",
                "category": "low_value_workflows",
                "impact": "medium",
                "automatic_product_strategy_forbidden": True,
            }
        )

    if not expansion_value.get("upgrade_candidates") and not expansion_value.get("plan_expansion_paths"):
        opportunities.append(
            {
                "opportunity_id": "expansion-signals-pending",
                "title": "Expansion value signals pending stronger adoption evidence",
                "category": "unmet_demand",
                "impact": "low",
                "automatic_product_strategy_forbidden": True,
            }
        )

    if problem_solution_report.get("customer_problems") and not problem_solution_report.get("problem_resolution_evidence"):
        opportunities.append(
            {
                "opportunity_id": "problem-resolution-gap",
                "title": "Customer problems identified without sufficient resolution evidence",
                "category": "unmet_demand",
                "impact": "high",
                "automatic_product_strategy_forbidden": True,
            }
        )

    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "core_principle": PMF_CORE_PRINCIPLE,
    }


def build_pmf_scorecard(*, evidence: dict[str, Any]) -> dict[str, Any]:
    demand_report = build_capability_demand_report(evidence=evidence)
    adoption = _composed_section(evidence, "fix_320", "adoption_analytics_report")
    retention = _composed_section(evidence, "fix_320", "retention_intelligence_report")
    expansion = _composed_section(evidence, "fix_320", "expansion_intelligence_report")
    feedback = _composed_section(evidence, "fix_319", "customer_feedback_dashboard")

    demand_score = min(
        1.0,
        (len(demand_report.get("requested_capabilities") or []) * 0.1)
        + (demand_report.get("feature_request_count", 0) * 0.05),
    )
    adoption_rate = float(adoption.get("adoption_rate_percent") or 0) / 100.0
    retained = int(retention.get("retained_customers") or 0)
    disengaged = int(retention.get("disengaged_customers") or 0)
    retention_score = retained / max(retained + disengaged, 1)
    expansion_score = min(1.0, len(expansion.get("plan_expansion") or expansion.get("upgrade_candidates") or []) * 0.2)
    advocacy_score = min(
        1.0,
        int(feedback.get("positive_sentiment_count") or 0) / max(int(feedback.get("feedback_item_count") or 1), 1),
    )

    dimensions = {
        "demand": round(demand_score, 3),
        "adoption": round(adoption_rate, 3),
        "retention": round(retention_score, 3),
        "expansion": round(expansion_score, 3),
        "advocacy": round(advocacy_score, 3),
    }
    overall = round(sum(dimensions.values()) / len(dimensions), 3)

    return {
        "dimensions": dimensions,
        "dimension_labels": list(PMF_SCORECARD_DIMENSIONS),
        "overall_score": overall,
        "overall_level": _fit_level(overall),
        "dimension_levels": {key: _fit_level(score) for key, score in dimensions.items()},
        "fit_levels": list(PMF_FIT_LEVELS),
        "validated": True,
    }


def build_product_market_fit_dashboard(
    *,
    value_registry: dict[str, Any],
    problem_solution_report: dict[str, Any],
    value_report: dict[str, Any],
    capability_demand: dict[str, Any],
    scorecard: dict[str, Any],
    opportunity_registry: dict[str, Any],
) -> dict[str, Any]:
    return {
        "value_signal_count": value_registry.get("count", 0),
        "customer_problem_count": len(problem_solution_report.get("customer_problems") or []),
        "realized_value_signals": len(value_report.get("realized_value") or []),
        "unrealized_value_signals": len(value_report.get("unrealized_value") or []),
        "requested_capability_count": len(capability_demand.get("requested_capabilities") or []),
        "adopted_capability_count": len(capability_demand.get("adopted_capabilities") or []),
        "ignored_capability_count": len(capability_demand.get("ignored_capabilities") or []),
        "pmf_overall_score": scorecard.get("overall_score", 0),
        "pmf_overall_level": scorecard.get("overall_level", "UNKNOWN"),
        "pmf_opportunity_count": opportunity_registry.get("count", 0),
        "core_principle": PMF_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_product_strategy_forbidden": True,
    }

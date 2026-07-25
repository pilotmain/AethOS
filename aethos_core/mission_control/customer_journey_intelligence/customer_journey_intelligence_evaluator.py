# SPDX-License-Identifier: Apache-2.0
"""FIX 321 — customer journey intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_contract import (
    JOURNEY_CORE_PRINCIPLE,
    JOURNEY_FUNNEL_TRANSITIONS,
    JOURNEY_OPPORTUNITY_TYPES,
    JOURNEY_STAGES,
    PRIVACY_REQUIREMENTS,
    PROGRESSION_STATES,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evidence import (
    _section_block,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def _stage_counts(*, evidence: dict[str, Any]) -> dict[str, int]:
    tenant = evidence.get("fix_300") or {}
    onboarding = evidence.get("fix_301") or {}
    product = evidence.get("fix_311") or {}
    beta = evidence.get("fix_312") or {}
    analytics = _composed_section(evidence, "fix_318", "user_journey_report")
    growth = _composed_section(evidence, "fix_320", "growth_adoption_dashboard")
    feedback = _composed_section(evidence, "fix_319", "customer_feedback_dashboard")

    tenant_dashboard = _section_block(tenant, "tenant_dashboard")
    progress = _section_block(onboarding, "onboarding_progress_registry")
    product_dashboard = _section_block(product, "public_product_dashboard")
    beta_cohort = _section_block(beta, "beta_cohort_registry")

    org_count = int(tenant_dashboard.get("organization_count") or 0)
    user_count = int(tenant_dashboard.get("user_count") or org_count or 0)
    started = int(progress.get("started_count") or user_count or 1)
    completed = int(progress.get("completed_count") or progress.get("completed_steps_count") or 0)
    activated = int(growth.get("activated_customers") or completed or 0)
    capability_usage = _composed_section(evidence, "fix_318", "capability_usage_report")
    capabilities_used = capability_usage.get("capabilities_used") or []
    capability_count = len(capabilities_used) or activated
    retained = int(growth.get("retained_customers") or (_composed_section(evidence, "fix_318", "customer_success_analytics_report").get("healthy_customers") or 0))
    expansion_signals = int(growth.get("workspace_growth") or tenant_dashboard.get("workspace_count") or 0)
    advocacy_signals = int(feedback.get("positive_sentiment_count") or beta_cohort.get("participant_count") or 0)

    evaluation_count = int(product_dashboard.get("visitor_count") or beta_cohort.get("admitted_count") or org_count or user_count)
    if evaluation_count == 0 and org_count:
        evaluation_count = org_count

    adoption_count = max(capability_count, int((_composed_section(evidence, "fix_320", "adoption_registry").get("activated_customers") or activated)))

    stages_data = (analytics.get("stages") or {})
    activation_count = int(stages_data.get("activation", {}).get("onboarding_completed") or activated or completed)
    retention_count = int(stages_data.get("retention", {}).get("retained_subscriptions") or retained)
    expansion_count = int(stages_data.get("expansion", {}).get("upgrade_candidates") or expansion_signals)

    return {
        "awareness": max(user_count, org_count, 1),
        "evaluation": max(evaluation_count, 1),
        "onboarding": max(started, 1),
        "activation": max(activation_count, completed, 0),
        "adoption": max(adoption_count, 0),
        "retention": max(retention_count, retained, 0),
        "expansion": max(expansion_count, 0),
        "advocacy": max(advocacy_signals, 0),
    }


def _progression_state(*, stage: str, count: int, prior_count: int) -> str:
    if count <= 0:
        return "not_started"
    if stage == "onboarding" and count < prior_count:
        return "stalled"
    if count >= prior_count and prior_count > 0:
        return "completed"
    if count > 0:
        return "in_progress"
    return "not_started"


def _confidence(*, stage: str, count: int, sources_ok: dict[str, Any]) -> float:
    base = 0.55
    if count > 0:
        base += 0.15
    source_map = {
        "awareness": ["fix_300", "fix_312"],
        "evaluation": ["fix_311", "fix_312"],
        "onboarding": ["fix_301"],
        "activation": ["fix_301", "fix_318"],
        "adoption": ["fix_318", "fix_320"],
        "retention": ["fix_318", "fix_320"],
        "expansion": ["fix_320"],
        "advocacy": ["fix_319", "fix_312"],
    }
    ok_count = sum(1 for key in source_map.get(stage, []) if sources_ok.get(key))
    return round(min(base + ok_count * 0.1, 0.95), 2)


def build_customer_journey_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    sid = str(evidence.get("session_id") or "default")
    counts = _stage_counts(evidence=evidence)
    sources_ok = evidence.get("sources_ok") or {}
    entries: list[dict[str, Any]] = []
    prior = counts["awareness"]

    for stage in JOURNEY_STAGES:
        count = counts.get(stage, 0)
        state = _progression_state(stage=stage, count=count, prior_count=prior)
        entries.append(
            {
                "tenant": sid,
                "stage": stage,
                "progression_state": state,
                "confidence": _confidence(stage=stage, count=count, sources_ok=sources_ok),
                "stage_signal_count": count,
                "tenant_scoped": True,
            }
        )
        if count > 0:
            prior = count

    current_stage = "awareness"
    for stage in reversed(JOURNEY_STAGES):
        if counts.get(stage, 0) > 0:
            current_stage = stage
            break

    return {
        "entries": entries,
        "current_stage": current_stage,
        "journey_stages": list(JOURNEY_STAGES),
        "cross_tenant_journey_analysis_forbidden": True,
        "validated": bool(entries),
    }


def build_journey_funnel_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    counts = _stage_counts(evidence=evidence)
    transitions: list[dict[str, Any]] = []

    for from_stage, to_stage in JOURNEY_FUNNEL_TRANSITIONS:
        from_count = max(counts.get(from_stage, 0), 1)
        to_count = counts.get(to_stage, 0)
        conversion_rate = round((to_count / from_count) * 100, 1) if from_count else 0.0
        transitions.append(
            {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "from_count": from_count,
                "to_count": to_count,
                "conversion_rate_percent": conversion_rate,
            }
        )

    return {
        "transitions": transitions,
        "stage_counts": counts,
        "validated": bool(transitions),
    }


def build_journey_dropoff_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    onboarding = evidence.get("fix_301") or {}
    progress = _section_block(onboarding, "onboarding_progress_registry")
    onboarding_analytics = _composed_section(evidence, "fix_318", "onboarding_analytics_report")
    feedback_trends = _composed_section(evidence, "fix_319", "feedback_trend_report")

    abandonment_points = list(
        onboarding_analytics.get("drop_off_points")
        or progress.get("incomplete_steps")
        or progress.get("pending_steps")
        or []
    )
    stalled_journeys: list[str] = []
    if progress.get("incomplete_steps") or progress.get("pending_steps"):
        stalled_journeys.append("onboarding_incomplete")
    if _section_block(evidence.get("fix_303") or {}, "provider_connection_dashboard").get(
        "connected_provider_count", 1
    ) == 0:
        stalled_journeys.append("provider_not_connected")

    friction_hotspots = list(abandonment_points)
    for item in _composed_section(evidence, "fix_319", "customer_friction_report").get("onboarding_friction") or []:
        friction_hotspots.append(str(item.get("title") or item) if isinstance(item, dict) else str(item))

    return {
        "abandonment_points": abandonment_points[:10],
        "stalled_journeys": stalled_journeys,
        "friction_hotspots": friction_hotspots[:10],
        "feedback_dropoff_linked": bool(feedback_trends.get("recurring_complaints")),
        "validated": bool(abandonment_points or stalled_journeys or friction_hotspots),
    }


def build_journey_success_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    journey = _composed_section(evidence, "fix_318", "user_journey_report")
    feedback_trends = _composed_section(evidence, "fix_319", "feedback_trend_report")
    growth_success = _composed_section(evidence, "fix_320", "success_pattern_report")
    growth_expansion = _composed_section(evidence, "fix_320", "expansion_intelligence_report")

    successful_paths = list(journey.get("success_predictors") or [])
    successful_paths.extend(growth_success.get("behaviors_linked_to_success") or [])

    high_retention_paths = list(growth_success.get("onboarding_paths_linked_to_retention") or [])
    if journey.get("stages", {}).get("retention"):
        high_retention_paths.append("healthy_customer_status")

    expansion_paths = list(growth_expansion.get("plan_expansion") or [])
    expansion_paths.extend(growth_expansion.get("upgrade_candidates") or [])

    recurring_requests = feedback_trends.get("recurring_requests") or []
    if recurring_requests:
        successful_paths.append("address_recurring_requests_for_retention")

    return {
        "sources": ["FIX 318", "FIX 319", "FIX 320"],
        "successful_paths": successful_paths[:12],
        "high_retention_paths": high_retention_paths[:8],
        "expansion_paths": expansion_paths[:8],
        "validated": bool(successful_paths or high_retention_paths or expansion_paths),
    }


def build_journey_friction_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    onboarding = evidence.get("fix_301") or {}
    provider = evidence.get("fix_303") or {}
    feedback_friction = _composed_section(evidence, "fix_319", "customer_friction_report")
    progress = _section_block(onboarding, "onboarding_progress_registry")
    provider_dashboard = _section_block(provider, "provider_connection_dashboard")
    provider_analytics = _composed_section(evidence, "fix_318", "provider_analytics_report")

    onboarding_friction = list(
        feedback_friction.get("onboarding_friction")
        or progress.get("incomplete_steps")
        or progress.get("pending_steps")
        or []
    )
    provider_friction = list(
        feedback_friction.get("provider_friction")
        or provider_analytics.get("readiness_failures")
        or []
    )
    capability_friction = list(
        (_composed_section(evidence, "fix_318", "capability_usage_report").get("capabilities_confusing") or [])
        + (_composed_section(evidence, "fix_318", "capability_usage_report").get("capabilities_ignored") or [])
    )

    return {
        "sources": ["FIX 301", "FIX 303", "FIX 319"],
        "onboarding_friction": onboarding_friction[:8],
        "provider_connection_friction": provider_friction[:8],
        "capability_discovery_friction": capability_friction[:8],
        "connected_provider_count": provider_dashboard.get("connected_provider_count", 0),
        "validated": bool(onboarding_friction or provider_friction or capability_friction),
    }


def build_journey_cohort_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    retention = _composed_section(evidence, "fix_320", "retention_intelligence_report")
    beta = evidence.get("fix_312") or {}
    onboarding = evidence.get("fix_301") or {}
    beta_cohort = _section_block(beta, "beta_cohort_registry")
    progress = _section_block(onboarding, "onboarding_progress_registry")

    cohorts = [
        {
            "cohort": "beta_participants",
            "size": beta_cohort.get("participant_count", 0),
            "performance": beta_cohort.get("admitted_count", 0),
            "retention_signal": "beta_engaged",
        },
        {
            "cohort": "onboarding_started",
            "size": progress.get("started_count", 0),
            "performance": progress.get("completed_count", 0),
            "retention_signal": "onboarding_completion",
        },
    ]
    cohorts.extend(
        {
            "cohort": str(row.get("cohort") or "retention"),
            "size": row.get("count", 0),
            "performance": row.get("count", 0),
            "retention_signal": retention.get("retention_trend", "stable"),
        }
        for row in (retention.get("retention_cohorts") or [])
    )

    return {
        "cohorts": cohorts,
        "cohort_progression": [
            {"cohort": c["cohort"], "progression": c.get("performance", 0)} for c in cohorts if c.get("size")
        ],
        "cohort_retention": [
            {"cohort": c["cohort"], "retention_signal": c.get("retention_signal")} for c in cohorts
        ],
        "validated": bool(cohorts),
    }


def build_journey_opportunity_registry(
    *,
    dropoff_report: dict[str, Any],
    friction_report: dict[str, Any],
    success_report: dict[str, Any],
    cohort_report: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    for point in dropoff_report.get("abandonment_points") or []:
        opportunities.append(
            {
                "opportunity_id": f"activation-{str(point)[:24]}",
                "title": f"Reduce drop-off at {point}",
                "opportunity_type": "activation",
                "journey_impact": "high",
                "customer_impact": "high",
                "retention_impact": "medium",
                "effort": "medium",
                "automatic_customer_intervention_forbidden": True,
            }
        )

    for friction in friction_report.get("onboarding_friction") or []:
        opportunities.append(
            {
                "opportunity_id": f"activation-friction-{str(friction)[:24]}",
                "title": f"Resolve onboarding friction: {friction}",
                "opportunity_type": "activation",
                "journey_impact": "high",
                "customer_impact": "high",
                "retention_impact": "high",
                "effort": "medium",
                "automatic_customer_intervention_forbidden": True,
            }
        )

    for stalled in dropoff_report.get("stalled_journeys") or []:
        opportunities.append(
            {
                "opportunity_id": f"retention-stalled-{str(stalled)[:24]}",
                "title": f"Unblock stalled journey: {stalled}",
                "opportunity_type": "retention",
                "journey_impact": "high",
                "customer_impact": "high",
                "retention_impact": "high",
                "effort": "high",
                "automatic_customer_intervention_forbidden": True,
            }
        )

    for path in success_report.get("expansion_paths") or []:
        opportunities.append(
            {
                "opportunity_id": f"expansion-{str(path)[:24]}",
                "title": f"Support expansion path: {path}",
                "opportunity_type": "expansion",
                "journey_impact": "medium",
                "customer_impact": "medium",
                "retention_impact": "low",
                "effort": "low",
                "automatic_customer_intervention_forbidden": True,
            }
        )

    for cohort in cohort_report.get("cohorts") or []:
        if cohort.get("cohort") == "onboarding_started" and cohort.get("size", 0) > cohort.get("performance", 0):
            opportunities.append(
                {
                    "opportunity_id": "retention-onboarding-cohort",
                    "title": "Improve onboarding cohort completion for retention",
                    "opportunity_type": "retention",
                    "journey_impact": "high",
                    "customer_impact": "high",
                    "retention_impact": "high",
                    "effort": "medium",
                    "automatic_customer_intervention_forbidden": True,
                }
            )
            break

    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "opportunity_types": list(JOURNEY_OPPORTUNITY_TYPES),
        "core_principle": JOURNEY_CORE_PRINCIPLE,
    }


def _priority_score(opportunity: dict[str, Any]) -> float:
    impact_scores = {"high": 3.0, "medium": 2.0, "low": 1.0}
    journey = impact_scores.get(str(opportunity.get("journey_impact") or "medium"), 2.0)
    customer = impact_scores.get(str(opportunity.get("customer_impact") or "medium"), 2.0)
    retention = impact_scores.get(str(opportunity.get("retention_impact") or "medium"), 2.0)
    effort_penalty = {"low": 0.0, "medium": 0.5, "high": 1.0}.get(str(opportunity.get("effort") or "medium"), 0.5)
    return round(journey + customer + retention - effort_penalty, 3)


def build_journey_priority_matrix(*, registry: dict[str, Any]) -> dict[str, Any]:
    ranked = [{**opp, "priority_score": _priority_score(opp)} for opp in registry.get("opportunities") or []]
    ranked.sort(key=lambda row: row["priority_score"], reverse=True)
    return {
        "ranked_opportunities": ranked[:12],
        "highest_journey_impact": [row for row in ranked if row.get("journey_impact") == "high"][:5],
        "highest_retention_impact": [row for row in ranked if row.get("retention_impact") == "high"][:5],
        "automatic_customer_intervention_forbidden": True,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
    }

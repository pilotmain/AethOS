# SPDX-License-Identifier: Apache-2.0
"""FIX 323 — customer value realization intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_contract import (
    PRIVACY_REQUIREMENTS,
    VALUE_OPPORTUNITY_TYPES,
    VALUE_OUTCOME_CATEGORIES,
    VALUE_REALIZATION_CORE_PRINCIPLE,
    VALUE_REALIZATION_LEVELS,
    VALUE_REALIZATION_SCORECARD_DIMENSIONS,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evidence import (
    _section_block,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def _realization_level(score: float) -> str:
    if score >= 0.85:
        return "EXCEPTIONAL"
    if score >= 0.7:
        return "HIGH"
    if score >= 0.5:
        return "MODERATE"
    if score >= 0.25:
        return "LOW"
    return "UNKNOWN"


def build_value_outcome_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    usage = _composed_section(evidence, "fix_318", "capability_usage_report")
    journey_success = _composed_section(evidence, "fix_321", "journey_success_report")
    pmf_value = _composed_section(evidence, "fix_322", "customer_value_realization_report")
    support = evidence.get("fix_310") or {}
    adoption = _section_block(support, "customer_adoption_report")

    outcomes: list[dict[str, Any]] = []
    if usage.get("capabilities_used"):
        outcomes.append(
            {
                "outcome_id": "workflow-improvement",
                "category": "workflow_improvement",
                "detail": f"Adopted capabilities: {', '.join((usage.get('capabilities_used') or [])[:4])}",
                "tenant_scoped": True,
            }
        )
    if journey_success.get("successful_paths"):
        outcomes.append(
            {
                "outcome_id": "operational-improvement",
                "category": "operational_improvement",
                "detail": f"Successful paths: {', '.join(journey_success.get('successful_paths')[:3])}",
                "tenant_scoped": True,
            }
        )
    onboarding_rate = _composed_section(evidence, "fix_318", "onboarding_analytics_report").get(
        "average_completion_rate_percent", 0
    )
    if onboarding_rate:
        outcomes.append(
            {
                "outcome_id": "time-saved-onboarding",
                "category": "time_saved",
                "detail": f"Onboarding completion at {onboarding_rate}% reduces setup friction",
                "tenant_scoped": True,
            }
        )
    if pmf_value.get("realized_value"):
        outcomes.append(
            {
                "outcome_id": "visibility-improvement",
                "category": "visibility_improvement",
                "detail": str((pmf_value.get("realized_value") or ["Improved product visibility"])[0]),
                "tenant_scoped": True,
            }
        )
    if adoption.get("engagement_trend") or adoption.get("trends"):
        outcomes.append(
            {
                "outcome_id": "governance-improvement",
                "category": "governance_improvement",
                "detail": f"Engagement trend: {adoption.get('engagement_trend') or adoption.get('trends') or 'stable'}",
                "tenant_scoped": True,
            }
        )

    if not outcomes:
        outcomes.append(
            {
                "outcome_id": "placeholder-outcome",
                "category": "workflow_improvement",
                "detail": "Value outcome evidence pending tenant-scoped intake",
                "tenant_scoped": True,
            }
        )

    return {
        "outcomes": outcomes,
        "count": len(outcomes),
        "categories": list(VALUE_OUTCOME_CATEGORIES),
        "cross_tenant_exposure_forbidden": True,
        "validated": bool(outcomes),
    }


def build_expected_value_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    onboarding = evidence.get("fix_301") or {}
    progress = _section_block(onboarding, "onboarding_progress_registry")
    activation = _section_block(onboarding, "onboarding_activation_registry")
    support = evidence.get("fix_310") or {}
    success_dashboard = _section_block(support, "customer_success_dashboard")
    pmf = _composed_section(evidence, "fix_322", "problem_solution_fit_report")

    expectations: list[dict[str, Any]] = [
        {
            "expectation_id": "onboarding-completion",
            "source": "onboarding_expectations",
            "detail": "Complete onboarding and activate Mission Control",
            "objective": "activation",
        },
        {
            "expectation_id": "provider-connection",
            "source": "onboarding_expectations",
            "detail": "Connect primary provider and reach operational readiness",
            "objective": "activation",
        },
    ]
    for step in progress.get("steps") or progress.get("onboarding_steps") or []:
        expectations.append(
            {
                "expectation_id": f"onboarding-step-{str(step)[:24]}",
                "source": "onboarding_expectations",
                "detail": f"Complete onboarding step: {step}",
                "objective": "activation",
            }
        )
    for goal in activation.get("success_objectives") or activation.get("objectives") or []:
        expectations.append(
            {
                "expectation_id": f"success-objective-{str(goal)[:24]}",
                "source": "success_objectives",
                "detail": str(goal),
                "objective": "customer_success",
            }
        )
    for obs in success_dashboard.get("observations") or success_dashboard.get("success_goals") or []:
        expectations.append(
            {
                "expectation_id": f"customer-goal-{str(obs)[:24]}",
                "source": "customer_goals",
                "detail": str(obs),
                "objective": "customer_success",
            }
        )
    if pmf.get("customer_problems"):
        expectations.append(
            {
                "expectation_id": "product-promise-resolution",
                "source": "product_promises",
                "detail": "Resolve primary customer problems through product capabilities",
                "objective": "value_realization",
            }
        )

    return {
        "expectations": expectations[:16],
        "count": len(expectations[:16]),
        "sources": ["onboarding_expectations", "customer_goals", "success_objectives", "product_promises"],
        "validated": bool(expectations),
    }


def build_value_gap_report(
    *,
    outcome_registry: dict[str, Any],
    expected_registry: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    pmf_value = _composed_section(evidence, "fix_322", "customer_value_realization_report")
    unrealized = list(pmf_value.get("unrealized_value") or [])
    realized_count = outcome_registry.get("count", 0)
    expected_count = expected_registry.get("count", 0)
    gap_count = max(expected_count - realized_count, len(unrealized))

    gaps: list[dict[str, Any]] = []
    for item in unrealized[:8]:
        gaps.append(
            {
                "expected_value": "Full capability and workflow value",
                "realized_value": str(item),
                "value_gap": "unrealized_capability_or_workflow_value",
            }
        )
    ignored = _composed_section(evidence, "fix_318", "capability_usage_report").get("capabilities_ignored") or []
    for cap in ignored[:4]:
        gaps.append(
            {
                "expected_value": f"Value from {cap}",
                "realized_value": "Not adopted or underutilized",
                "value_gap": "adoption_gap",
            }
        )

    return {
        "gaps": gaps,
        "gap_count": gap_count,
        "realized_outcome_count": realized_count,
        "expected_outcome_count": expected_count,
        "validated": bool(gaps or expected_count),
    }


def build_capability_value_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    cap295 = evidence.get("fix_295") or {}
    usage = _composed_section(evidence, "fix_318", "capability_usage_report")
    retention = _composed_section(evidence, "fix_320", "retention_value_report")
    registry = _section_block(cap295, "capability_registry")

    value_by_capability: list[dict[str, Any]] = []
    for cap in usage.get("capabilities_used") or []:
        value_by_capability.append(
            {
                "capability": cap,
                "value_signal": "adopted_and_used",
                "retention_linked": cap in (retention.get("capabilities_driving_retention") or []),
            }
        )
    for cap in usage.get("capabilities_ignored") or []:
        value_by_capability.append(
            {
                "capability": cap,
                "value_signal": "low_or_no_value_realization",
                "retention_linked": False,
            }
        )

    top_value = [row for row in value_by_capability if row.get("value_signal") == "adopted_and_used"][:6]

    return {
        "sources": ["FIX 295", "FIX 318", "FIX 320"],
        "capabilities": value_by_capability[:12],
        "highest_value_capabilities": top_value,
        "capability_count": registry.get("capability_count", len(value_by_capability)),
        "validated": bool(value_by_capability),
    }


def build_journey_value_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    journey_success = _composed_section(evidence, "fix_321", "journey_success_report")
    journey_registry = _composed_section(evidence, "fix_321", "customer_journey_registry")
    funnel = _composed_section(evidence, "fix_321", "journey_funnel_report")

    journeys: list[dict[str, Any]] = []
    for path in journey_success.get("successful_paths") or []:
        journeys.append({"journey": path, "value_signal": "success_path", "stage": "success"})
    for path in journey_success.get("high_retention_paths") or []:
        journeys.append({"journey": path, "value_signal": "retention_path", "stage": "retention"})
    for path in journey_success.get("expansion_paths") or []:
        journeys.append({"journey": path, "value_signal": "expansion_path", "stage": "expansion"})

    current_stage = journey_registry.get("current_stage")
    if current_stage:
        journeys.append(
            {
                "journey": f"current_stage:{current_stage}",
                "value_signal": "active_journey",
                "stage": current_stage,
            }
        )

    top_transitions = sorted(
        funnel.get("transitions") or [],
        key=lambda row: float(row.get("conversion_rate_percent") or 0),
        reverse=True,
    )[:3]

    return {
        "sources": ["FIX 321"],
        "journeys": journeys[:12],
        "highest_value_journeys": journeys[:6],
        "top_converting_stages": top_transitions,
        "validated": bool(journeys),
    }


def build_customer_success_outcome_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    support = evidence.get("fix_310") or {}
    growth = _composed_section(evidence, "fix_320", "retention_intelligence_report")
    health = _section_block(support, "customer_health_registry")
    risk = _section_block(support, "customer_risk_registry")

    successful = int(health.get("healthy_count") or growth.get("retained_customers") or 0)
    at_risk = int(risk.get("at_risk_count") or growth.get("disengaged_customers") or 0)
    partial = max(successful // 2, 0) if successful and at_risk else 0
    unsuccessful = at_risk

    return {
        "sources": ["FIX 310", "FIX 320"],
        "successful_customers": successful,
        "partially_successful_customers": partial,
        "unsuccessful_customers": unsuccessful,
        "retention_trend": growth.get("retention_trend", "stable"),
        "validated": bool(support or growth),
    }


def build_value_opportunity_registry(
    *,
    gap_report: dict[str, Any],
    capability_value: dict[str, Any],
    journey_value: dict[str, Any],
    success_outcome: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    for gap in gap_report.get("gaps") or []:
        opportunities.append(
            {
                "opportunity_id": f"unrealized-{len(opportunities) + 1}",
                "title": f"Close value gap: {gap.get('value_gap')}",
                "opportunity_type": "unrealized_value",
                "value_gap": str(gap.get("realized_value") or gap.get("value_gap")),
                "impact": "high",
                "confidence": 0.82,
                "effort": "medium",
                "automatic_customer_success_forbidden": True,
            }
        )

    for cap in capability_value.get("capabilities") or []:
        if cap.get("value_signal") == "low_or_no_value_realization":
            opportunities.append(
                {
                    "opportunity_id": f"adoption-{str(cap.get('capability'))[:24]}",
                    "title": f"Increase value adoption for {cap.get('capability')}",
                    "opportunity_type": "adoption",
                    "value_gap": "capability_underutilized",
                    "impact": "medium",
                    "confidence": 0.78,
                    "effort": "low",
                    "automatic_customer_success_forbidden": True,
                }
            )

    if success_outcome.get("partially_successful_customers"):
        opportunities.append(
            {
                "opportunity_id": "education-partial-success",
                "title": "Education opportunity for partially successful customers",
                "opportunity_type": "education",
                "value_gap": "partial_value_realization",
                "impact": "medium",
                "confidence": 0.75,
                "effort": "medium",
                "automatic_customer_success_forbidden": True,
            }
        )

    for journey in journey_value.get("journeys") or []:
        if journey.get("value_signal") == "active_journey" and "onboarding" in str(journey.get("stage") or ""):
            opportunities.append(
                {
                    "opportunity_id": "onboarding-value-gap",
                    "title": "Onboarding opportunity to unlock full journey value",
                    "opportunity_type": "onboarding",
                    "value_gap": "journey_value_incomplete",
                    "impact": "high",
                    "confidence": 0.8,
                    "effort": "medium",
                    "automatic_customer_success_forbidden": True,
                }
            )
            break

    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "opportunity_types": list(VALUE_OPPORTUNITY_TYPES),
        "core_principle": VALUE_REALIZATION_CORE_PRINCIPLE,
    }


def build_value_realization_scorecard(
    *,
    outcome_registry: dict[str, Any],
    gap_report: dict[str, Any],
    capability_value: dict[str, Any],
    success_outcome: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    growth = _composed_section(evidence, "fix_320", "growth_adoption_dashboard")
    expected = gap_report.get("expected_outcome_count") or 1
    realized = gap_report.get("realized_outcome_count") or 0
    outcome_score = min(1.0, realized / max(expected, 1))

    adopted = len([c for c in capability_value.get("capabilities") or [] if c.get("value_signal") == "adopted_and_used"])
    total_caps = max(len(capability_value.get("capabilities") or []), 1)
    adoption_score = min(1.0, adopted / total_caps)

    retained = int(success_outcome.get("successful_customers") or 0)
    at_risk = int(success_outcome.get("unsuccessful_customers") or 0)
    retention_score = retained / max(retained + at_risk, 1)

    expansion_score = min(1.0, int(growth.get("workspace_growth") or 0) / 10.0)

    dimensions = {
        "outcome_achievement": round(outcome_score, 3),
        "value_adoption": round(adoption_score, 3),
        "value_retention": round(retention_score, 3),
        "value_expansion": round(expansion_score, 3),
    }
    overall = round(sum(dimensions.values()) / len(dimensions), 3)

    return {
        "dimensions": dimensions,
        "dimension_labels": list(VALUE_REALIZATION_SCORECARD_DIMENSIONS),
        "overall_score": overall,
        "overall_level": _realization_level(overall),
        "dimension_levels": {key: _realization_level(score) for key, score in dimensions.items()},
        "realization_levels": list(VALUE_REALIZATION_LEVELS),
        "outcome_count": outcome_registry.get("count", 0),
        "validated": True,
    }


def build_customer_value_dashboard(
    *,
    outcome_registry: dict[str, Any],
    expected_registry: dict[str, Any],
    gap_report: dict[str, Any],
    capability_value: dict[str, Any],
    journey_value: dict[str, Any],
    success_outcome: dict[str, Any],
    scorecard: dict[str, Any],
    opportunity_registry: dict[str, Any],
) -> dict[str, Any]:
    return {
        "realized_outcome_count": outcome_registry.get("count", 0),
        "expected_outcome_count": expected_registry.get("count", 0),
        "value_gap_count": gap_report.get("gap_count", 0),
        "highest_value_capability_count": len(capability_value.get("highest_value_capabilities") or []),
        "highest_value_journey_count": len(journey_value.get("highest_value_journeys") or []),
        "successful_customers": success_outcome.get("successful_customers", 0),
        "partially_successful_customers": success_outcome.get("partially_successful_customers", 0),
        "unsuccessful_customers": success_outcome.get("unsuccessful_customers", 0),
        "value_realization_level": scorecard.get("overall_level", "UNKNOWN"),
        "value_realization_score": scorecard.get("overall_score", 0),
        "value_opportunity_count": opportunity_registry.get("count", 0),
        "core_principle": VALUE_REALIZATION_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_customer_success_forbidden": True,
    }

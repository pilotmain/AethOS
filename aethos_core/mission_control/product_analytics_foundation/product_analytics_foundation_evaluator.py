# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — product analytics evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
    ANALYTICS_CORE_PRINCIPLE,
    CANONICAL_ANALYTICS_EVENTS,
    JOURNEY_STAGES,
    PRIVACY_PRINCIPLES,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evidence import (
    _section_block,
)


def build_analytics_event_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    tenant = evidence.get("fix_300") or {}
    onboarding = evidence.get("fix_301") or {}
    provider = evidence.get("fix_303") or {}
    beta = evidence.get("fix_312") or {}
    tenant_dashboard = _section_block(tenant, "tenant_dashboard")
    progress = _section_block(onboarding, "onboarding_progress_registry")
    provider_dashboard = _section_block(provider, "provider_connection_dashboard")

    event_counts = {
        "organization_created": tenant_dashboard.get("organization_count", 0),
        "workspace_created": tenant_dashboard.get("workspace_count", 0),
        "project_registered": tenant_dashboard.get("project_count", 0),
        "provider_connected": provider_dashboard.get("connected_provider_count", 0),
        "onboarding_completed": progress.get("completed_steps_count") or progress.get("completed_count") or 0,
        "beta_admitted": _section_block(beta, "beta_cohort_registry").get("admitted_count", 0),
        "launch_review_completed": progress.get("launch_review_completed_count", 0),
    }

    events = []
    for name in CANONICAL_ANALYTICS_EVENTS:
        events.append(
            {
                "event": name,
                "count": event_counts.get(name, 0),
                "tenant_scoped": True,
                "message_content_analysis_forbidden": True,
            }
        )

    return {
        "events": events,
        "canonical_events": list(CANONICAL_ANALYTICS_EVENTS),
        "privacy_principles": list(PRIVACY_PRINCIPLES),
        "cross_tenant_analytics_forbidden": True,
        "validated": bool(tenant or onboarding or provider),
    }


def build_user_journey_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    tenant = evidence.get("fix_300") or {}
    onboarding = evidence.get("fix_301") or {}
    support = evidence.get("fix_310") or {}
    billing = evidence.get("fix_305") or {}
    tenant_dashboard = _section_block(tenant, "tenant_dashboard")
    progress = _section_block(onboarding, "onboarding_progress_registry")
    customer_health = _section_block(support, "customer_health_registry")
    subscription = _section_block(billing, "subscription_registry")

    org_count = int(tenant_dashboard.get("organization_count") or 0)
    completed = int(progress.get("completed_steps_count") or progress.get("completed_count") or 0)
    started = int(progress.get("started_count") or org_count or 1)
    completion_rate = round((completed / started) * 100, 1) if started else 0.0

    stages = {
        "entry": {"organizations": org_count, "users": tenant_dashboard.get("user_count", 0)},
        "activation": {
            "onboarding_started": started,
            "onboarding_completed": completed,
            "completion_rate_percent": completion_rate,
        },
        "adoption": {
            "healthy_customers": customer_health.get("healthy_count", 0),
            "active_projects": tenant_dashboard.get("project_count", 0),
        },
        "retention": {
            "at_risk_customers": customer_health.get("at_risk_count", 0),
            "retained_subscriptions": len(subscription.get("active_subscriptions") or []),
        },
        "expansion": {
            "upgrade_candidates": len(_section_block(billing, "usage_registry").get("expansion_candidates") or []),
            "beta_participants": _section_block(evidence.get("fix_312") or {}, "beta_cohort_registry").get(
                "participant_count", 0
            ),
        },
    }

    return {
        "journey_stages": list(JOURNEY_STAGES),
        "stages": stages,
        "success_predictors": [
            "onboarding_completed",
            "provider_connected",
            "mission_control_activation",
            "healthy_customer_status",
        ],
        "tenant_isolation_preserved": True,
        "validated": bool(stages["entry"]["organizations"] or stages["activation"]["onboarding_started"]),
    }


def build_onboarding_analytics_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    onboarding = evidence.get("fix_301") or {}
    progress = _section_block(onboarding, "onboarding_progress_registry")
    steps = list(progress.get("steps") or progress.get("onboarding_steps") or [])
    incomplete = list(progress.get("incomplete_steps") or progress.get("pending_steps") or [])
    completed = int(progress.get("completed_steps_count") or progress.get("completed_count") or 0)
    started = int(progress.get("started_count") or completed + len(incomplete) or 1)
    drop_offs = incomplete or list(progress.get("drop_off_points") or [])

    return {
        "sources": ["FIX 301"],
        "sources_ok": {"fix_301": bool((evidence.get("sources_ok") or {}).get("fix_301"))},
        "step_completion": steps,
        "drop_off_points": drop_offs,
        "average_completion_rate_percent": round((completed / started) * 100, 1) if started else 0.0,
        "users_completed_onboarding": completed,
        "users_started_onboarding": started,
        "validated": bool(onboarding),
    }


def build_capability_usage_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    cap295 = evidence.get("fix_295") or {}
    cap296 = evidence.get("fix_296") or {}
    registry = _section_block(cap295, "capability_registry")
    capabilities = list(registry.get("capabilities") or [])
    proven = _section_block(cap296, "proven_capabilities")
    operational = _section_block(cap296, "operational_capabilities")
    experimental = _section_block(cap296, "experimental_capabilities")
    planned = _section_block(cap296, "planned_blocked_capabilities")

    used = list(proven.get("items") or []) + list(operational.get("items") or [])
    ignored = list(planned.get("items") or [])
    confusing = list(experimental.get("items") or [])[:6]

    return {
        "sources": ["FIX 295", "FIX 296"],
        "sources_ok": {
            "fix_295": bool((evidence.get("sources_ok") or {}).get("fix_295")),
            "fix_296": bool((evidence.get("sources_ok") or {}).get("fix_296")),
        },
        "capabilities_used": used[:12],
        "capabilities_ignored": ignored[:12],
        "capabilities_confusing": confusing,
        "capability_count": registry.get("capability_count", len(capabilities)),
        "validated": bool(used or capabilities),
    }


def build_provider_analytics_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    provider = evidence.get("fix_303") or {}
    dashboard = _section_block(provider, "provider_connection_dashboard")
    reports = provider.get("sections", {}).get("provider_connection_reports") or []

    adoption = {
        "github": 0,
        "railway": 0,
        "vercel": 0,
    }
    readiness_failures: list[str] = []
    for row in reports:
        if not isinstance(row, dict):
            continue
        name = str(row.get("provider") or "").lower()
        if name in adoption:
            adoption[name] = int(row.get("connected_count") or row.get("connection_count") or 0)
        readiness = str(row.get("readiness") or row.get("status") or "")
        if readiness in {"not_configured", "partial", "failed"}:
            readiness_failures.append(f"{name}: {readiness}")

    if not any(adoption.values()):
        connected = int(dashboard.get("connected_provider_count") or 0)
        adoption["github"] = connected

    most_connected = max(adoption, key=adoption.get) if any(adoption.values()) else None

    return {
        "sources": ["FIX 303"],
        "sources_ok": {"fix_303": bool((evidence.get("sources_ok") or {}).get("fix_303"))},
        "provider_adoption": adoption,
        "most_connected_provider": most_connected,
        "readiness_failures": readiness_failures[:8],
        "connected_provider_count": dashboard.get("connected_provider_count", 0),
        "validated": bool(provider),
    }


def build_commercial_analytics_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    billing = evidence.get("fix_305") or {}
    payment = evidence.get("fix_308") or {}
    plans = _section_block(billing, "plan_registry")
    subscriptions = _section_block(billing, "subscription_registry")
    entitlements = _section_block(billing, "entitlement_registry")
    upgrade_paths = _section_block(payment, "upgrade_path_registry")
    commercial_dashboard = _section_block(payment, "commercial_analytics_dashboard")

    plan_adoption = list(plans.get("plans") or plans.get("items") or [])
    active_subscriptions = list(subscriptions.get("active_subscriptions") or subscriptions.get("items") or [])
    utilization = entitlements.get("utilization_summary") or entitlements.get("usage_summary")

    return {
        "sources": ["FIX 305", "FIX 308"],
        "sources_ok": {
            "fix_305": bool((evidence.get("sources_ok") or {}).get("fix_305")),
            "fix_308": bool((evidence.get("sources_ok") or {}).get("fix_308")),
        },
        "plan_adoption": plan_adoption[:8],
        "most_successful_plans": commercial_dashboard.get("top_plans") or plan_adoption[:3],
        "upgrade_paths": list(upgrade_paths.get("paths") or upgrade_paths.get("items") or [])[:8],
        "entitlement_utilization": utilization,
        "active_subscription_count": len(active_subscriptions),
        "validated": bool(billing or payment),
    }


def build_customer_success_analytics_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    support = evidence.get("fix_310") or {}
    beta = evidence.get("fix_312") or {}
    health = _section_block(support, "customer_health_registry")
    risk = _section_block(support, "customer_risk_registry")
    adoption = _section_block(support, "customer_adoption_report")
    beta_metrics = _section_block(beta, "beta_success_metrics")

    return {
        "sources": ["FIX 310", "FIX 312"],
        "sources_ok": {
            "fix_310": bool((evidence.get("sources_ok") or {}).get("fix_310")),
            "fix_312": bool((evidence.get("sources_ok") or {}).get("fix_312")),
        },
        "healthy_customers": health.get("healthy_count", 0),
        "at_risk_customers": risk.get("at_risk_count", 0),
        "engagement_trends": adoption.get("trends") or adoption.get("engagement_trend"),
        "beta_engagement": beta_metrics,
        "validated": bool(support or beta),
    }


def build_behavioral_opportunity_registry(
    *,
    onboarding_report: dict[str, Any],
    capability_report: dict[str, Any],
    provider_report: dict[str, Any],
    journey_report: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    completion_rate = float(onboarding_report.get("average_completion_rate_percent") or 0)
    if completion_rate < 70:
        opportunities.append(
            {
                "opportunity_id": "high-onboarding-drop-off",
                "signal": "high_onboarding_drop_off",
                "detail": f"Onboarding completion rate is {completion_rate}%.",
                "source": "onboarding_analytics_report",
                "automatic_behavior_modification_forbidden": True,
            }
        )

    for point in onboarding_report.get("drop_off_points") or []:
        opportunities.append(
            {
                "opportunity_id": f"onboarding-drop-off-{str(point)[:32]}",
                "signal": "onboarding_drop_off_point",
                "detail": f"Users drop off at: {point}",
                "source": "onboarding_analytics_report",
                "automatic_behavior_modification_forbidden": True,
            }
        )

    connected = int(provider_report.get("connected_provider_count") or 0)
    if connected == 0:
        opportunities.append(
            {
                "opportunity_id": "low-provider-connection-completion",
                "signal": "low_provider_connection_completion",
                "detail": "No provider connections recorded in tenant-scoped analytics.",
                "source": "provider_analytics_report",
                "automatic_behavior_modification_forbidden": True,
            }
        )

    if capability_report.get("capabilities_ignored"):
        opportunities.append(
            {
                "opportunity_id": "unused-capabilities",
                "signal": "unused_capabilities",
                "detail": "Capabilities exist but show low or no adoption signals.",
                "source": "capability_usage_report",
                "automatic_behavior_modification_forbidden": True,
            }
        )

    predictors = journey_report.get("success_predictors") or []
    if predictors:
        opportunities.append(
            {
                "opportunity_id": "success-behavior-predictors",
                "signal": "success_predictors_identified",
                "detail": f"Behaviors associated with success: {', '.join(predictors)}",
                "source": "user_journey_report",
                "automatic_behavior_modification_forbidden": True,
            }
        )

    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "core_principle": ANALYTICS_CORE_PRINCIPLE,
    }

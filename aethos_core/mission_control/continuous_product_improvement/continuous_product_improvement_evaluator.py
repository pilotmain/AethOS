# SPDX-License-Identifier: Apache-2.0
"""FIX 317 — improvement intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_contract import (
    EFFORT_LEVELS,
    IMPACT_LEVELS,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_evidence import (
    _section_block,
)


def _opportunity(
    *,
    opportunity_id: str,
    title: str,
    recommendation: str,
    source: str,
    affected_areas: list[str],
    impact: str = "medium",
    effort: str = "medium",
    confidence: float = 0.75,
) -> dict[str, Any]:
    return {
        "opportunity_id": opportunity_id,
        "title": title,
        "recommendation": recommendation,
        "source": source,
        "affected_areas": affected_areas,
        "impact": impact if impact in IMPACT_LEVELS else "medium",
        "effort": effort if effort in EFFORT_LEVELS else "medium",
        "confidence": round(max(0.0, min(float(confidence), 1.0)), 2),
        "automatic_execution_forbidden": True,
    }


def _blocker_opportunities(
    *,
    blockers: list[Any],
    source: str,
    affected_areas: list[str],
    prefix: str,
    impact: str = "high",
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    for index, blocker in enumerate(blockers[:8]):
        text = str(blocker)
        opportunities.append(
            _opportunity(
                opportunity_id=f"{prefix}-{index + 1}",
                title=text[:120],
                recommendation=f"Review and address blocker: {text}",
                source=source,
                affected_areas=affected_areas,
                impact=impact,
                effort="medium",
                confidence=0.85,
            )
        )
    return opportunities


def build_feedback_intelligence_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    support = evidence.get("fix_310") or {}
    beta = evidence.get("fix_312") or {}
    support_dashboard = _section_block(support, "customer_support_success_dashboard")
    risk_registry = _section_block(support, "customer_risk_registry")
    beta_feedback = _section_block(beta, "beta_feedback_registry")
    opportunities = _blocker_opportunities(
        blockers=list(support.get("blockers") or []),
        source="FIX 310",
        affected_areas=["customer_support", "customer_success"],
        prefix="feedback-support",
    )
    opportunities.extend(
        _blocker_opportunities(
            blockers=list(beta.get("blockers") or []),
            source="FIX 312",
            affected_areas=["beta_program", "customer_feedback"],
            prefix="feedback-beta",
        )
    )
    feedback_items = list(beta_feedback.get("feedback_items") or beta_feedback.get("items") or [])[:6]
    for index, item in enumerate(feedback_items):
        opportunities.append(
            _opportunity(
                opportunity_id=f"feedback-item-{index + 1}",
                title=str(item)[:120],
                recommendation="Incorporate beta feedback into human-reviewed improvement backlog.",
                source="FIX 312",
                affected_areas=["beta_feedback", "product"],
                impact="medium",
                effort="low",
                confidence=0.8,
            )
        )

    return {
        "sources": ["FIX 310", "FIX 312"],
        "sources_ok": {
            "fix_310": bool((evidence.get("sources_ok") or {}).get("fix_310")),
            "fix_312": bool((evidence.get("sources_ok") or {}).get("fix_312")),
        },
        "customer_feedback_signals": feedback_items,
        "support_observations": {
            "at_risk_count": risk_registry.get("at_risk_count"),
            "healthy_count": risk_registry.get("healthy_count"),
            "evidence_coverage": support_dashboard.get("evidence_coverage"),
        },
        "opportunities": opportunities,
        "validated": bool(opportunities or support or beta),
    }


def build_onboarding_improvement_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    onboarding = evidence.get("fix_301") or {}
    tenant = evidence.get("fix_300") or {}
    progress = _section_block(onboarding, "onboarding_progress_registry")
    checklist = _section_block(onboarding, "provider_connection_checklist")
    tenant_onboarding = _section_block(tenant, "tenant_onboarding_registry")
    opportunities: list[dict[str, Any]] = []

    incomplete_steps = list(progress.get("incomplete_steps") or progress.get("pending_steps") or [])[:6]
    for index, step in enumerate(incomplete_steps):
        opportunities.append(
            _opportunity(
                opportunity_id=f"onboarding-step-{index + 1}",
                title=f"Onboarding friction: {step}",
                recommendation="Reduce friction in onboarding step and clarify next action for operators.",
                source="FIX 301",
                affected_areas=["onboarding", "activation"],
                impact="high",
                effort="medium",
                confidence=0.82,
            )
        )

    if checklist.get("missing_providers") or checklist.get("pending_connections"):
        opportunities.append(
            _opportunity(
                opportunity_id="onboarding-provider-friction",
                title="Provider connection friction during onboarding",
                recommendation="Improve provider connection guidance and readiness checks during onboarding.",
                source="FIX 301",
                affected_areas=["onboarding", "provider_connection"],
                impact="high",
                effort="medium",
                confidence=0.78,
            )
        )

    if tenant_onboarding.get("pending_tenants") or tenant_onboarding.get("abandoned_onboarding"):
        opportunities.append(
            _opportunity(
                opportunity_id="onboarding-abandonment",
                title="Onboarding abandonment detected in tenant foundation evidence",
                recommendation="Investigate abandonment points and simplify tenant setup path.",
                source="FIX 300",
                affected_areas=["onboarding", "tenant_foundation"],
                impact="high",
                effort="high",
                confidence=0.7,
            )
        )

    return {
        "sources": ["FIX 300", "FIX 301"],
        "sources_ok": {
            "fix_300": bool((evidence.get("sources_ok") or {}).get("fix_300")),
            "fix_301": bool((evidence.get("sources_ok") or {}).get("fix_301")),
        },
        "onboarding_completion": progress.get("completion_rate") or progress.get("completed_steps"),
        "onboarding_abandonment_signals": progress.get("abandoned_steps") or incomplete_steps,
        "friction_points": incomplete_steps,
        "opportunities": opportunities,
        "validated": bool(opportunities or onboarding or tenant),
    }


def build_product_experience_improvement_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    product = evidence.get("fix_311") or {}
    dashboard = _section_block(product, "public_product_dashboard")
    capability_explorer = _section_block(product, "capability_explorer")
    trust_explorer = _section_block(product, "trust_explorer")
    opportunities: list[dict[str, Any]] = []

    if capability_explorer.get("confusion_points") or capability_explorer.get("gaps"):
        opportunities.append(
            _opportunity(
                opportunity_id="product-capability-confusion",
                title="Capability confusion in public product experience",
                recommendation="Clarify capability boundaries and maturity labels in the product explorer.",
                source="FIX 311",
                affected_areas=["product_experience", "capabilities"],
                impact="medium",
                effort="low",
                confidence=0.8,
            )
        )

    if trust_explorer.get("confusion_points") or trust_explorer.get("gaps"):
        opportunities.append(
            _opportunity(
                opportunity_id="product-trust-confusion",
                title="Trust confusion in public product experience",
                recommendation="Improve trust explorer copy and evidence links for human review.",
                source="FIX 311",
                affected_areas=["product_experience", "trust"],
                impact="medium",
                effort="low",
                confidence=0.8,
            )
        )

    if dashboard.get("navigation_friction") or dashboard.get("launch_status") in {"BLOCKED", "ATTENTION"}:
        opportunities.append(
            _opportunity(
                opportunity_id="product-navigation-friction",
                title="Navigation or readiness friction in public product journey",
                recommendation="Streamline public journey paths and highlight next best actions.",
                source="FIX 311",
                affected_areas=["product_experience", "navigation"],
                impact="medium",
                effort="medium",
                confidence=0.72,
            )
        )

    return {
        "sources": ["FIX 311"],
        "sources_ok": {"fix_311": bool((evidence.get("sources_ok") or {}).get("fix_311"))},
        "capability_confusion_signals": capability_explorer.get("confusion_points") or capability_explorer.get("gaps"),
        "trust_confusion_signals": trust_explorer.get("confusion_points") or trust_explorer.get("gaps"),
        "navigation_friction_signals": dashboard.get("navigation_friction"),
        "opportunities": opportunities,
        "validated": bool(opportunities or product),
    }


def build_operational_improvement_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    monitoring = evidence.get("fix_220") or {}
    rollback = evidence.get("fix_230") or {}
    launch_ops = evidence.get("fix_313") or {}
    opportunities: list[dict[str, Any]] = []
    opportunities.extend(
        _blocker_opportunities(
            blockers=list(monitoring.get("blockers") or []),
            source="FIX 220",
            affected_areas=["operations", "monitoring"],
            prefix="ops-monitoring",
        )
    )
    opportunities.extend(
        _blocker_opportunities(
            blockers=list(rollback.get("blockers") or []),
            source="FIX 230",
            affected_areas=["operations", "rollback"],
            prefix="ops-rollback",
        )
    )
    opportunities.extend(
        _blocker_opportunities(
            blockers=list(launch_ops.get("blockers") or []),
            source="FIX 313",
            affected_areas=["operations", "launch"],
            prefix="ops-launch",
        )
    )
    launch_blockers = _section_block(launch_ops, "launch_blocker_registry")
    for index, item in enumerate(list(launch_blockers.get("blockers") or launch_blockers.get("items") or [])[:6]):
        opportunities.append(
            _opportunity(
                opportunity_id=f"ops-recurring-{index + 1}",
                title=f"Recurring operational blocker: {item}",
                recommendation="Review recurring launch/operations blocker and propose human-approved remediation.",
                source="FIX 313",
                affected_areas=["operations", "launch_blockers"],
                impact="high",
                effort="medium",
                confidence=0.84,
            )
        )

    return {
        "sources": ["FIX 220", "FIX 230", "FIX 313"],
        "sources_ok": {
            key: bool((evidence.get("sources_ok") or {}).get(key))
            for key in ("fix_220", "fix_230", "fix_313")
        },
        "recurring_incidents": _section_block(monitoring, "incident_detection").get("recurring_incidents"),
        "recurring_blockers": launch_blockers.get("blockers") or launch_blockers.get("items"),
        "operational_bottlenecks": list(launch_ops.get("blockers") or [])[:6],
        "opportunities": opportunities,
        "validated": bool(opportunities or monitoring or rollback or launch_ops),
    }


def build_governance_improvement_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    auth = evidence.get("fix_302") or {}
    audit = evidence.get("fix_307") or {}
    least_privilege = _section_block(auth, "least_privilege_report")
    boundary_audit = _section_block(auth, "tenant_boundary_audit")
    governance_timeline = _section_block(audit, "governance_timeline")
    opportunities: list[dict[str, Any]] = []

    if least_privilege.get("gaps") or least_privilege.get("findings"):
        opportunities.append(
            _opportunity(
                opportunity_id="governance-least-privilege",
                title="Least-privilege or approval bottleneck detected",
                recommendation="Review authorization bottlenecks and simplify human approval paths.",
                source="FIX 302",
                affected_areas=["governance", "authorization"],
                impact="high",
                effort="medium",
                confidence=0.8,
            )
        )

    if boundary_audit.get("findings") or boundary_audit.get("violations"):
        opportunities.append(
            _opportunity(
                opportunity_id="governance-boundary-audit",
                title="Tenant boundary audit findings require review",
                recommendation="Address tenant boundary findings through human governance review.",
                source="FIX 302",
                affected_areas=["governance", "tenant_boundary"],
                impact="high",
                effort="high",
                confidence=0.78,
            )
        )

    delayed_reviews = list(governance_timeline.get("delayed_reviews") or governance_timeline.get("items") or [])[:6]
    for index, item in enumerate(delayed_reviews):
        opportunities.append(
            _opportunity(
                opportunity_id=f"governance-delay-{index + 1}",
                title=f"Governance review delay: {item}",
                recommendation="Reduce review delays while preserving human authority over decisions.",
                source="FIX 307",
                affected_areas=["governance", "review_delays"],
                impact="medium",
                effort="medium",
                confidence=0.76,
            )
        )

    return {
        "sources": ["FIX 302", "FIX 307"],
        "sources_ok": {
            "fix_302": bool((evidence.get("sources_ok") or {}).get("fix_302")),
            "fix_307": bool((evidence.get("sources_ok") or {}).get("fix_307")),
        },
        "approval_bottlenecks": least_privilege.get("gaps") or least_privilege.get("findings"),
        "review_delays": delayed_reviews,
        "governance_friction_signals": boundary_audit.get("findings") or boundary_audit.get("violations"),
        "opportunities": opportunities,
        "validated": bool(opportunities or auth or audit),
    }


def build_commercial_improvement_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    billing = evidence.get("fix_305") or {}
    payment = evidence.get("fix_308") or {}
    usage_limits = _section_block(billing, "usage_limit_report")
    billing_readiness = _section_block(billing, "billing_readiness_report")
    upgrade_paths = _section_block(payment, "upgrade_path_registry")
    commercial_governance = _section_block(payment, "commercial_governance_report")
    opportunities: list[dict[str, Any]] = []

    if usage_limits.get("limits_reached") or usage_limits.get("friction_points"):
        opportunities.append(
            _opportunity(
                opportunity_id="commercial-usage-friction",
                title="Usage limit or entitlement friction detected",
                recommendation="Clarify plan limits and upgrade paths for customers experiencing friction.",
                source="FIX 305",
                affected_areas=["commercial", "entitlements"],
                impact="medium",
                effort="low",
                confidence=0.79,
            )
        )

    if billing_readiness.get("blockers") or billing_readiness.get("gaps"):
        opportunities.append(
            _opportunity(
                opportunity_id="commercial-billing-readiness",
                title="Billing readiness gaps affecting commercial experience",
                recommendation="Close billing readiness gaps through human-reviewed commercial changes.",
                source="FIX 305",
                affected_areas=["commercial", "billing"],
                impact="high",
                effort="medium",
                confidence=0.77,
            )
        )

    upgrade_items = list(upgrade_paths.get("paths") or upgrade_paths.get("items") or [])[:6]
    for index, item in enumerate(upgrade_items):
        opportunities.append(
            _opportunity(
                opportunity_id=f"commercial-upgrade-{index + 1}",
                title=f"Upgrade opportunity: {item}",
                recommendation="Evaluate upgrade path clarity and reduce plan friction for operators.",
                source="FIX 308",
                affected_areas=["commercial", "upgrade_paths"],
                impact="medium",
                effort="low",
                confidence=0.74,
            )
        )

    if commercial_governance.get("findings") or commercial_governance.get("confusion_points"):
        opportunities.append(
            _opportunity(
                opportunity_id="commercial-entitlement-confusion",
                title="Entitlement or commercial governance confusion",
                recommendation="Improve entitlement messaging and commercial governance clarity.",
                source="FIX 308",
                affected_areas=["commercial", "entitlements"],
                impact="medium",
                effort="medium",
                confidence=0.75,
            )
        )

    return {
        "sources": ["FIX 305", "FIX 308"],
        "sources_ok": {
            "fix_305": bool((evidence.get("sources_ok") or {}).get("fix_305")),
            "fix_308": bool((evidence.get("sources_ok") or {}).get("fix_308")),
        },
        "upgrade_opportunities": upgrade_items,
        "plan_friction_signals": usage_limits.get("friction_points") or usage_limits.get("limits_reached"),
        "entitlement_confusion_signals": commercial_governance.get("confusion_points") or commercial_governance.get("findings"),
        "opportunities": opportunities,
        "validated": bool(opportunities or billing or payment),
    }


def build_improvement_opportunity_registry(*, reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []
    for report in reports.values():
        opportunities.extend(list(report.get("opportunities") or []))

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for opp in opportunities:
        key = str(opp.get("opportunity_id") or opp.get("title"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(opp)

    return {
        "opportunities": deduped,
        "count": len(deduped),
        "automatic_backlog_creation_forbidden": True,
    }


def _priority_score(opportunity: dict[str, Any]) -> float:
    impact_scores = {"high": 3.0, "medium": 2.0, "low": 1.0}
    effort_scores = {"low": 3.0, "medium": 2.0, "high": 1.0}
    impact = impact_scores.get(str(opportunity.get("impact") or "medium"), 2.0)
    effort = effort_scores.get(str(opportunity.get("effort") or "medium"), 2.0)
    confidence = float(opportunity.get("confidence") or 0.5)
    strategic = 1.0 if "launch" in " ".join(opportunity.get("affected_areas") or []) else 0.0
    return round(impact * 2.0 + effort + confidence + strategic, 3)


def build_improvement_priority_matrix(*, registry: dict[str, Any]) -> dict[str, Any]:
    ranked = []
    for opp in list(registry.get("opportunities") or []):
        ranked.append({**opp, "priority_score": _priority_score(opp)})
    ranked.sort(key=lambda row: row["priority_score"], reverse=True)

    return {
        "ranked_opportunities": ranked[:12],
        "high_impact_low_effort": [
            row for row in ranked if row.get("impact") == "high" and row.get("effort") == "low"
        ][:6],
        "strategic_value_leaders": ranked[:5],
        "ranking_model": "impact_x2 + inverse_effort + confidence + launch_strategic_bonus",
        "automatic_execution_forbidden": True,
    }

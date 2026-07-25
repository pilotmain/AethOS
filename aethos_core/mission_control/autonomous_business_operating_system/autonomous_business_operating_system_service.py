# SPDX-License-Identifier: Apache-2.0
"""FIX 290 — autonomous business operating system service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_290_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_service import (
    build_autonomous_application_lifecycle_management,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_contract import (
    AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290,
    AUTONOMOUS_BUSINESS_OPERATING_COMPOSES_EVIDENCE_ONLY_FIX_290,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_FIX,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_INVARIANT,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_PRINCIPLES,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_SCHEMA_VERSION,
    BILLING_AUTHORITY_FIX_290,
    BUSINESS_AUTHORITY_FIX_290,
    BUSINESS_DOMAINS,
    BUSINESS_HEALTH_DIMENSIONS,
    BUSINESS_RISK_DIMENSIONS,
    CUSTOMER_MUTATION_AUTHORITY_FIX_290,
    DEPLOYMENT_AUTHORITY_FIX_290,
    EXECUTION_PERFORMED_FIX_290,
    FORBIDDEN_BUSINESS_OPERATING_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_290,
    GOVERNANCE_MUTATION_PERFORMED_FIX_290,
    MERGE_AUTHORITY_FIX_290,
    MUTATION_PERFORMED_FIX_290,
    PROVIDER_MUTATION_AUTHORITY_FIX_290,
    REPOSITORY_MUTATION_AUTHORITY_FIX_290,
    ROLLBACK_AUTHORITY_FIX_290,
    TRUST_MUTATION_AUTHORITY_FIX_290,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_store import (
    has_human_business_decision_approve,
    list_autonomous_business_operating_system_records,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_service import (
    build_governed_application_generation,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)

_DOMAIN_NOTE_KIND: dict[str, str] = {
    "product_domain_note": "product",
    "customer_domain_note": "customer",
    "revenue_domain_note": "revenue",
    "team_domain_note": "team",
    "project_domain_note": "project",
    "operational_domain_note": "operational",
}


@dataclass(frozen=True)
class AutonomousBusinessOperatingSystemResult:
    ok: bool
    session_id: str
    autonomous_business_operating_system: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _health_tier(score: float) -> str:
    if score >= 85:
        return "EXCELLENT"
    if score >= 70:
        return "HEALTHY"
    if score >= 50:
        return "WATCH"
    if score >= 30:
        return "AT_RISK"
    return "UNPROVEN"


def _risk_tier(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "ELEVATED"
    if score >= 30:
        return "MODERATE"
    return "LOW"


def _domain_records(
    *,
    domain: str,
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        r
        for r in business_records
        if r.get("business_domain") == domain
        or _DOMAIN_NOTE_KIND.get(str(r.get("kind") or "")) == domain
    ]


def _product_portfolio_registry(
    *,
    generation: dict[str, Any],
    lifecycle_sections: dict[str, Any],
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gen_sections = generation.get("sections") or {}
    product = (gen_sections.get("product_understanding_package") or [{}])[0]
    product_name = str(generation.get("product_name") or "portfolio")
    evolution_opps = (
        (lifecycle_sections.get("lifecycle_opportunity_registry") or [{}])[0].get("opportunities") or []
    )
    domain_records = _domain_records(domain="product", business_records=business_records)
    return [
        {
            "registry_id": "product-portfolio-registry",
            "product_name": product_name,
            "products": [product_name] if product.get("present") else [],
            "roadmap_signals": list(product.get("goals") or [])[:5] if product.get("present") else [],
            "feature_signals": [
                stage.get("stage")
                for stage in (lifecycle_sections.get("lifecycle_stage_registry") or [])
                if stage.get("stage") in {"product_design", "delivery", "evolution"}
            ],
            "evolution_opportunity_count": len(
                [o for o in evolution_opps if o.get("source_fix") in {"FIX 261", "FIX 270"}]
            ),
            "operator_note_count": len(domain_records),
            "read_only": True,
        }
    ]


def _customer_intelligence_registry(
    *,
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    domain_records = _domain_records(domain="customer", business_records=business_records)
    insight_records = [r for r in business_records if r.get("kind") == "customer_insight_note"]
    return [
        {
            "registry_id": "customer-intelligence-registry",
            "segment_count": len({r.get("content", "")[:40] for r in domain_records}) or 0,
            "feedback_items": [r.get("content") for r in domain_records[-10:]],
            "pain_points": [r.get("content") for r in insight_records if "pain" in str(r.get("content", "")).lower()],
            "request_count": len(domain_records) + len(insight_records),
            "operator_note_count": len(domain_records) + len(insight_records),
            "read_only": True,
        }
    ]


def _revenue_intelligence_registry(
    *,
    engineering_sections: dict[str, Any],
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    portfolio_summary = dict(
        ((engineering_sections.get("portfolio_engineering_dashboard") or [{}])[0]).get("portfolio_summary") or {}
    )
    domain_records = _domain_records(domain="revenue", business_records=business_records)
    revenue_observations = [r for r in business_records if r.get("kind") == "revenue_observation_note"]
    growth_score = float(portfolio_summary.get("portfolio_engineering_health_score") or 0)
    return [
        {
            "registry_id": "revenue-intelligence-registry",
            "growth_signal_tier": _health_tier(growth_score),
            "usage_signals": [f"portfolio_health:{growth_score}"],
            "commercial_opportunity_count": len(domain_records) + len(revenue_observations),
            "observations": [r.get("content") for r in revenue_observations[-5:]],
            "operator_note_count": len(domain_records) + len(revenue_observations),
            "read_only": True,
        }
    ]


def _team_operating_registry(
    *,
    business_records: list[dict[str, Any]],
    lifecycle_sections: dict[str, Any],
) -> list[dict[str, Any]]:
    domain_records = _domain_records(domain="team", business_records=business_records)
    decision_records = [
        r
        for r in business_records
        if str(r.get("kind") or "").startswith("human_business_decision_")
    ]
    human_review = (lifecycle_sections.get("human_lifecycle_review") or [{}])[0]
    return [
        {
            "registry_id": "team-operating-registry",
            "ownership_notes": [r.get("content") for r in domain_records[-5:]],
            "decision_history_count": len(decision_records),
            "approval_capacity_signal": "available" if human_review.get("execution_authority") is False else "unknown",
            "operator_note_count": len(domain_records),
            "read_only": True,
        }
    ]


def _project_portfolio_registry(
    *,
    delivery_rows: list[dict[str, Any]],
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    domain_records = _domain_records(domain="project", business_records=business_records)
    projects = [
        {
            "project_id": row.get("repository"),
            "display_name": row.get("display_name") or row.get("repository"),
            "milestone_stages": list(row.get("live_evidence_stages") or []),
            "visibility": row.get("program_visibility"),
        }
        for row in delivery_rows
    ]
    return [
        {
            "registry_id": "project-portfolio-registry",
            "project_count": len(projects),
            "projects": projects[:10],
            "initiative_notes": [r.get("content") for r in domain_records[-5:]],
            "operator_note_count": len(domain_records),
            "read_only": True,
        }
    ]


def _business_operations_registry(
    *,
    lifecycle_sections: dict[str, Any],
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    domain_records = _domain_records(domain="operational", business_records=business_records)
    dashboard = (lifecycle_sections.get("lifecycle_management_dashboard") or [{}])[0]
    return [
        {
            "registry_id": "business-operations-registry",
            "deployment_status": dashboard.get("delivery_status"),
            "operational_status": dashboard.get("operational_status"),
            "recovery_status": dashboard.get("recovery_status"),
            "incident_notes": [r.get("content") for r in domain_records[-5:]],
            "operator_note_count": len(domain_records),
            "read_only": True,
        }
    ]


def _business_goal_registry(
    *,
    generation: dict[str, Any],
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gen_sections = generation.get("sections") or {}
    product = (gen_sections.get("product_understanding_package") or [{}])[0]
    goal_records = [r for r in business_records if r.get("kind") == "business_goal_note"]
    objectives: list[dict[str, Any]] = []
    if product.get("present"):
        for idx, goal in enumerate(list(product.get("goals") or [])[:5], start=1):
            objectives.append(
                {
                    "objective_id": f"inferred-goal-{idx}",
                    "title": str(goal),
                    "source": "fix_250_product_understanding",
                    "read_only": True,
                }
            )
    for idx, record in enumerate(goal_records, start=1):
        objectives.append(
            {
                "objective_id": record.get("goal_id") or f"operator-goal-{idx}",
                "title": record.get("content"),
                "source": "operator_business_goal_note",
                "read_only": True,
            }
        )
    return [
        {
            "registry_id": "business-goal-registry",
            "objective_count": len(objectives),
            "objectives": objectives,
            "key_result_signals": [o.get("title") for o in objectives[:3]],
            "read_only": True,
        }
    ]


def _strategic_alignment_graph(
    *,
    goals: list[dict[str, Any]],
    delivery_rows: list[dict[str, Any]],
    lifecycle_sections: dict[str, Any],
    product_name: str,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for goal in goals[:5]:
        goal_id = str(goal.get("objective_id") or "goal")
        nodes.append({"node_id": goal_id, "node_type": "business_goal", "label": goal.get("title")})
        initiative_id = f"initiative-{goal_id}"
        nodes.append(
            {
                "node_id": initiative_id,
                "node_type": "initiative",
                "label": f"Initiative supporting {goal.get('title', 'goal')}",
            }
        )
        edges.append({"from": goal_id, "to": initiative_id, "relation": "drives"})
        project_id = f"project-{product_name.replace(' ', '-').lower()}"
        nodes.append({"node_id": project_id, "node_type": "project", "label": product_name})
        edges.append({"from": initiative_id, "to": project_id, "relation": "funds"})
        edges.append({"from": project_id, "to": "product-portfolio", "relation": "delivers"})

    nodes.append({"node_id": "product-portfolio", "node_type": "product", "label": product_name})
    for row in delivery_rows[:4]:
        repo = str(row.get("repository") or "repo")
        feature_id = f"feature-{repo}"
        work_id = f"delivery-{repo}"
        nodes.append({"node_id": feature_id, "node_type": "feature", "label": row.get("display_name") or repo})
        nodes.append({"node_id": work_id, "node_type": "delivery_work", "label": f"Delivery work for {repo}"})
        edges.append({"from": "product-portfolio", "to": feature_id, "relation": "includes"})
        edges.append({"from": feature_id, "to": work_id, "relation": "requires"})

    stage = (lifecycle_sections.get("lifecycle_management_dashboard") or [{}])[0].get(
        "current_lifecycle_stage"
    )
    return [
        {
            "graph_id": "strategic-alignment-graph",
            "current_lifecycle_stage": stage,
            "node_count": len({n["node_id"] for n in nodes}),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "read_only": True,
        }
    ]


def _business_opportunity_portfolio(
    *,
    lifecycle_sections: dict[str, Any],
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    lifecycle_registry = (lifecycle_sections.get("lifecycle_opportunity_registry") or [{}])[0]
    for item in lifecycle_registry.get("opportunities") or []:
        opportunities.append(
            {
                **item,
                "business_domain": "product" if item.get("source_fix") == "FIX 250" else "operational",
            }
        )
    for record in business_records:
        kind = str(record.get("kind") or "")
        if kind == "customer_insight_note":
            opportunities.append(
                {
                    "opportunity_id": record.get("opportunity_id") or f"customer-{record.get('recorded_at')}",
                    "source": "operator_customer_insight",
                    "business_domain": "customer",
                    "title": record.get("content"),
                    "read_only": True,
                }
            )
        elif kind == "revenue_observation_note":
            opportunities.append(
                {
                    "opportunity_id": record.get("opportunity_id") or f"revenue-{record.get('recorded_at')}",
                    "source": "operator_revenue_observation",
                    "business_domain": "revenue",
                    "title": record.get("content"),
                    "read_only": True,
                }
            )
    return [
        {
            "portfolio_id": "business-opportunity-portfolio",
            "opportunity_count": len(opportunities),
            "opportunities": opportunities[:20],
            "read_only": True,
        }
    ]


def _business_health_dashboard(
    *,
    lifecycle_sections: dict[str, Any],
    engineering_sections: dict[str, Any],
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lifecycle_health = (lifecycle_sections.get("lifecycle_health_dashboard") or [{}])[0]
    lifecycle_dims = {
        str(row.get("dimension")): float(row.get("health_score") or 0)
        for row in lifecycle_health.get("dimensions") or []
    }
    portfolio_summary = dict(
        ((engineering_sections.get("portfolio_engineering_dashboard") or [{}])[0]).get("portfolio_summary") or {}
    )
    portfolio_score = float(portfolio_summary.get("portfolio_engineering_health_score") or 0)
    customer_notes = len(_domain_records(domain="customer", business_records=business_records))
    revenue_notes = len(
        [r for r in business_records if r.get("kind") in {"revenue_domain_note", "revenue_observation_note"}]
    )

    dimensions = {
        "product": lifecycle_dims.get("portfolio", portfolio_score),
        "customer": min(100.0, 40.0 + customer_notes * 10),
        "revenue": min(100.0, 35.0 + revenue_notes * 10),
        "delivery": lifecycle_dims.get("delivery", portfolio_score),
        "operational": lifecycle_dims.get("operational", max(0.0, portfolio_score - 10)),
        "portfolio": lifecycle_dims.get("portfolio", portfolio_score),
    }
    rows = [
        {
            "dimension": dim,
            "health_score": round(score, 1),
            "health_tier": _health_tier(score),
            "read_only": True,
        }
        for dim, score in dimensions.items()
        if dim in BUSINESS_HEALTH_DIMENSIONS
    ]
    overall = round(sum(r["health_score"] for r in rows) / len(rows), 1) if rows else 0.0
    return [
        {
            "dashboard_id": "business-health-dashboard",
            "overall_health_score": overall,
            "overall_health_tier": _health_tier(overall),
            "dimensions": rows,
            "read_only": True,
        }
    ]


def _business_risk_dashboard(
    *,
    lifecycle_sections: dict[str, Any],
    business_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lifecycle_risk = (lifecycle_sections.get("lifecycle_risk_dashboard") or [{}])[0]
    lifecycle_dims = {
        str(row.get("dimension")): float(row.get("risk_score") or 0)
        for row in lifecycle_risk.get("dimensions") or []
    }
    customer_gaps = max(0, 3 - len(_domain_records(domain="customer", business_records=business_records)))
    revenue_gaps = max(
        0,
        3
        - len(
            [r for r in business_records if r.get("kind") in {"revenue_domain_note", "revenue_observation_note"}]
        ),
    )
    goal_count = len([r for r in business_records if r.get("kind") == "business_goal_note"])

    dimensions = {
        "delivery": lifecycle_dims.get("delivery", 30.0),
        "operational": lifecycle_dims.get("operational", 25.0),
        "customer": min(100.0, customer_gaps * 20 + 15),
        "revenue": min(100.0, revenue_gaps * 20 + 15),
        "strategic": min(100.0, max(0, 2 - goal_count) * 25 + 20),
    }
    rows = [
        {
            "dimension": dim,
            "risk_score": round(score, 1),
            "risk_tier": _risk_tier(score),
            "read_only": True,
        }
        for dim, score in dimensions.items()
        if dim in BUSINESS_RISK_DIMENSIONS
    ]
    return [
        {
            "dashboard_id": "business-risk-dashboard",
            "overall_risk_tier": _risk_tier(max(r["risk_score"] for r in rows) if rows else 0),
            "dimensions": rows,
            "read_only": True,
        }
    ]


def _business_operating_memory(
    *,
    business_records: list[dict[str, Any]],
    alignment_graph: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "memory_id": "business-operating-memory",
            "goal_count": len([r for r in business_records if r.get("kind") == "business_goal_note"]),
            "decision_history_count": sum(
                1 for r in business_records if str(r.get("kind") or "").startswith("human_business_decision_")
            ),
            "customer_insight_count": len(
                [r for r in business_records if r.get("kind") == "customer_insight_note"]
            ),
            "revenue_observation_count": len(
                [r for r in business_records if r.get("kind") == "revenue_observation_note"]
            ),
            "alignment_node_count": (alignment_graph[0].get("node_count") if alignment_graph else 0),
            "entries": [{**r, "read_only": True} for r in business_records[-50:]],
            "read_only": True,
        }
    ]


def build_autonomous_business_operating_system(*, session_id: str) -> AutonomousBusinessOperatingSystemResult:
    sid = (session_id or "default").strip()[:64] or "default"
    business_records = list_autonomous_business_operating_system_records()
    human_approved = has_human_business_decision_approve(session_id=sid)

    lifecycle = build_autonomous_application_lifecycle_management(session_id=sid)
    lifecycle_payload = lifecycle.autonomous_application_lifecycle_management or {}
    lifecycle_sections = lifecycle_payload.get("sections") or {}

    generation = build_governed_application_generation(session_id=sid)
    gen_payload = generation.governed_application_generation or {}

    engineering = build_multi_repository_engineering_intelligence(session_id=sid)
    engineering_sections = engineering.multi_repository_engineering_intelligence.get("sections") or {}
    delivery_rows = list(engineering_sections.get("program_delivery_visibility") or [])

    product_name = str(gen_payload.get("product_name") or "portfolio")

    product_portfolio = _product_portfolio_registry(
        generation=gen_payload,
        lifecycle_sections=lifecycle_sections,
        business_records=business_records,
    )
    customer_intelligence = _customer_intelligence_registry(business_records=business_records)
    revenue_intelligence = _revenue_intelligence_registry(
        engineering_sections=engineering_sections,
        business_records=business_records,
    )
    team_operating = _team_operating_registry(
        business_records=business_records,
        lifecycle_sections=lifecycle_sections,
    )
    project_portfolio = _project_portfolio_registry(
        delivery_rows=delivery_rows,
        business_records=business_records,
    )
    business_operations = _business_operations_registry(
        lifecycle_sections=lifecycle_sections,
        business_records=business_records,
    )
    business_goals = _business_goal_registry(
        generation=gen_payload,
        business_records=business_records,
    )
    alignment_graph = _strategic_alignment_graph(
        goals=(business_goals[0].get("objectives") or []) if business_goals else [],
        delivery_rows=delivery_rows,
        lifecycle_sections=lifecycle_sections,
        product_name=product_name,
    )
    opportunity_portfolio = _business_opportunity_portfolio(
        lifecycle_sections=lifecycle_sections,
        business_records=business_records,
    )
    health_dashboard = _business_health_dashboard(
        lifecycle_sections=lifecycle_sections,
        engineering_sections=engineering_sections,
        business_records=business_records,
    )
    risk_dashboard = _business_risk_dashboard(
        lifecycle_sections=lifecycle_sections,
        business_records=business_records,
    )
    operating_memory = _business_operating_memory(
        business_records=business_records,
        alignment_graph=alignment_graph,
    )

    domain_registries = {
        "product": product_portfolio,
        "customer": customer_intelligence,
        "revenue": revenue_intelligence,
        "team": team_operating,
        "project": project_portfolio,
        "operational": business_operations,
    }

    sections = {
        "product_portfolio_registry": product_portfolio,
        "customer_intelligence_registry": customer_intelligence,
        "revenue_intelligence_registry": revenue_intelligence,
        "team_operating_registry": team_operating,
        "project_portfolio_registry": project_portfolio,
        "business_operations_registry": business_operations,
        "business_goal_registry": business_goals,
        "strategic_alignment_graph": alignment_graph,
        "business_opportunity_portfolio": opportunity_portfolio,
        "business_health_dashboard": health_dashboard,
        "business_risk_dashboard": risk_dashboard,
        "business_operating_memory": operating_memory,
        "business_operating_dashboard": [
            {
                "dashboard_id": "business-operating-dashboard",
                "business_domains": list(BUSINESS_DOMAINS),
                "goal_count": (business_goals[0] if business_goals else {}).get("objective_count", 0),
                "project_count": (project_portfolio[0] if project_portfolio else {}).get("project_count", 0),
                "customer_request_count": (customer_intelligence[0] if customer_intelligence else {}).get(
                    "request_count", 0
                ),
                "open_opportunity_count": (opportunity_portfolio[0] if opportunity_portfolio else {}).get(
                    "opportunity_count", 0
                ),
                "overall_health": (health_dashboard[0] if health_dashboard else {}).get("overall_health_tier"),
                "overall_risk": (risk_dashboard[0] if risk_dashboard else {}).get("overall_risk_tier"),
                "current_lifecycle_stage": lifecycle_payload.get("current_lifecycle_stage"),
                "strategic_alignment_nodes": (alignment_graph[0] if alignment_graph else {}).get("node_count", 0),
                "human_business_decision_approve": human_approved,
                "recommends_future_initiatives": True,
                "feeds_governed_delivery_planning": human_approved
                and bool(lifecycle_payload.get("human_lifecycle_decision_approve")),
                "read_only": True,
            }
        ],
        "human_business_review": [
            {
                "review_id": "human-business-decision",
                "decisions_supported": list(
                    (
                        "human_business_decision_approve",
                        "human_business_decision_hold",
                        "human_business_decision_reject",
                        "human_business_decision_defer",
                    )
                ),
                "human_business_decision_approve": human_approved,
                "execution_authority": False,
                "read_only": True,
            }
        ],
        "business_domain_registries": [
            {
                "domain": domain,
                "registry_id": (domain_registries[domain][0] if domain_registries[domain] else {}).get(
                    "registry_id"
                ),
                "operator_note_count": (domain_registries[domain][0] if domain_registries[domain] else {}).get(
                    "operator_note_count", 0
                ),
                "read_only": True,
            }
            for domain in BUSINESS_DOMAINS
        ],
        "forbidden_business_operating_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_BUSINESS_OPERATING_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_SCHEMA_VERSION,
        "fix": AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_290,
        "execution_performed": EXECUTION_PERFORMED_FIX_290,
        "business_compose_artifacts_only": AUTONOMOUS_BUSINESS_OPERATING_COMPOSES_EVIDENCE_ONLY_FIX_290,
        "business_authority": BUSINESS_AUTHORITY_FIX_290,
        "automatic_business_execution_enabled": AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290,
        "customer_mutation_authority": CUSTOMER_MUTATION_AUTHORITY_FIX_290,
        "billing_authority": BILLING_AUTHORITY_FIX_290,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_290,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_290,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_290,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_290,
        "merge_authority": MERGE_AUTHORITY_FIX_290,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_290,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_290,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_290,
        "invariant": AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_INVARIANT,
        "session_id": sid,
        "business_domains": list(BUSINESS_DOMAINS),
        "sections": sections,
        "operator_record_count": len(business_records),
        "human_business_decision_approve": human_approved,
        "fix_290_certification_requirements": list(FIX_290_CERTIFICATION_REQUIREMENTS),
        "autonomous_business_operating_system_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_PRINCIPLES
        ],
        "sources": {
            "composes_fix_280_application_lifecycle_management": True,
            "composes_fix_260_multi_repository_engineering_intelligence": True,
            "composes_fix_250_governed_application_generation": True,
            "composes_fix_261_product_evolution_intelligence": True,
            "composes_fix_270_product_stewardship": True,
            "pilot_reexecution_performed": False,
            "code_generation_performed": False,
            "financial_transactions_performed": False,
            "customer_mutation_performed": False,
            "billing_execution_performed": False,
        },
    }

    return AutonomousBusinessOperatingSystemResult(
        ok=True,
        session_id=sid,
        autonomous_business_operating_system=payload,
        detail="Autonomous business operating system composed from unified business evidence (business ≠ authority).",
    )

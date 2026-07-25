# SPDX-License-Identifier: Apache-2.0
"""FIX 327 — enterprise program intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_contract import (
    ENTERPRISE_PROGRAM_CORE_PRINCIPLE,
    PRIVACY_REQUIREMENTS,
    PROGRAM_ENTITY_TYPES,
    PROGRAM_HEALTH_STATUSES,
    PROGRAM_OPPORTUNITY_TYPES,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def build_program_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    projects = _composed_section(evidence, "fix_290", "project_portfolio_registry")
    products = _composed_section(evidence, "fix_290", "product_portfolio_registry")
    assets = _composed_section(evidence, "fix_324", "portfolio_asset_registry")
    plans = _composed_section(evidence, "fix_326", "strategic_plan_registry")

    programs: list[dict[str, Any]] = [
        {
            "program_id": "program-customer-intelligence",
            "entity_type": "strategic_program",
            "name": "Customer Intelligence Program",
            "tenant_scoped": True,
        },
        {
            "program_id": "program-mission-control",
            "entity_type": "strategic_program",
            "name": "Mission Control Platform Program",
            "tenant_scoped": True,
        },
    ]

    for item in (projects.get("projects") or projects.get("items") or [])[:4]:
        programs.append(
            {
                "program_id": f"initiative-{str(item)[:24]}",
                "entity_type": "initiative",
                "name": str(item),
                "tenant_scoped": True,
            }
        )
    for item in (products.get("products") or products.get("items") or [])[:4]:
        programs.append(
            {
                "program_id": f"project-{str(item)[:24]}",
                "entity_type": "project",
                "name": str(item),
                "tenant_scoped": True,
            }
        )
    for asset in (assets.get("assets") or [])[:4]:
        programs.append(
            {
                "program_id": str(asset.get("asset_id") or asset.get("name"))[:32],
                "entity_type": "workstream",
                "name": str(asset.get("name")),
                "tenant_scoped": True,
            }
        )
    for plan in (plans.get("plans") or [])[:3]:
        programs.append(
            {
                "program_id": str(plan.get("plan_id") or plan.get("scenario"))[:32],
                "entity_type": "initiative",
                "name": str(plan.get("scenario")),
                "tenant_scoped": True,
            }
        )

    return {
        "programs": programs[:20],
        "count": len(programs[:20]),
        "entity_types": list(PROGRAM_ENTITY_TYPES),
        "cross_tenant_program_visibility_forbidden": True,
        "validated": bool(programs),
    }


def build_program_dependency_report(*, evidence: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    launch_blockers = _composed_section(evidence, "fix_313", "launch_blocker_registry")
    planning = _composed_section(evidence, "fix_326", "strategic_plan_registry")
    portfolio = _composed_section(evidence, "fix_324", "portfolio_opportunity_registry")

    dependencies: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    sequencing: list[dict[str, Any]] = []
    critical_path: list[str] = []

    program_names = [str(p.get("name")) for p in registry.get("programs") or []]
    if len(program_names) >= 2:
        dependencies.append(
            {
                "from_program": program_names[0],
                "to_program": program_names[1],
                "dependency_type": "sequencing",
            }
        )
        critical_path.extend(program_names[:3])

    for blocker in (launch_blockers.get("blockers") or launch_blockers.get("items") or [])[:4]:
        blockers.append({"program": program_names[0] if program_names else "Mission Control", "blocker": str(blocker)})
        critical_path.append(f"resolve:{blocker}")

    for plan in (planning.get("plans") or [])[:3]:
        sequencing.append(
            {
                "program": str(plan.get("scenario")),
                "sequence_step": plan.get("scenario_type"),
                "depends_on": (plan.get("assumptions") or ["human plan approval"])[0],
            }
        )

    for opp in (portfolio.get("opportunities") or [])[:2]:
        dependencies.append(
            {
                "from_program": str(opp.get("title")),
                "to_program": program_names[-1] if program_names else "Portfolio execution",
                "dependency_type": "value_delivery",
            }
        )

    return {
        "dependencies": dependencies[:10],
        "blockers": blockers[:8],
        "sequencing_constraints": sequencing[:8],
        "critical_path": critical_path[:8],
        "dependency_count": len(dependencies),
        "blocker_count": len(blockers),
        "validated": bool(dependencies or blockers or sequencing or critical_path),
    }


def _health_status(*, risk_count: int, blocker_count: int, business_value: float) -> str:
    if blocker_count >= 2:
        return "blocked"
    if risk_count >= 4 or business_value < 0.45:
        return "at_risk"
    if risk_count >= 2 or business_value < 0.6:
        return "warning"
    return "healthy"


def build_program_health_report(*, evidence: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    platform = _composed_section(evidence, "fix_316", "platform_health_baseline")
    customer = _composed_section(evidence, "fix_316", "customer_health_baseline")
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    portfolio_value = _composed_section(evidence, "fix_324", "strategic_value_report")
    executive = _composed_section(evidence, "fix_325", "executive_decision_dashboard")

    risk_count = len(portfolio_risk.get("operational_risk") or []) + len(portfolio_risk.get("product_risk") or [])
    blocker_count = int(executive.get("highest_risk_decision_count") or 0)
    business_value = float(portfolio_value.get("business_value_score") or 0.5)

    program_health: list[dict[str, Any]] = []
    for program in registry.get("programs") or []:
        status = _health_status(risk_count=risk_count, blocker_count=blocker_count, business_value=business_value)
        program_health.append(
            {
                "program_id": program.get("program_id"),
                "name": program.get("name"),
                "health_status": status,
                "platform_health": platform.get("status", "UNKNOWN"),
                "customer_health": customer.get("status", "UNKNOWN"),
                "automatic_program_execution_forbidden": True,
            }
        )

    by_status = {status: 0 for status in PROGRAM_HEALTH_STATUSES}
    for row in program_health:
        key = str(row.get("health_status") or "warning")
        if key in by_status:
            by_status[key] += 1

    return {
        "sources": ["FIX 316", "FIX 324", "FIX 325"],
        "programs": program_health[:16],
        "health_status_counts": by_status,
        "health_dimensions": list(PROGRAM_HEALTH_STATUSES),
        "validated": bool(program_health),
    }


def build_program_progress_report(*, evidence: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    planning = _composed_section(evidence, "fix_326", "strategic_planning_dashboard")
    executive = _composed_section(evidence, "fix_325", "executive_decision_dashboard")
    comparison = _composed_section(evidence, "fix_326", "strategic_comparison_matrix")
    strongest = comparison.get("strongest_plan") or {}

    milestones: list[dict[str, Any]] = []
    for program in registry.get("programs") or []:
        milestones.append(
            {
                "program_id": program.get("program_id"),
                "name": program.get("name"),
                "milestone": "Portfolio evidence composed",
                "completion_percent": 65 if program.get("entity_type") == "strategic_program" else 45,
            }
        )

    completion_trend = "rising" if int(planning.get("generated_plan_count") or 0) >= 3 else "steady"
    confidence = "high" if float(strongest.get("comparison_score") or 0) >= 7 else "medium"
    if int(executive.get("highest_risk_decision_count") or 0) >= 2:
        confidence = "low"

    return {
        "milestones": milestones[:12],
        "completion_trend": completion_trend,
        "average_completion_percent": round(
            sum(m.get("completion_percent", 0) for m in milestones) / max(len(milestones), 1),
            1,
        ),
        "execution_confidence": confidence,
        "validated": bool(milestones),
    }


def build_program_risk_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    launch_risks = _composed_section(evidence, "fix_309", "launch_risk_registry")
    launch_blockers = _composed_section(evidence, "fix_313", "launch_blocker_registry")
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    planning_risk = _composed_section(evidence, "fix_326", "strategic_risk_forecast")

    operational = list(launch_blockers.get("blockers") or launch_blockers.get("items") or [])
    operational.extend(portfolio_risk.get("operational_risk") or [])
    operational.extend(planning_risk.get("operational_risks") or [])

    product = list(launch_risks.get("risks") or launch_risks.get("items") or [])
    product.extend(portfolio_risk.get("product_risk") or [])

    program_risks = [
        {
            "program": "Enterprise portfolio execution",
            "risk_signal": item,
            "source": "composed",
        }
        for item in (operational + product)[:8]
    ]

    return {
        "sources": ["FIX 309", "FIX 313", "FIX 324", "FIX 326"],
        "program_risks": program_risks,
        "operational_risk_signals": operational[:8],
        "product_risk_signals": product[:8],
        "planning_execution_risks": planning_risk.get("execution_risks") or [],
        "validated": bool(program_risks),
    }


def build_program_alignment_report(*, evidence: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    goals = _composed_section(evidence, "fix_290", "business_goal_registry")
    portfolio_alignment = _composed_section(evidence, "fix_324", "strategic_alignment_report")
    planning = _composed_section(evidence, "fix_326", "strategic_plan_registry")
    products = _composed_section(evidence, "fix_290", "product_portfolio_registry")

    goal_items = list(goals.get("objectives") or goals.get("goals") or portfolio_alignment.get("goals") or [])
    program_names = [str(p.get("name")) for p in registry.get("programs") or [] if p.get("entity_type") != "workstream"]
    product_items = list(products.get("products") or products.get("items") or [])
    plan_scenarios = [str(p.get("scenario")) for p in planning.get("plans") or []]

    aligned_rows: list[dict[str, Any]] = []
    for goal in goal_items[:4]:
        aligned_rows.append(
            {
                "goal": str(goal),
                "programs": program_names[:3],
                "products": product_items[:2],
            }
        )
    if not aligned_rows:
        aligned_rows.append(
            {
                "goal": "Deliver tenant-scoped portfolio outcomes",
                "programs": program_names[:3],
                "products": product_items[:2] or ["Mission Control"],
            }
        )

    return {
        "sources": ["FIX 290", "FIX 324", "FIX 326"],
        "goals": goal_items[:8] or ["Deliver tenant-scoped portfolio outcomes"],
        "programs": program_names[:8],
        "projects": [p for p in registry.get("programs") or [] if p.get("entity_type") == "project"][:8],
        "products": product_items[:8] or ["Mission Control"],
        "plan_scenarios": plan_scenarios[:5],
        "aligned_rows": aligned_rows,
        "alignment_score": round(min(1.0, len(aligned_rows) / 5.0 + 0.45), 3),
        "validated": bool(registry or goals or portfolio_alignment or planning),
    }


def build_program_opportunity_registry(
    *,
    dependency_report: dict[str, Any],
    health_report: dict[str, Any],
    risk_report: dict[str, Any],
    alignment_report: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    for program in health_report.get("programs") or []:
        if program.get("health_status") == "healthy":
            opportunities.append(
                {
                    "opportunity_id": f"acceleration-{str(program.get('program_id'))[:20]}",
                    "title": f"Accelerate {program.get('name')}",
                    "opportunity_type": "acceleration",
                    "automatic_program_execution_forbidden": True,
                }
            )

    for blocker in dependency_report.get("blockers") or []:
        opportunities.append(
            {
                "opportunity_id": f"dependency-{str(blocker.get('blocker'))[:20]}",
                "title": f"Reduce dependency blocker: {blocker.get('blocker')}",
                "opportunity_type": "dependency_reduction",
                "automatic_program_execution_forbidden": True,
            }
        )

    if alignment_report.get("alignment_score", 0) >= 0.6:
        opportunities.append(
            {
                "opportunity_id": "efficiency-portfolio-coordination",
                "title": "Improve cross-program coordination efficiency",
                "opportunity_type": "efficiency",
                "automatic_program_execution_forbidden": True,
            }
        )

    for risk in (risk_report.get("program_risks") or [])[:2]:
        opportunities.append(
            {
                "opportunity_id": f"efficiency-{str(risk.get('risk_signal'))[:20]}",
                "title": f"Mitigate program risk: {risk.get('risk_signal')}",
                "opportunity_type": "efficiency",
                "automatic_program_execution_forbidden": True,
            }
        )

    return {
        "opportunities": opportunities[:16],
        "count": len(opportunities[:16]),
        "opportunity_types": list(PROGRAM_OPPORTUNITY_TYPES),
        "core_principle": ENTERPRISE_PROGRAM_CORE_PRINCIPLE,
    }


def _program_priority_score(
    *,
    value: float,
    risk: float,
    health: str,
    impact: float,
) -> float:
    health_bonus = {"healthy": 0.3, "warning": 0.1, "at_risk": -0.1, "blocked": -0.4}.get(health, 0.0)
    return round(value * 3.0 + impact * 2.0 - risk + health_bonus, 3)


def build_program_priority_matrix(
    *,
    registry: dict[str, Any],
    health_report: dict[str, Any],
    risk_report: dict[str, Any],
    alignment_report: dict[str, Any],
    opportunity_registry: dict[str, Any],
) -> dict[str, Any]:
    health_by_id = {str(p.get("program_id")): p for p in health_report.get("programs") or []}
    alignment_score = float(alignment_report.get("alignment_score") or 0.5)
    ranked: list[dict[str, Any]] = []

    for program in registry.get("programs") or []:
        pid = str(program.get("program_id"))
        health = health_by_id.get(pid, {})
        status = str(health.get("health_status") or "warning")
        risk = 0.6 if status in {"at_risk", "blocked"} else 0.25
        value = alignment_score
        impact = 0.8 if program.get("entity_type") == "strategic_program" else 0.55
        ranked.append(
            {
                **program,
                "health_status": status,
                "priority_score": _program_priority_score(
                    value=value,
                    risk=risk,
                    health=status,
                    impact=impact,
                ),
                "intervention_type": "leadership_review" if status in {"at_risk", "blocked"} else "monitor",
            }
        )

    ranked.sort(key=lambda row: row.get("priority_score", 0), reverse=True)

    highest_value = sorted(ranked, key=lambda row: float(row.get("priority_score") or 0), reverse=True)[:5]
    highest_risk = [row for row in ranked if row.get("health_status") in {"at_risk", "blocked"}][:5]
    if not highest_risk:
        highest_risk = [
            {
                "program_id": "portfolio-risk",
                "name": str((risk_report.get("program_risks") or [{}])[0].get("risk_signal", "Portfolio risk")),
                "health_status": "at_risk",
                "priority_score": 7.5,
                "intervention_type": "leadership_review",
            }
        ]

    highest_impact = [
        opp for opp in opportunity_registry.get("opportunities") or [] if opp.get("opportunity_type") == "acceleration"
    ][:5]
    if not highest_impact:
        highest_impact = ranked[:5]

    return {
        "ranked_programs": ranked[:12],
        "highest_value_programs": highest_value,
        "highest_risk_programs": highest_risk,
        "highest_impact_interventions": highest_impact,
        "automatic_program_execution_forbidden": True,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
    }


def build_enterprise_program_dashboard(
    *,
    registry: dict[str, Any],
    dependency_report: dict[str, Any],
    health_report: dict[str, Any],
    progress_report: dict[str, Any],
    risk_report: dict[str, Any],
    alignment_report: dict[str, Any],
    opportunity_registry: dict[str, Any],
    priority_matrix: dict[str, Any],
) -> dict[str, Any]:
    health_counts = health_report.get("health_status_counts") or {}
    top = (priority_matrix.get("ranked_programs") or [{}])[0]
    return {
        "program_count": registry.get("count", 0),
        "dependency_count": dependency_report.get("dependency_count", 0),
        "blocker_count": dependency_report.get("blocker_count", 0),
        "healthy_program_count": health_counts.get("healthy", 0),
        "blocked_program_count": health_counts.get("blocked", 0),
        "at_risk_program_count": health_counts.get("at_risk", 0),
        "average_completion_percent": progress_report.get("average_completion_percent", 0),
        "execution_confidence": progress_report.get("execution_confidence", "medium"),
        "program_risk_count": len(risk_report.get("program_risks") or []),
        "alignment_score": alignment_report.get("alignment_score", 0),
        "program_opportunity_count": opportunity_registry.get("count", 0),
        "top_priority_program": top.get("name"),
        "top_priority_score": top.get("priority_score", 0),
        "leadership_intervention_programs": [
            row.get("name") for row in priority_matrix.get("highest_risk_programs") or [] if row.get("name")
        ][:3],
        "core_principle": ENTERPRISE_PROGRAM_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_program_execution_forbidden": True,
    }

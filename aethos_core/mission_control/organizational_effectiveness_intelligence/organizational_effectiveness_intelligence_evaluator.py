# SPDX-License-Identifier: Apache-2.0
"""FIX 328 — organizational effectiveness intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_contract import (
    ORGANIZATIONAL_CORE_PRINCIPLE,
    ORGANIZATIONAL_EFFECTIVENESS_LEVELS,
    ORGANIZATIONAL_EFFECTIVENESS_SCORECARD_DIMENSIONS,
    ORGANIZATIONAL_OPPORTUNITY_TYPES,
    ORGANIZATIONAL_RISK_CATEGORIES,
    PRIVACY_REQUIREMENTS,
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
        return "EFFECTIVE"
    if score >= 0.55:
        return "STABLE"
    if score >= 0.4:
        return "NEEDS_IMPROVEMENT"
    return "CRITICAL"


def build_organizational_structure_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    organizations = _composed_section(evidence, "fix_300", "organization_registry")
    workspaces = _composed_section(evidence, "fix_300", "workspace_registry")
    roles = _composed_section(evidence, "fix_300", "role_registry")
    governance = _composed_section(evidence, "fix_300", "tenant_governance_boundary_registry")
    governance_actions = _composed_section(evidence, "fix_302", "governance_action_report")

    org_items = list(organizations.get("organizations") or organizations.get("items") or [])
    if not org_items and organizations.get("organization_count"):
        org_items = [{"name": "Primary tenant organization", "tenant_scoped": True}]

    workspace_items = list(workspaces.get("workspaces") or workspaces.get("items") or [])
    role_items = list(roles.get("roles") or roles.get("items") or [])
    responsibility_items = list(
        governance.get("boundaries")
        or governance.get("responsibilities")
        or governance_actions.get("actions")
        or []
    )

    return {
        "sources": ["FIX 300", "FIX 302"],
        "organizations": org_items[:8] or [{"name": "Primary tenant organization", "tenant_scoped": True}],
        "workspaces": workspace_items[:8] or [{"name": "Default workspace", "tenant_scoped": True}],
        "roles": role_items[:8] or [{"name": "operator", "tenant_scoped": True}],
        "governance_responsibilities": responsibility_items[:8] or ["Tenant-scoped governance review"],
        "organization_count": organizations.get("organization_count", len(org_items) or 1),
        "workspace_count": workspaces.get("workspace_count", len(workspace_items) or 1),
        "cross_tenant_visibility_forbidden": True,
        "validated": bool(organizations or workspaces or roles or governance),
    }


def build_governance_friction_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    boundary = _composed_section(evidence, "fix_302", "tenant_boundary_audit")
    governance_action = _composed_section(evidence, "fix_302", "governance_action_report")
    least_privilege = _composed_section(evidence, "fix_302", "least_privilege_report")
    governance_timeline = _composed_section(evidence, "fix_307", "governance_timeline")
    programs = _composed_section(evidence, "fix_327", "program_dependency_report")

    approval_delays = list(
        least_privilege.get("gaps")
        or least_privilege.get("findings")
        or governance_action.get("pending_actions")
        or []
    )
    review_delays = list(
        governance_timeline.get("delayed_reviews")
        or governance_timeline.get("items")
        or governance_timeline.get("events")
        or []
    )
    bottlenecks = list(boundary.get("findings") or boundary.get("violations") or [])
    bottlenecks.extend(programs.get("blockers") or [])

    return {
        "sources": ["FIX 302", "FIX 307", "FIX 327"],
        "approval_delays": approval_delays[:8],
        "review_delays": review_delays[:8],
        "governance_bottlenecks": bottlenecks[:8],
        "friction_signal_count": len(approval_delays) + len(review_delays) + len(bottlenecks),
        "validated": bool(approval_delays or review_delays or bottlenecks or boundary or governance_timeline),
    }


def build_coordination_intelligence_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    dependency = _composed_section(evidence, "fix_327", "program_dependency_report")
    programs = _composed_section(evidence, "fix_327", "program_registry")
    dashboard = _composed_section(evidence, "fix_327", "enterprise_program_dashboard")

    dependency_coordination = list(dependency.get("dependencies") or [])
    cross_program = [
        dep for dep in dependency_coordination if dep.get("dependency_type") in {"sequencing", "value_delivery"}
    ]
    cross_workstream = [
        p for p in (programs.get("programs") or []) if p.get("entity_type") == "workstream"
    ]

    failures: list[str] = []
    if dependency.get("blocker_count", 0):
        failures.extend([str(b.get("blocker")) for b in (dependency.get("blockers") or [])[:4]])
    if int(dashboard.get("blocker_count") or 0) >= 2:
        failures.append("Multiple program blockers indicate coordination failure risk")

    return {
        "sources": ["FIX 327"],
        "dependency_coordination": dependency_coordination[:8],
        "cross_program_coordination": cross_program[:8],
        "cross_workstream_coordination": cross_workstream[:8],
        "coordination_failures": failures[:8],
        "validated": bool(dependency_coordination or cross_program or cross_workstream or failures),
    }


def build_organizational_capacity_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    programs = _composed_section(evidence, "fix_327", "program_registry")
    dashboard = _composed_section(evidence, "fix_327", "enterprise_program_dashboard")
    friction = build_governance_friction_report(evidence=evidence)
    tenant = _composed_section(evidence, "fix_300", "tenant_dashboard")
    decisions = _composed_section(evidence, "fix_325", "executive_decision_registry")

    active_initiatives = [
        p for p in (programs.get("programs") or []) if p.get("entity_type") in {"initiative", "project"}
    ]
    active_programs = [
        p for p in (programs.get("programs") or []) if p.get("entity_type") == "strategic_program"
    ]
    operational_burden = int(dashboard.get("program_risk_count") or 0) + int(tenant.get("project_count") or 0)
    review_burden = friction.get("friction_signal_count", 0) + int(decisions.get("pending_count") or 0)

    constrained = operational_burden >= 6 or review_burden >= 4

    return {
        "active_initiatives": active_initiatives[:8],
        "active_programs": active_programs[:8],
        "active_initiative_count": len(active_initiatives),
        "active_program_count": len(active_programs),
        "operational_burden": operational_burden,
        "review_burden": review_burden,
        "capacity_constrained": constrained,
        "validated": True,
    }


def build_decision_velocity_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    decisions = _composed_section(evidence, "fix_325", "executive_decision_registry")
    recommendations = _composed_section(evidence, "fix_325", "executive_recommendation_report")
    dashboard = _composed_section(evidence, "fix_325", "executive_decision_dashboard")

    pending = int(decisions.get("pending_count") or 0)
    reviewed = int(decisions.get("reviewed_count") or 0)
    deferred = int(decisions.get("deferred_count") or 0)
    total = max(pending + reviewed + deferred, 1)

    review_velocity = round(reviewed / total, 3)
    decision_latency = "high" if pending >= 3 else "medium" if pending >= 1 else "low"
    approval_throughput = round(
        len(recommendations.get("recommendations") or []) / max(int(dashboard.get("recommendation_count") or 1), 1),
        3,
    )

    return {
        "sources": ["FIX 325"],
        "pending_decisions": pending,
        "reviewed_decisions": reviewed,
        "deferred_decisions": deferred,
        "review_velocity": review_velocity,
        "decision_latency": decision_latency,
        "approval_throughput": approval_throughput,
        "validated": bool(decisions or recommendations or dashboard),
    }


def build_organizational_risk_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    launch_risks = _composed_section(evidence, "fix_309", "launch_risk_registry")
    launch_blockers = _composed_section(evidence, "fix_313", "launch_blocker_registry")
    program_risk = _composed_section(evidence, "fix_327", "program_risk_report")
    dependency = _composed_section(evidence, "fix_327", "program_dependency_report")
    friction = build_governance_friction_report(evidence=evidence)

    execution_risk = list(program_risk.get("program_risks") or [])
    dependency_risk = list(dependency.get("blockers") or []) + list(dependency.get("critical_path") or [])
    governance_risk = list(friction.get("governance_bottlenecks") or []) + list(friction.get("review_delays") or [])
    operational_risk = list(launch_blockers.get("blockers") or launch_blockers.get("items") or [])
    operational_risk.extend(launch_risks.get("risks") or launch_risks.get("items") or [])

    return {
        "sources": ["FIX 309", "FIX 313", "FIX 327"],
        "execution_risk": execution_risk[:8],
        "dependency_risk": dependency_risk[:8],
        "governance_risk": governance_risk[:8],
        "operational_risk": operational_risk[:8],
        "risk_categories": list(ORGANIZATIONAL_RISK_CATEGORIES),
        "validated": bool(execution_risk or dependency_risk or governance_risk or operational_risk),
    }


def build_organizational_opportunity_registry(
    *,
    friction_report: dict[str, Any],
    coordination_report: dict[str, Any],
    capacity_report: dict[str, Any],
    risk_report: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    for item in friction_report.get("governance_bottlenecks") or []:
        opportunities.append(
            {
                "opportunity_id": f"governance-{str(item)[:20]}",
                "title": f"Reduce governance bottleneck: {item}",
                "opportunity_type": "governance",
                "automatic_organizational_changes_forbidden": True,
            }
        )

    for failure in coordination_report.get("coordination_failures") or []:
        opportunities.append(
            {
                "opportunity_id": f"coordination-{str(failure)[:20]}",
                "title": f"Improve coordination: {failure}",
                "opportunity_type": "coordination",
                "automatic_organizational_changes_forbidden": True,
            }
        )

    if capacity_report.get("capacity_constrained"):
        opportunities.append(
            {
                "opportunity_id": "efficiency-capacity-relief",
                "title": "Relieve organizational capacity constraints through prioritization",
                "opportunity_type": "efficiency",
                "automatic_organizational_changes_forbidden": True,
            }
        )

    for risk in (risk_report.get("operational_risk") or [])[:2]:
        opportunities.append(
            {
                "opportunity_id": f"efficiency-{str(risk)[:20]}",
                "title": f"Reduce operational friction: {risk}",
                "opportunity_type": "efficiency",
                "automatic_organizational_changes_forbidden": True,
            }
        )

    return {
        "opportunities": opportunities[:16],
        "count": len(opportunities[:16]),
        "opportunity_types": list(ORGANIZATIONAL_OPPORTUNITY_TYPES),
        "core_principle": ORGANIZATIONAL_CORE_PRINCIPLE,
    }


def build_organizational_effectiveness_scorecard(
    *,
    friction_report: dict[str, Any],
    coordination_report: dict[str, Any],
    capacity_report: dict[str, Any],
    velocity_report: dict[str, Any],
    risk_report: dict[str, Any],
    program_dashboard: dict[str, Any],
) -> dict[str, Any]:
    friction_penalty = min(0.5, friction_report.get("friction_signal_count", 0) * 0.08)
    coordination_penalty = min(0.4, len(coordination_report.get("coordination_failures") or []) * 0.12)
    capacity_penalty = 0.25 if capacity_report.get("capacity_constrained") else 0.0
    velocity_bonus = float(velocity_report.get("review_velocity") or 0) * 0.3
    execution_base = 0.7 if int(program_dashboard.get("healthy_program_count") or 0) >= 1 else 0.45
    execution_penalty = min(0.35, len(risk_report.get("execution_risk") or []) * 0.06)

    dimension_scores = {
        "governance": max(0.0, 0.75 - friction_penalty),
        "coordination": max(0.0, 0.7 - coordination_penalty),
        "capacity": max(0.0, 0.68 - capacity_penalty),
        "decision_velocity": max(0.0, min(1.0, 0.55 + velocity_bonus)),
        "execution_effectiveness": max(0.0, execution_base - execution_penalty),
    }

    levels = {dim: _level_from_score(score) for dim, score in dimension_scores.items()}
    overall_score = round(sum(dimension_scores.values()) / len(dimension_scores), 3)

    return {
        "dimensions": list(ORGANIZATIONAL_EFFECTIVENESS_SCORECARD_DIMENSIONS),
        "dimension_scores": dimension_scores,
        "dimension_levels": levels,
        "overall_score": overall_score,
        "overall_level": _level_from_score(overall_score),
        "levels": list(ORGANIZATIONAL_EFFECTIVENESS_LEVELS),
        "automatic_organizational_changes_forbidden": True,
        "validated": True,
    }


def build_organizational_effectiveness_dashboard(
    *,
    structure_registry: dict[str, Any],
    friction_report: dict[str, Any],
    coordination_report: dict[str, Any],
    capacity_report: dict[str, Any],
    velocity_report: dict[str, Any],
    risk_report: dict[str, Any],
    opportunity_registry: dict[str, Any],
    scorecard: dict[str, Any],
) -> dict[str, Any]:
    return {
        "organization_count": structure_registry.get("organization_count", 0),
        "workspace_count": structure_registry.get("workspace_count", 0),
        "friction_signal_count": friction_report.get("friction_signal_count", 0),
        "governance_bottleneck_count": len(friction_report.get("governance_bottlenecks") or []),
        "coordination_failure_count": len(coordination_report.get("coordination_failures") or []),
        "capacity_constrained": capacity_report.get("capacity_constrained", False),
        "review_burden": capacity_report.get("review_burden", 0),
        "decision_latency": velocity_report.get("decision_latency", "medium"),
        "review_velocity": velocity_report.get("review_velocity", 0),
        "organizational_risk_count": (
            len(risk_report.get("execution_risk") or [])
            + len(risk_report.get("governance_risk") or [])
        ),
        "opportunity_count": opportunity_registry.get("count", 0),
        "overall_effectiveness_level": scorecard.get("overall_level", "STABLE"),
        "overall_effectiveness_score": scorecard.get("overall_score", 0),
        "core_principle": ORGANIZATIONAL_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_organizational_changes_forbidden": True,
    }

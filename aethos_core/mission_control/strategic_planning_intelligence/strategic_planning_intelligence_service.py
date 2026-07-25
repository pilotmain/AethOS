# SPDX-License-Identifier: Apache-2.0
"""FIX 326 — strategic planning intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_326_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_326,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_326,
    AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_326,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326,
    EXECUTION_PERFORMED_FIX_326,
    FORBIDDEN_PLANNING_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_326,
    HUMAN_PLANNING_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_326,
    PRIVACY_REQUIREMENTS,
    STRATEGIC_PLANNING_AUTHORITY_FIX_326,
    STRATEGIC_PLANNING_COMPOSES_EVIDENCE_ONLY_FIX_326,
    STRATEGIC_PLANNING_CORE_PRINCIPLE,
    STRATEGIC_PLANNING_INTELLIGENCE_DOMAINS,
    STRATEGIC_PLANNING_INTELLIGENCE_FIX,
    STRATEGIC_PLANNING_INTELLIGENCE_INVARIANT,
    STRATEGIC_PLANNING_INTELLIGENCE_SCHEMA_VERSION,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_evaluator import (
    build_resource_planning_report,
    build_scenario_impact_report,
    build_strategic_comparison_matrix,
    build_strategic_opportunity_forecast,
    build_strategic_plan_registry,
    build_strategic_planning_dashboard,
    build_strategic_planning_registry,
    build_strategic_risk_forecast,
    build_strategic_scenario_report,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_evidence import (
    collect_strategic_planning_evidence,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_store import (
    has_planning_review_decision_approve,
    list_planning_review_records,
)


@dataclass(frozen=True)
class StrategicPlanningIntelligenceResult:
    ok: bool
    session_id: str
    strategic_planning_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_strategic_planning_intelligence(*, session_id: str = "default") -> StrategicPlanningIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_strategic_planning_evidence(session_id=sid)

    strategic_planning_registry = build_strategic_planning_registry(evidence=evidence)
    strategic_scenario_report = build_strategic_scenario_report(evidence=evidence)
    scenario_impact_report = build_scenario_impact_report(
        scenario_report=strategic_scenario_report,
        evidence=evidence,
    )
    strategic_risk_forecast = build_strategic_risk_forecast(evidence=evidence)
    strategic_opportunity_forecast = build_strategic_opportunity_forecast(evidence=evidence)
    resource_planning_report = build_resource_planning_report(evidence=evidence)
    strategic_plan_registry = build_strategic_plan_registry(
        scenario_report=strategic_scenario_report,
        impact_report=scenario_impact_report,
        risk_forecast=strategic_risk_forecast,
        opportunity_forecast=strategic_opportunity_forecast,
    )
    strategic_comparison_matrix = build_strategic_comparison_matrix(
        plan_registry=strategic_plan_registry,
        scenario_report=strategic_scenario_report,
        risk_forecast=strategic_risk_forecast,
    )
    strategic_planning_dashboard = build_strategic_planning_dashboard(
        planning_registry=strategic_planning_registry,
        scenario_report=strategic_scenario_report,
        impact_report=scenario_impact_report,
        risk_forecast=strategic_risk_forecast,
        opportunity_forecast=strategic_opportunity_forecast,
        resource_report=resource_planning_report,
        plan_registry=strategic_plan_registry,
        comparison_matrix=strategic_comparison_matrix,
    )
    strategic_planning_dashboard["human_planning_review_decision_approve"] = has_planning_review_decision_approve(
        session_id=sid
    )

    strategic_planning_review_registry = {
        "records": list_planning_review_records(),
        "commands": (
            "planning note: ...",
            "planning review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "strategic_planning_registry": [strategic_planning_registry],
        "strategic_scenario_report": [strategic_scenario_report],
        "scenario_impact_report": [scenario_impact_report],
        "strategic_risk_forecast": [strategic_risk_forecast],
        "strategic_opportunity_forecast": [strategic_opportunity_forecast],
        "resource_planning_report": [resource_planning_report],
        "strategic_plan_registry": [strategic_plan_registry],
        "strategic_comparison_matrix": [strategic_comparison_matrix],
        "strategic_planning_dashboard": [strategic_planning_dashboard],
        "strategic_planning_review_registry": [strategic_planning_review_registry],
    }

    board = {
        "schema_version": STRATEGIC_PLANNING_INTELLIGENCE_SCHEMA_VERSION,
        "fix": STRATEGIC_PLANNING_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": STRATEGIC_PLANNING_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_326,
        "execution_performed": EXECUTION_PERFORMED_FIX_326,
        "strategic_planning_authority": STRATEGIC_PLANNING_AUTHORITY_FIX_326,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326,
        "automatic_project_creation_enabled": AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_326,
        "automatic_budget_allocation_enabled": AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_326,
        "automatic_resource_assignment_enabled": AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_326,
        "strategic_planning_compose_artifacts_only": STRATEGIC_PLANNING_COMPOSES_EVIDENCE_ONLY_FIX_326,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_326,
        "domains": list(STRATEGIC_PLANNING_INTELLIGENCE_DOMAINS),
        "human_planning_review_decision_kinds": list(HUMAN_PLANNING_REVIEW_DECISION_KINDS),
        "forbidden_planning_actions": [label for label, _detail in FORBIDDEN_PLANNING_ACTIONS],
        "core_principle": STRATEGIC_PLANNING_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "fix_326_certification_requirements": list(FIX_326_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return StrategicPlanningIntelligenceResult(
        ok=True,
        session_id=sid,
        strategic_planning_intelligence=board,
        detail="Strategic planning intelligence composed without strategic execution authority.",
    )

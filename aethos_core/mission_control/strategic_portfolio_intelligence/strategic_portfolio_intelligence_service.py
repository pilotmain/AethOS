# SPDX-License-Identifier: Apache-2.0
"""FIX 324 — strategic portfolio intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_324_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324,
    EXECUTION_PERFORMED_FIX_324,
    FORBIDDEN_STRATEGIC_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_324,
    HUMAN_STRATEGIC_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_324,
    PRIVACY_REQUIREMENTS,
    STRATEGIC_AUTHORITY_FIX_324,
    STRATEGIC_CORE_PRINCIPLE,
    STRATEGIC_PORTFOLIO_COMPOSES_EVIDENCE_ONLY_FIX_324,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_DOMAINS,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_FIX,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_INVARIANT,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_SCHEMA_VERSION,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_evaluator import (
    build_investment_opportunity_report,
    build_portfolio_asset_registry,
    build_portfolio_opportunity_registry,
    build_portfolio_risk_report,
    build_resource_allocation_report,
    build_strategic_alignment_report,
    build_strategic_portfolio_dashboard,
    build_strategic_priority_matrix,
    build_strategic_value_report,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_evidence import (
    collect_strategic_portfolio_evidence,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_store import (
    has_strategic_review_decision_approve,
    list_strategic_review_records,
)


@dataclass(frozen=True)
class StrategicPortfolioIntelligenceResult:
    ok: bool
    session_id: str
    strategic_portfolio_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_strategic_portfolio_intelligence(*, session_id: str = "default") -> StrategicPortfolioIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_strategic_portfolio_evidence(session_id=sid)

    portfolio_asset_registry = build_portfolio_asset_registry(evidence=evidence)
    strategic_value_report = build_strategic_value_report(evidence=evidence)
    investment_opportunity_report = build_investment_opportunity_report(evidence=evidence)
    portfolio_risk_report = build_portfolio_risk_report(evidence=evidence)
    resource_allocation_report = build_resource_allocation_report(evidence=evidence)
    strategic_alignment_report = build_strategic_alignment_report(evidence=evidence)
    portfolio_opportunity_registry = build_portfolio_opportunity_registry(
        investment_report=investment_opportunity_report,
        strategic_value=strategic_value_report,
        alignment_report=strategic_alignment_report,
        risk_report=portfolio_risk_report,
    )
    strategic_priority_matrix = build_strategic_priority_matrix(
        registry=portfolio_opportunity_registry,
        investment_report=investment_opportunity_report,
        risk_report=portfolio_risk_report,
    )
    strategic_portfolio_dashboard = build_strategic_portfolio_dashboard(
        asset_registry=portfolio_asset_registry,
        strategic_value=strategic_value_report,
        investment_report=investment_opportunity_report,
        risk_report=portfolio_risk_report,
        resource_report=resource_allocation_report,
        alignment_report=strategic_alignment_report,
        opportunity_registry=portfolio_opportunity_registry,
        priority_matrix=strategic_priority_matrix,
    )
    strategic_portfolio_dashboard["human_strategic_review_decision_approve"] = has_strategic_review_decision_approve(
        session_id=sid
    )

    strategic_review_registry = {
        "records": list_strategic_review_records(),
        "commands": (
            "strategic note: ...",
            "strategic review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "portfolio_asset_registry": [portfolio_asset_registry],
        "strategic_value_report": [strategic_value_report],
        "investment_opportunity_report": [investment_opportunity_report],
        "portfolio_risk_report": [portfolio_risk_report],
        "resource_allocation_report": [resource_allocation_report],
        "strategic_alignment_report": [strategic_alignment_report],
        "portfolio_opportunity_registry": [portfolio_opportunity_registry],
        "strategic_priority_matrix": [strategic_priority_matrix],
        "strategic_portfolio_dashboard": [strategic_portfolio_dashboard],
        "strategic_review_registry": [strategic_review_registry],
    }

    board = {
        "schema_version": STRATEGIC_PORTFOLIO_INTELLIGENCE_SCHEMA_VERSION,
        "fix": STRATEGIC_PORTFOLIO_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": STRATEGIC_PORTFOLIO_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_324,
        "execution_performed": EXECUTION_PERFORMED_FIX_324,
        "strategic_authority": STRATEGIC_AUTHORITY_FIX_324,
        "automatic_budget_allocation_enabled": AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324,
        "automatic_project_creation_enabled": AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324,
        "automatic_resource_reallocation_enabled": AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324,
        "strategic_portfolio_compose_artifacts_only": STRATEGIC_PORTFOLIO_COMPOSES_EVIDENCE_ONLY_FIX_324,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_324,
        "domains": list(STRATEGIC_PORTFOLIO_INTELLIGENCE_DOMAINS),
        "human_strategic_review_decision_kinds": list(HUMAN_STRATEGIC_REVIEW_DECISION_KINDS),
        "forbidden_strategic_actions": [label for label, _detail in FORBIDDEN_STRATEGIC_ACTIONS],
        "fix_324_certification_requirements": list(FIX_324_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return StrategicPortfolioIntelligenceResult(
        ok=True,
        session_id=sid,
        strategic_portfolio_intelligence=board,
        detail="Strategic portfolio intelligence composed without executive decision authority.",
    )

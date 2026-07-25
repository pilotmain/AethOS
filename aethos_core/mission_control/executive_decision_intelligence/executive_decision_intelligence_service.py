# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_325_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_325,
    AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_325,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_325,
    EXECUTION_PERFORMED_FIX_325,
    EXECUTIVE_AUTHORITY_FIX_325,
    EXECUTIVE_CORE_PRINCIPLE,
    EXECUTIVE_DECISION_COMPOSES_EVIDENCE_ONLY_FIX_325,
    EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS,
    EXECUTIVE_DECISION_INTELLIGENCE_FIX,
    EXECUTIVE_DECISION_INTELLIGENCE_INVARIANT,
    EXECUTIVE_DECISION_INTELLIGENCE_SCHEMA_VERSION,
    FORBIDDEN_EXECUTIVE_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_325,
    HUMAN_EXECUTIVE_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_325,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_evaluator import (
    build_decision_opportunity_report,
    build_decision_risk_report,
    build_executive_alignment_report,
    build_executive_decision_dashboard,
    build_executive_decision_registry,
    build_executive_opportunity_registry,
    build_executive_priority_matrix,
    build_executive_recommendation_report,
    build_tradeoff_analysis_report,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_evidence import (
    collect_executive_decision_evidence,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_store import (
    has_executive_review_decision_approve,
    list_executive_review_records,
)


@dataclass(frozen=True)
class ExecutiveDecisionIntelligenceResult:
    ok: bool
    session_id: str
    executive_decision_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_executive_decision_intelligence(*, session_id: str = "default") -> ExecutiveDecisionIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_executive_decision_evidence(session_id=sid)

    executive_decision_registry = build_executive_decision_registry(evidence=evidence)
    decision_opportunity_report = build_decision_opportunity_report(evidence=evidence)
    decision_risk_report = build_decision_risk_report(evidence=evidence)
    executive_recommendation_report = build_executive_recommendation_report(evidence=evidence)
    tradeoff_analysis_report = build_tradeoff_analysis_report(
        opportunity_report=decision_opportunity_report,
        risk_report=decision_risk_report,
        recommendation_report=executive_recommendation_report,
    )
    executive_alignment_report = build_executive_alignment_report(evidence=evidence)
    executive_opportunity_registry = build_executive_opportunity_registry(
        opportunity_report=decision_opportunity_report,
        recommendation_report=executive_recommendation_report,
        evidence=evidence,
    )
    executive_priority_matrix = build_executive_priority_matrix(
        registry=executive_opportunity_registry,
        recommendation_report=executive_recommendation_report,
        risk_report=decision_risk_report,
        tradeoff_report=tradeoff_analysis_report,
    )
    executive_decision_dashboard = build_executive_decision_dashboard(
        decision_registry=executive_decision_registry,
        opportunity_report=decision_opportunity_report,
        risk_report=decision_risk_report,
        recommendation_report=executive_recommendation_report,
        tradeoff_report=tradeoff_analysis_report,
        alignment_report=executive_alignment_report,
        opportunity_registry=executive_opportunity_registry,
        priority_matrix=executive_priority_matrix,
    )
    executive_decision_dashboard["human_executive_review_decision_approve"] = has_executive_review_decision_approve(
        session_id=sid
    )

    executive_review_registry = {
        "records": list_executive_review_records(),
        "commands": (
            "executive note: ...",
            "executive review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "executive_decision_registry": [executive_decision_registry],
        "decision_opportunity_report": [decision_opportunity_report],
        "decision_risk_report": [decision_risk_report],
        "executive_recommendation_report": [executive_recommendation_report],
        "tradeoff_analysis_report": [tradeoff_analysis_report],
        "executive_alignment_report": [executive_alignment_report],
        "executive_opportunity_registry": [executive_opportunity_registry],
        "executive_priority_matrix": [executive_priority_matrix],
        "executive_decision_dashboard": [executive_decision_dashboard],
        "executive_review_registry": [executive_review_registry],
    }

    board = {
        "schema_version": EXECUTIVE_DECISION_INTELLIGENCE_SCHEMA_VERSION,
        "fix": EXECUTIVE_DECISION_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": EXECUTIVE_DECISION_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_325,
        "execution_performed": EXECUTION_PERFORMED_FIX_325,
        "executive_authority": EXECUTIVE_AUTHORITY_FIX_325,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_325,
        "automatic_resource_reallocation_enabled": AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_325,
        "automatic_budget_allocation_enabled": AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_325,
        "automatic_decision_execution_enabled": AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325,
        "executive_decision_compose_artifacts_only": EXECUTIVE_DECISION_COMPOSES_EVIDENCE_ONLY_FIX_325,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_325,
        "domains": list(EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS),
        "human_executive_review_decision_kinds": list(HUMAN_EXECUTIVE_REVIEW_DECISION_KINDS),
        "forbidden_executive_actions": [label for label, _detail in FORBIDDEN_EXECUTIVE_ACTIONS],
        "core_principle": EXECUTIVE_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "fix_325_certification_requirements": list(FIX_325_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return ExecutiveDecisionIntelligenceResult(
        ok=True,
        session_id=sid,
        executive_decision_intelligence=board,
        detail="Executive decision intelligence composed without executive authority.",
    )

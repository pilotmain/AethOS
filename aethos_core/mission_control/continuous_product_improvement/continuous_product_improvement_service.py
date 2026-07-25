# SPDX-License-Identifier: Apache-2.0
"""FIX 317 — continuous product improvement service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_317_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_contract import (
    AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317,
    AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_317,
    AUTOMATIC_PRODUCT_MUTATION_ENABLED_FIX_317,
    CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317,
    CONTINUOUS_IMPROVEMENT_COMPOSES_EVIDENCE_ONLY_FIX_317,
    CONTINUOUS_PRODUCT_IMPROVEMENT_DOMAINS,
    CONTINUOUS_PRODUCT_IMPROVEMENT_FIX,
    CONTINUOUS_PRODUCT_IMPROVEMENT_INVARIANT,
    CONTINUOUS_PRODUCT_IMPROVEMENT_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_317,
    FORBIDDEN_CONTINUOUS_IMPROVEMENT_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_317,
    HUMAN_IMPROVEMENT_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_317,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_evaluator import (
    build_commercial_improvement_report,
    build_feedback_intelligence_report,
    build_governance_improvement_report,
    build_improvement_opportunity_registry,
    build_improvement_priority_matrix,
    build_onboarding_improvement_report,
    build_operational_improvement_report,
    build_product_experience_improvement_report,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_evidence import (
    collect_improvement_evidence,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_store import (
    has_improvement_review_decision_approve,
    list_improvement_review_records,
)


@dataclass(frozen=True)
class ContinuousProductImprovementResult:
    ok: bool
    session_id: str
    continuous_product_improvement: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_continuous_product_improvement(*, session_id: str = "default") -> ContinuousProductImprovementResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_improvement_evidence(session_id=sid)

    feedback_intelligence_report = build_feedback_intelligence_report(evidence=evidence)
    onboarding_improvement_report = build_onboarding_improvement_report(evidence=evidence)
    product_experience_improvement_report = build_product_experience_improvement_report(evidence=evidence)
    operational_improvement_report = build_operational_improvement_report(evidence=evidence)
    governance_improvement_report = build_governance_improvement_report(evidence=evidence)
    commercial_improvement_report = build_commercial_improvement_report(evidence=evidence)

    reports = {
        "feedback_intelligence_report": feedback_intelligence_report,
        "onboarding_improvement_report": onboarding_improvement_report,
        "product_experience_improvement_report": product_experience_improvement_report,
        "operational_improvement_report": operational_improvement_report,
        "governance_improvement_report": governance_improvement_report,
        "commercial_improvement_report": commercial_improvement_report,
    }
    improvement_opportunity_registry = build_improvement_opportunity_registry(reports=reports)
    improvement_priority_matrix = build_improvement_priority_matrix(registry=improvement_opportunity_registry)

    top_opportunity = (improvement_priority_matrix.get("ranked_opportunities") or [{}])[0]
    continuous_improvement_dashboard = {
        "opportunity_count": improvement_opportunity_registry.get("count", 0),
        "top_opportunity": top_opportunity.get("title"),
        "top_priority_score": top_opportunity.get("priority_score"),
        "feedback_signals": len(feedback_intelligence_report.get("opportunities") or []),
        "onboarding_friction_points": len(onboarding_improvement_report.get("friction_points") or []),
        "operational_blockers": len(operational_improvement_report.get("operational_bottlenecks") or []),
        "commercial_friction_signals": len(commercial_improvement_report.get("plan_friction_signals") or []),
        "human_improvement_review_decision_approve": has_improvement_review_decision_approve(session_id=sid),
        "core_principle": "improvement_recommendations ≠ automatic_execution",
    }
    improvement_review_registry = {
        "records": list_improvement_review_records(),
        "commands": (
            "improvement note: ...",
            "improvement review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "feedback_intelligence_report": [feedback_intelligence_report],
        "onboarding_improvement_report": [onboarding_improvement_report],
        "product_experience_improvement_report": [product_experience_improvement_report],
        "operational_improvement_report": [operational_improvement_report],
        "governance_improvement_report": [governance_improvement_report],
        "commercial_improvement_report": [commercial_improvement_report],
        "improvement_opportunity_registry": [improvement_opportunity_registry],
        "improvement_priority_matrix": [improvement_priority_matrix],
        "continuous_improvement_dashboard": [continuous_improvement_dashboard],
        "improvement_review_registry": [improvement_review_registry],
    }

    blockers = [
        blocker
        for report in reports.values()
        for blocker in (report.get("blockers") or [])
        if blocker
    ][:8]

    board = {
        "schema_version": CONTINUOUS_PRODUCT_IMPROVEMENT_SCHEMA_VERSION,
        "fix": CONTINUOUS_PRODUCT_IMPROVEMENT_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": CONTINUOUS_PRODUCT_IMPROVEMENT_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_317,
        "execution_performed": EXECUTION_PERFORMED_FIX_317,
        "continuous_improvement_authority": CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317,
        "automatic_backlog_creation_enabled": AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317,
        "automatic_feature_creation_enabled": AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_317,
        "automatic_product_mutation_enabled": AUTOMATIC_PRODUCT_MUTATION_ENABLED_FIX_317,
        "continuous_improvement_compose_artifacts_only": CONTINUOUS_IMPROVEMENT_COMPOSES_EVIDENCE_ONLY_FIX_317,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_317,
        "domains": list(CONTINUOUS_PRODUCT_IMPROVEMENT_DOMAINS),
        "human_improvement_review_decision_kinds": list(HUMAN_IMPROVEMENT_REVIEW_DECISION_KINDS),
        "forbidden_continuous_improvement_actions": [label for label, _detail in FORBIDDEN_CONTINUOUS_IMPROVEMENT_ACTIONS],
        "fix_317_certification_requirements": list(FIX_317_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return ContinuousProductImprovementResult(
        ok=True,
        session_id=sid,
        continuous_product_improvement=board,
        blockers=blockers,
        detail="Continuous product improvement composed from FIX 300–313 evidence without automatic execution.",
    )

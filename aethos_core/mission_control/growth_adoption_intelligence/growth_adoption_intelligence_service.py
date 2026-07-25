# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — growth & adoption intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_320_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_contract import (
    AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_320,
    AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_320,
    AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320,
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_320,
    FORBIDDEN_GROWTH_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_320,
    GROWTH_ADOPTION_COMPOSES_EVIDENCE_ONLY_FIX_320,
    GROWTH_ADOPTION_INTELLIGENCE_DOMAINS,
    GROWTH_ADOPTION_INTELLIGENCE_FIX,
    GROWTH_ADOPTION_INTELLIGENCE_INVARIANT,
    GROWTH_ADOPTION_INTELLIGENCE_SCHEMA_VERSION,
    GROWTH_AUTHORITY_FIX_320,
    GROWTH_CORE_PRINCIPLE,
    HUMAN_GROWTH_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_320,
    PRIVACY_REQUIREMENTS,
    EXECUTION_PERFORMED_FIX_320,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_evaluator import (
    build_adoption_analytics_report,
    build_adoption_registry,
    build_churn_risk_report,
    build_expansion_intelligence_report,
    build_growth_opportunity_registry,
    build_growth_priority_matrix,
    build_retention_intelligence_report,
    build_success_pattern_report,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_evidence import (
    collect_growth_evidence,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_store import (
    has_growth_review_decision_approve,
    list_growth_review_records,
)


@dataclass(frozen=True)
class GrowthAdoptionIntelligenceResult:
    ok: bool
    session_id: str
    growth_adoption_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_growth_adoption_intelligence(*, session_id: str = "default") -> GrowthAdoptionIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_growth_evidence(session_id=sid)

    adoption_registry = build_adoption_registry(evidence=evidence)
    adoption_analytics_report = build_adoption_analytics_report(evidence=evidence)
    retention_intelligence_report = build_retention_intelligence_report(evidence=evidence)
    expansion_intelligence_report = build_expansion_intelligence_report(evidence=evidence)
    success_pattern_report = build_success_pattern_report(evidence=evidence)
    churn_risk_report = build_churn_risk_report(evidence=evidence)
    growth_opportunity_registry = build_growth_opportunity_registry(
        adoption_report=adoption_analytics_report,
        retention_report=retention_intelligence_report,
        expansion_report=expansion_intelligence_report,
        churn_report=churn_risk_report,
        success_report=success_pattern_report,
    )
    growth_priority_matrix = build_growth_priority_matrix(registry=growth_opportunity_registry)

    growth_adoption_dashboard = {
        "activated_customers": adoption_registry.get("activated_customers", 0),
        "adoption_rate_percent": adoption_analytics_report.get("adoption_rate_percent", 0),
        "adoption_velocity_score": adoption_analytics_report.get("adoption_velocity_score", 0),
        "retained_customers": retention_intelligence_report.get("retained_customers", 0),
        "disengaged_customers": retention_intelligence_report.get("disengaged_customers", 0),
        "workspace_growth": expansion_intelligence_report.get("workspace_growth", 0),
        "project_growth": expansion_intelligence_report.get("project_growth", 0),
        "success_pattern_count": len(success_pattern_report.get("behaviors_linked_to_success") or []),
        "churn_risk_score": churn_risk_report.get("churn_risk_score", 0),
        "growth_opportunity_count": growth_opportunity_registry.get("count", 0),
        "top_growth_opportunity": (growth_priority_matrix.get("ranked_opportunities") or [{}])[0],
        "human_growth_review_decision_approve": has_growth_review_decision_approve(session_id=sid),
        "core_principle": GROWTH_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_growth_execution_forbidden": True,
    }
    growth_review_registry = {
        "records": list_growth_review_records(),
        "commands": (
            "growth note: ...",
            "growth review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "adoption_registry": [adoption_registry],
        "adoption_analytics_report": [adoption_analytics_report],
        "retention_intelligence_report": [retention_intelligence_report],
        "expansion_intelligence_report": [expansion_intelligence_report],
        "success_pattern_report": [success_pattern_report],
        "churn_risk_report": [churn_risk_report],
        "growth_opportunity_registry": [growth_opportunity_registry],
        "growth_priority_matrix": [growth_priority_matrix],
        "growth_adoption_dashboard": [growth_adoption_dashboard],
        "growth_review_registry": [growth_review_registry],
    }

    board = {
        "schema_version": GROWTH_ADOPTION_INTELLIGENCE_SCHEMA_VERSION,
        "fix": GROWTH_ADOPTION_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": GROWTH_ADOPTION_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_320,
        "execution_performed": EXECUTION_PERFORMED_FIX_320,
        "growth_authority": GROWTH_AUTHORITY_FIX_320,
        "automatic_customer_outreach_enabled": AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_320,
        "automatic_plan_upgrade_enabled": AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_320,
        "automatic_customer_targeting_enabled": AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_320,
        "automatic_growth_execution_enabled": AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320,
        "growth_adoption_compose_artifacts_only": GROWTH_ADOPTION_COMPOSES_EVIDENCE_ONLY_FIX_320,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_320,
        "domains": list(GROWTH_ADOPTION_INTELLIGENCE_DOMAINS),
        "human_growth_review_decision_kinds": list(HUMAN_GROWTH_REVIEW_DECISION_KINDS),
        "forbidden_growth_actions": [label for label, _detail in FORBIDDEN_GROWTH_ACTIONS],
        "fix_320_certification_requirements": list(FIX_320_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return GrowthAdoptionIntelligenceResult(
        ok=True,
        session_id=sid,
        growth_adoption_intelligence=board,
        detail="Growth & adoption intelligence composed without automatic growth execution.",
    )

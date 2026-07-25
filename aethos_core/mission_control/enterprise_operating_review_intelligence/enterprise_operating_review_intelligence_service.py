# SPDX-License-Identifier: Apache-2.0
"""FIX 329 — enterprise operating review intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_329_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_contract import (
    AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_329,
    AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_329,
    AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_329,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_329,
    ENTERPRISE_OPERATING_CORE_PRINCIPLE,
    ENTERPRISE_OPERATING_REVIEW_COMPOSES_EVIDENCE_ONLY_FIX_329,
    ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_DOMAINS,
    ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_FIX,
    ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_INVARIANT,
    ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_329,
    FORBIDDEN_OPERATING_REVIEW_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_329,
    HUMAN_OPERATING_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_329,
    OPERATING_REVIEW_AUTHORITY_FIX_329,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_evaluator import (
    build_enterprise_operating_dashboard,
    build_enterprise_opportunity_review,
    build_enterprise_risk_review,
    build_executive_action_registry,
    build_executive_operating_scorecard,
    build_executive_operating_snapshot,
    build_organizational_health_review,
    build_program_health_review,
    build_strategic_health_review,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_evidence import (
    collect_enterprise_operating_review_evidence,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_store import (
    has_operating_review_decision_approve,
    list_operating_review_records,
)


@dataclass(frozen=True)
class EnterpriseOperatingReviewIntelligenceResult:
    ok: bool
    session_id: str
    enterprise_operating_review_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_enterprise_operating_review_intelligence(
    *, session_id: str = "default"
) -> EnterpriseOperatingReviewIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_enterprise_operating_review_evidence(session_id=sid)

    executive_operating_snapshot = build_executive_operating_snapshot(evidence=evidence)
    strategic_health_review = build_strategic_health_review(evidence=evidence)
    program_health_review = build_program_health_review(evidence=evidence)
    organizational_health_review = build_organizational_health_review(evidence=evidence)
    enterprise_risk_review = build_enterprise_risk_review(evidence=evidence)
    enterprise_opportunity_review = build_enterprise_opportunity_review(evidence=evidence)
    executive_action_registry = build_executive_action_registry(
        snapshot=executive_operating_snapshot,
        risk_review=enterprise_risk_review,
        opportunity_review=enterprise_opportunity_review,
        program_review=program_health_review,
        organization_review=organizational_health_review,
    )
    executive_operating_scorecard = build_executive_operating_scorecard(
        strategic_review=strategic_health_review,
        program_review=program_health_review,
        organization_review=organizational_health_review,
        risk_review=enterprise_risk_review,
        snapshot=executive_operating_snapshot,
    )
    enterprise_operating_dashboard = build_enterprise_operating_dashboard(
        snapshot=executive_operating_snapshot,
        strategic_review=strategic_health_review,
        program_review=program_health_review,
        organization_review=organizational_health_review,
        risk_review=enterprise_risk_review,
        opportunity_review=enterprise_opportunity_review,
        action_registry=executive_action_registry,
        scorecard=executive_operating_scorecard,
    )
    enterprise_operating_dashboard["human_operating_review_decision_approve"] = has_operating_review_decision_approve(
        session_id=sid
    )

    executive_operating_review_registry = {
        "records": list_operating_review_records(),
        "commands": (
            "operating review note: ...",
            "operating review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "executive_operating_snapshot": [executive_operating_snapshot],
        "strategic_health_review": [strategic_health_review],
        "program_health_review": [program_health_review],
        "organizational_health_review": [organizational_health_review],
        "enterprise_risk_review": [enterprise_risk_review],
        "enterprise_opportunity_review": [enterprise_opportunity_review],
        "executive_action_registry": [executive_action_registry],
        "executive_operating_scorecard": [executive_operating_scorecard],
        "enterprise_operating_dashboard": [enterprise_operating_dashboard],
        "executive_operating_review_registry": [executive_operating_review_registry],
    }

    board = {
        "schema_version": ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_SCHEMA_VERSION,
        "fix": ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_329,
        "execution_performed": EXECUTION_PERFORMED_FIX_329,
        "operating_review_authority": OPERATING_REVIEW_AUTHORITY_FIX_329,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_329,
        "automatic_program_execution_enabled": AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_329,
        "automatic_organizational_changes_enabled": AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_329,
        "automatic_decision_execution_enabled": AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_329,
        "enterprise_operating_review_compose_artifacts_only": ENTERPRISE_OPERATING_REVIEW_COMPOSES_EVIDENCE_ONLY_FIX_329,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_329,
        "domains": list(ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_DOMAINS),
        "human_operating_review_decision_kinds": list(HUMAN_OPERATING_REVIEW_DECISION_KINDS),
        "forbidden_operating_review_actions": [label for label, _detail in FORBIDDEN_OPERATING_REVIEW_ACTIONS],
        "core_principle": ENTERPRISE_OPERATING_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "fix_329_certification_requirements": list(FIX_329_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return EnterpriseOperatingReviewIntelligenceResult(
        ok=True,
        session_id=sid,
        enterprise_operating_review_intelligence=board,
        detail="Enterprise operating review intelligence composed without executive authority.",
    )

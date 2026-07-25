# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — customer feedback intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_319_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_contract import (
    AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319,
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_319,
    AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_319,
    CUSTOMER_FEEDBACK_COMPOSES_EVIDENCE_ONLY_FIX_319,
    CUSTOMER_FEEDBACK_INTELLIGENCE_DOMAINS,
    CUSTOMER_FEEDBACK_INTELLIGENCE_FIX,
    CUSTOMER_FEEDBACK_INTELLIGENCE_INVARIANT,
    CUSTOMER_FEEDBACK_INTELLIGENCE_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_319,
    FEEDBACK_AUTHORITY_FIX_319,
    FEEDBACK_CORE_PRINCIPLE,
    FORBIDDEN_FEEDBACK_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_319,
    HUMAN_FEEDBACK_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_319,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_evaluator import (
    build_capability_gap_report,
    build_customer_feedback_registry,
    build_customer_friction_report,
    build_feedback_classification_report,
    build_feedback_opportunity_registry,
    build_feedback_priority_matrix,
    build_feedback_sentiment_report,
    build_feedback_trend_report,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_evidence import (
    collect_feedback_evidence,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_store import (
    has_feedback_review_decision_approve,
    list_feedback_review_records,
)


@dataclass(frozen=True)
class CustomerFeedbackIntelligenceResult:
    ok: bool
    session_id: str
    customer_feedback_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_customer_feedback_intelligence(*, session_id: str = "default") -> CustomerFeedbackIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_feedback_evidence(session_id=sid)

    customer_feedback_registry = build_customer_feedback_registry(evidence=evidence)
    items = list(customer_feedback_registry.get("items") or [])
    feedback_classification_report = build_feedback_classification_report(items=items)
    classified_items = list(feedback_classification_report.get("items") or [])
    feedback_sentiment_report = build_feedback_sentiment_report(items=items)
    feedback_trend_report = build_feedback_trend_report(classified_items=classified_items)
    capability_gap_report = build_capability_gap_report(evidence=evidence, classified_items=classified_items)
    customer_friction_report = build_customer_friction_report(evidence=evidence)
    feedback_opportunity_registry = build_feedback_opportunity_registry(
        classified_items=classified_items,
        trend_report=feedback_trend_report,
        capability_gap_report=capability_gap_report,
        friction_report=customer_friction_report,
    )
    feedback_priority_matrix = build_feedback_priority_matrix(registry=feedback_opportunity_registry)

    sentiment_counts = feedback_sentiment_report.get("counts_by_sentiment") or {}
    classification_counts = feedback_classification_report.get("counts_by_classification") or {}
    customer_feedback_dashboard = {
        "feedback_item_count": customer_feedback_registry.get("count", 0),
        "positive_sentiment_count": sentiment_counts.get("positive", 0),
        "negative_sentiment_count": sentiment_counts.get("negative", 0),
        "recurring_request_count": len(feedback_trend_report.get("recurring_requests") or []),
        "recurring_complaint_count": len(feedback_trend_report.get("recurring_complaints") or []),
        "emerging_theme_count": len(feedback_trend_report.get("emerging_themes") or []),
        "capability_gap_count": len(capability_gap_report.get("gaps") or []),
        "onboarding_friction_count": len(customer_friction_report.get("onboarding_friction") or []),
        "provider_friction_count": len(customer_friction_report.get("provider_friction") or []),
        "opportunity_count": feedback_opportunity_registry.get("count", 0),
        "top_priority": (feedback_priority_matrix.get("ranked_opportunities") or [{}])[0],
        "top_classification": (
            max(classification_counts, key=classification_counts.get) if classification_counts else "—"
        ),
        "human_feedback_review_decision_approve": has_feedback_review_decision_approve(session_id=sid),
        "core_principle": FEEDBACK_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_work_creation_forbidden": True,
    }
    feedback_review_registry = {
        "records": list_feedback_review_records(),
        "commands": (
            "feedback note: ...",
            "feedback review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "customer_feedback_registry": [customer_feedback_registry],
        "feedback_classification_report": [feedback_classification_report],
        "feedback_sentiment_report": [feedback_sentiment_report],
        "feedback_trend_report": [feedback_trend_report],
        "capability_gap_report": [capability_gap_report],
        "customer_friction_report": [customer_friction_report],
        "feedback_opportunity_registry": [feedback_opportunity_registry],
        "feedback_priority_matrix": [feedback_priority_matrix],
        "customer_feedback_dashboard": [customer_feedback_dashboard],
        "feedback_review_registry": [feedback_review_registry],
    }

    board = {
        "schema_version": CUSTOMER_FEEDBACK_INTELLIGENCE_SCHEMA_VERSION,
        "fix": CUSTOMER_FEEDBACK_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": CUSTOMER_FEEDBACK_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_319,
        "execution_performed": EXECUTION_PERFORMED_FIX_319,
        "feedback_authority": FEEDBACK_AUTHORITY_FIX_319,
        "automatic_feature_creation_enabled": AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_319,
        "automatic_backlog_creation_enabled": AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319,
        "automatic_customer_contact_enabled": AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_319,
        "customer_feedback_compose_artifacts_only": CUSTOMER_FEEDBACK_COMPOSES_EVIDENCE_ONLY_FIX_319,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_319,
        "domains": list(CUSTOMER_FEEDBACK_INTELLIGENCE_DOMAINS),
        "human_feedback_review_decision_kinds": list(HUMAN_FEEDBACK_REVIEW_DECISION_KINDS),
        "forbidden_feedback_actions": [label for label, _detail in FORBIDDEN_FEEDBACK_ACTIONS],
        "fix_319_certification_requirements": list(FIX_319_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return CustomerFeedbackIntelligenceResult(
        ok=True,
        session_id=sid,
        customer_feedback_intelligence=board,
        detail="Customer feedback intelligence composed without automatic work creation.",
    )

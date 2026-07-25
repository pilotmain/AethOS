# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — product analytics foundation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_318_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
    ANALYTICS_AUTHORITY_FIX_318,
    ANALYTICS_CORE_PRINCIPLE,
    AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318,
    AUTOMATIC_PLAN_MUTATION_ENABLED_FIX_318,
    AUTOMATIC_USER_TARGETING_ENABLED_FIX_318,
    EXECUTION_PERFORMED_FIX_318,
    FORBIDDEN_ANALYTICS_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_318,
    HUMAN_ANALYTICS_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_318,
    PRIVACY_PRINCIPLES,
    PRODUCT_ANALYTICS_COMPOSES_EVIDENCE_ONLY_FIX_318,
    PRODUCT_ANALYTICS_FOUNDATION_DOMAINS,
    PRODUCT_ANALYTICS_FOUNDATION_FIX,
    PRODUCT_ANALYTICS_FOUNDATION_INVARIANT,
    PRODUCT_ANALYTICS_FOUNDATION_SCHEMA_VERSION,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evaluator import (
    build_analytics_event_registry,
    build_behavioral_opportunity_registry,
    build_capability_usage_report,
    build_commercial_analytics_report,
    build_customer_success_analytics_report,
    build_onboarding_analytics_report,
    build_provider_analytics_report,
    build_user_journey_report,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evidence import (
    collect_analytics_evidence,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_store import (
    has_analytics_review_decision_approve,
    list_analytics_review_records,
)


@dataclass(frozen=True)
class ProductAnalyticsFoundationResult:
    ok: bool
    session_id: str
    product_analytics_foundation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_product_analytics_foundation(*, session_id: str = "default") -> ProductAnalyticsFoundationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_analytics_evidence(session_id=sid)

    analytics_event_registry = build_analytics_event_registry(evidence=evidence)
    user_journey_report = build_user_journey_report(evidence=evidence)
    onboarding_analytics_report = build_onboarding_analytics_report(evidence=evidence)
    capability_usage_report = build_capability_usage_report(evidence=evidence)
    provider_analytics_report = build_provider_analytics_report(evidence=evidence)
    commercial_analytics_report = build_commercial_analytics_report(evidence=evidence)
    customer_success_analytics_report = build_customer_success_analytics_report(evidence=evidence)
    behavioral_opportunity_registry = build_behavioral_opportunity_registry(
        onboarding_report=onboarding_analytics_report,
        capability_report=capability_usage_report,
        provider_report=provider_analytics_report,
        journey_report=user_journey_report,
    )

    analytics_dashboard = {
        "onboarding_completion_rate_percent": onboarding_analytics_report.get("average_completion_rate_percent"),
        "users_completed_onboarding": onboarding_analytics_report.get("users_completed_onboarding"),
        "most_connected_provider": provider_analytics_report.get("most_connected_provider"),
        "capabilities_used_count": len(capability_usage_report.get("capabilities_used") or []),
        "active_subscription_count": commercial_analytics_report.get("active_subscription_count"),
        "healthy_customers": customer_success_analytics_report.get("healthy_customers"),
        "at_risk_customers": customer_success_analytics_report.get("at_risk_customers"),
        "behavioral_opportunity_count": behavioral_opportunity_registry.get("count", 0),
        "human_analytics_review_decision_approve": has_analytics_review_decision_approve(session_id=sid),
        "core_principle": ANALYTICS_CORE_PRINCIPLE,
        "privacy_principles": list(PRIVACY_PRINCIPLES),
    }
    analytics_review_registry = {
        "records": list_analytics_review_records(),
        "commands": (
            "analytics note: ...",
            "analytics review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "analytics_event_registry": [analytics_event_registry],
        "user_journey_report": [user_journey_report],
        "onboarding_analytics_report": [onboarding_analytics_report],
        "capability_usage_report": [capability_usage_report],
        "provider_analytics_report": [provider_analytics_report],
        "commercial_analytics_report": [commercial_analytics_report],
        "customer_success_analytics_report": [customer_success_analytics_report],
        "behavioral_opportunity_registry": [behavioral_opportunity_registry],
        "analytics_dashboard": [analytics_dashboard],
        "analytics_review_registry": [analytics_review_registry],
    }

    board = {
        "schema_version": PRODUCT_ANALYTICS_FOUNDATION_SCHEMA_VERSION,
        "fix": PRODUCT_ANALYTICS_FOUNDATION_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": PRODUCT_ANALYTICS_FOUNDATION_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_318,
        "execution_performed": EXECUTION_PERFORMED_FIX_318,
        "analytics_authority": ANALYTICS_AUTHORITY_FIX_318,
        "automatic_behavior_modification_enabled": AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318,
        "automatic_user_targeting_enabled": AUTOMATIC_USER_TARGETING_ENABLED_FIX_318,
        "automatic_plan_mutation_enabled": AUTOMATIC_PLAN_MUTATION_ENABLED_FIX_318,
        "product_analytics_compose_artifacts_only": PRODUCT_ANALYTICS_COMPOSES_EVIDENCE_ONLY_FIX_318,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_318,
        "domains": list(PRODUCT_ANALYTICS_FOUNDATION_DOMAINS),
        "human_analytics_review_decision_kinds": list(HUMAN_ANALYTICS_REVIEW_DECISION_KINDS),
        "forbidden_analytics_actions": [label for label, _detail in FORBIDDEN_ANALYTICS_ACTIONS],
        "fix_318_certification_requirements": list(FIX_318_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return ProductAnalyticsFoundationResult(
        ok=True,
        session_id=sid,
        product_analytics_foundation=board,
        detail="Product analytics foundation composed from tenant-scoped behavioral evidence without surveillance.",
    )

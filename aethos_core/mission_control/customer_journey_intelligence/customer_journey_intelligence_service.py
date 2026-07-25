# SPDX-License-Identifier: Apache-2.0
"""FIX 321 — customer journey intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_321_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_contract import (
    AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321,
    AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_321,
    AUTOMATIC_JOURNEY_MODIFICATION_ENABLED_FIX_321,
    CUSTOMER_JOURNEY_COMPOSES_EVIDENCE_ONLY_FIX_321,
    CUSTOMER_JOURNEY_INTELLIGENCE_DOMAINS,
    CUSTOMER_JOURNEY_INTELLIGENCE_FIX,
    CUSTOMER_JOURNEY_INTELLIGENCE_INVARIANT,
    CUSTOMER_JOURNEY_INTELLIGENCE_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_321,
    FORBIDDEN_JOURNEY_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_321,
    HUMAN_JOURNEY_REVIEW_DECISION_KINDS,
    JOURNEY_AUTHORITY_FIX_321,
    JOURNEY_CORE_PRINCIPLE,
    JOURNEY_STAGES,
    MUTATION_PERFORMED_FIX_321,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_evaluator import (
    build_customer_journey_registry,
    build_journey_cohort_report,
    build_journey_dropoff_report,
    build_journey_friction_report,
    build_journey_funnel_report,
    build_journey_opportunity_registry,
    build_journey_priority_matrix,
    build_journey_success_report,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_evidence import (
    collect_journey_evidence,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_store import (
    has_journey_review_decision_approve,
    list_journey_review_records,
)


@dataclass(frozen=True)
class CustomerJourneyIntelligenceResult:
    ok: bool
    session_id: str
    customer_journey_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_customer_journey_intelligence(*, session_id: str = "default") -> CustomerJourneyIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_journey_evidence(session_id=sid)

    customer_journey_registry = build_customer_journey_registry(evidence=evidence)
    journey_funnel_report = build_journey_funnel_report(evidence=evidence)
    journey_dropoff_report = build_journey_dropoff_report(evidence=evidence)
    journey_success_report = build_journey_success_report(evidence=evidence)
    journey_friction_report = build_journey_friction_report(evidence=evidence)
    journey_cohort_report = build_journey_cohort_report(evidence=evidence)
    journey_opportunity_registry = build_journey_opportunity_registry(
        dropoff_report=journey_dropoff_report,
        friction_report=journey_friction_report,
        success_report=journey_success_report,
        cohort_report=journey_cohort_report,
    )
    journey_priority_matrix = build_journey_priority_matrix(registry=journey_opportunity_registry)

    customer_journey_dashboard = {
        "current_stage": customer_journey_registry.get("current_stage"),
        "journey_stage_count": len(JOURNEY_STAGES),
        "completed_stages": sum(
            1
            for entry in customer_journey_registry.get("entries") or []
            if entry.get("progression_state") == "completed"
        ),
        "stalled_journey_count": len(journey_dropoff_report.get("stalled_journeys") or []),
        "dropoff_point_count": len(journey_dropoff_report.get("abandonment_points") or []),
        "successful_path_count": len(journey_success_report.get("successful_paths") or []),
        "friction_hotspot_count": len(journey_dropoff_report.get("friction_hotspots") or []),
        "cohort_count": len(journey_cohort_report.get("cohorts") or []),
        "journey_opportunity_count": journey_opportunity_registry.get("count", 0),
        "top_priority": (journey_priority_matrix.get("ranked_opportunities") or [{}])[0],
        "human_journey_review_decision_approve": has_journey_review_decision_approve(session_id=sid),
        "core_principle": JOURNEY_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_customer_intervention_forbidden": True,
    }
    journey_review_registry = {
        "records": list_journey_review_records(),
        "commands": (
            "journey note: ...",
            "journey review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "customer_journey_registry": [customer_journey_registry],
        "journey_funnel_report": [journey_funnel_report],
        "journey_dropoff_report": [journey_dropoff_report],
        "journey_success_report": [journey_success_report],
        "journey_friction_report": [journey_friction_report],
        "journey_cohort_report": [journey_cohort_report],
        "journey_opportunity_registry": [journey_opportunity_registry],
        "journey_priority_matrix": [journey_priority_matrix],
        "customer_journey_dashboard": [customer_journey_dashboard],
        "journey_review_registry": [journey_review_registry],
    }

    board = {
        "schema_version": CUSTOMER_JOURNEY_INTELLIGENCE_SCHEMA_VERSION,
        "fix": CUSTOMER_JOURNEY_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": CUSTOMER_JOURNEY_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_321,
        "execution_performed": EXECUTION_PERFORMED_FIX_321,
        "journey_authority": JOURNEY_AUTHORITY_FIX_321,
        "automatic_customer_targeting_enabled": AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_321,
        "automatic_customer_intervention_enabled": AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321,
        "automatic_journey_modification_enabled": AUTOMATIC_JOURNEY_MODIFICATION_ENABLED_FIX_321,
        "customer_journey_compose_artifacts_only": CUSTOMER_JOURNEY_COMPOSES_EVIDENCE_ONLY_FIX_321,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_321,
        "domains": list(CUSTOMER_JOURNEY_INTELLIGENCE_DOMAINS),
        "journey_stages": list(JOURNEY_STAGES),
        "human_journey_review_decision_kinds": list(HUMAN_JOURNEY_REVIEW_DECISION_KINDS),
        "forbidden_journey_actions": [label for label, _detail in FORBIDDEN_JOURNEY_ACTIONS],
        "fix_321_certification_requirements": list(FIX_321_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return CustomerJourneyIntelligenceResult(
        ok=True,
        session_id=sid,
        customer_journey_intelligence=board,
        detail="Customer journey intelligence composed without customer manipulation.",
    )

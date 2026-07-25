# SPDX-License-Identifier: Apache-2.0
"""FIX 323 — customer value realization intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_323_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_contract import (
    AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_323,
    AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323,
    AUTOMATIC_GOAL_MODIFICATION_ENABLED_FIX_323,
    CUSTOMER_VALUE_REALIZATION_COMPOSES_EVIDENCE_ONLY_FIX_323,
    CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_DOMAINS,
    CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_FIX,
    CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_INVARIANT,
    CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_323,
    FORBIDDEN_VALUE_REALIZATION_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_323,
    HUMAN_VALUE_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_323,
    PRIVACY_REQUIREMENTS,
    VALUE_REALIZATION_AUTHORITY_FIX_323,
    VALUE_REALIZATION_CORE_PRINCIPLE,
    VALUE_REALIZATION_SCORECARD_DIMENSIONS,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_evaluator import (
    build_capability_value_report,
    build_customer_success_outcome_report,
    build_customer_value_dashboard,
    build_expected_value_registry,
    build_journey_value_report,
    build_value_gap_report,
    build_value_opportunity_registry,
    build_value_outcome_registry,
    build_value_realization_scorecard,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_evidence import (
    collect_value_realization_evidence,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_store import (
    has_value_review_decision_approve,
    list_value_review_records,
)


@dataclass(frozen=True)
class CustomerValueRealizationIntelligenceResult:
    ok: bool
    session_id: str
    customer_value_realization_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_customer_value_realization_intelligence(
    *, session_id: str = "default"
) -> CustomerValueRealizationIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"

    from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guard import (
        evaluate_heavy_compose_guard,
    )
    from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalable_compose_bridge import (
        load_pmf_snapshot,
        load_value_realization_snapshot,
    )

    value_snapshot = load_value_realization_snapshot(session_id=sid)
    pmf_snapshot = load_pmf_snapshot(session_id=sid)
    guard = evaluate_heavy_compose_guard(
        module="FIX 323",
        session_id=sid,
        snapshot_available=bool(value_snapshot or pmf_snapshot),
    )
    if not guard.allowed and guard.mode != "test":
        if value_snapshot:
            return CustomerValueRealizationIntelligenceResult(
                ok=True,
                session_id=sid,
                customer_value_realization_intelligence=value_snapshot,
                detail="Value realization intelligence served from snapshot — heavy compose guarded.",
            )
        return CustomerValueRealizationIntelligenceResult(
            ok=True,
            session_id=sid,
            customer_value_realization_intelligence={
                "schema_version": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_SCHEMA_VERSION,
                "fix": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_FIX,
                "session_id": sid,
                "read_only": True,
                "runtime_guardrail_blocked": True,
                "runtime_mode": guard.mode,
                "detail": (
                    "Heavy FIX 323 compose blocked in operator mode. "
                    "Use `run full evidence benchmark` for full evidence compose."
                ),
                "sections": {},
            },
            blockers=["heavy_compose_guarded"],
            detail="Heavy FIX 323 compose guarded — snapshot unavailable.",
        )

    evidence = collect_value_realization_evidence(session_id=sid)

    value_outcome_registry = build_value_outcome_registry(evidence=evidence)
    expected_value_registry = build_expected_value_registry(evidence=evidence)
    value_gap_report = build_value_gap_report(
        outcome_registry=value_outcome_registry,
        expected_registry=expected_value_registry,
        evidence=evidence,
    )
    capability_value_report = build_capability_value_report(evidence=evidence)
    journey_value_report = build_journey_value_report(evidence=evidence)
    customer_success_outcome_report = build_customer_success_outcome_report(evidence=evidence)
    value_realization_scorecard = build_value_realization_scorecard(
        outcome_registry=value_outcome_registry,
        gap_report=value_gap_report,
        capability_value=capability_value_report,
        success_outcome=customer_success_outcome_report,
        evidence=evidence,
    )
    value_opportunity_registry = build_value_opportunity_registry(
        gap_report=value_gap_report,
        capability_value=capability_value_report,
        journey_value=journey_value_report,
        success_outcome=customer_success_outcome_report,
    )
    customer_value_dashboard = build_customer_value_dashboard(
        outcome_registry=value_outcome_registry,
        expected_registry=expected_value_registry,
        gap_report=value_gap_report,
        capability_value=capability_value_report,
        journey_value=journey_value_report,
        success_outcome=customer_success_outcome_report,
        scorecard=value_realization_scorecard,
        opportunity_registry=value_opportunity_registry,
    )
    customer_value_dashboard["human_value_review_decision_approve"] = has_value_review_decision_approve(session_id=sid)

    value_review_registry = {
        "records": list_value_review_records(),
        "commands": (
            "value note: ...",
            "value review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "value_outcome_registry": [value_outcome_registry],
        "expected_value_registry": [expected_value_registry],
        "value_gap_report": [value_gap_report],
        "capability_value_report": [capability_value_report],
        "journey_value_report": [journey_value_report],
        "customer_success_outcome_report": [customer_success_outcome_report],
        "value_opportunity_registry": [value_opportunity_registry],
        "value_realization_scorecard": [value_realization_scorecard],
        "customer_value_dashboard": [customer_value_dashboard],
        "value_review_registry": [value_review_registry],
    }

    board = {
        "schema_version": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_SCHEMA_VERSION,
        "fix": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_323,
        "execution_performed": EXECUTION_PERFORMED_FIX_323,
        "value_realization_authority": VALUE_REALIZATION_AUTHORITY_FIX_323,
        "automatic_customer_success_enabled": AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323,
        "automatic_customer_outreach_enabled": AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_323,
        "automatic_goal_modification_enabled": AUTOMATIC_GOAL_MODIFICATION_ENABLED_FIX_323,
        "customer_value_realization_compose_artifacts_only": CUSTOMER_VALUE_REALIZATION_COMPOSES_EVIDENCE_ONLY_FIX_323,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_323,
        "domains": list(CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_DOMAINS),
        "value_realization_scorecard_dimensions": list(VALUE_REALIZATION_SCORECARD_DIMENSIONS),
        "human_value_review_decision_kinds": list(HUMAN_VALUE_REVIEW_DECISION_KINDS),
        "forbidden_value_realization_actions": [label for label, _detail in FORBIDDEN_VALUE_REALIZATION_ACTIONS],
        "fix_323_certification_requirements": list(FIX_323_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return CustomerValueRealizationIntelligenceResult(
        ok=True,
        session_id=sid,
        customer_value_realization_intelligence=board,
        detail="Customer value realization intelligence composed without customer success execution.",
    )

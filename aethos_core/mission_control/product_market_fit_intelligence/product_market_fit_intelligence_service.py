# SPDX-License-Identifier: Apache-2.0
"""FIX 322 — product-market fit intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_322_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_contract import (
    AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_322,
    AUTOMATIC_PRICING_CHANGES_ENABLED_FIX_322,
    AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322,
    EXECUTION_PERFORMED_FIX_322,
    FORBIDDEN_PMF_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_322,
    HUMAN_PMF_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_322,
    PMF_AUTHORITY_FIX_322,
    PMF_CORE_PRINCIPLE,
    PMF_SCORECARD_DIMENSIONS,
    PRIVACY_REQUIREMENTS,
    PRODUCT_MARKET_FIT_COMPOSES_EVIDENCE_ONLY_FIX_322,
    PRODUCT_MARKET_FIT_INTELLIGENCE_DOMAINS,
    PRODUCT_MARKET_FIT_INTELLIGENCE_FIX,
    PRODUCT_MARKET_FIT_INTELLIGENCE_INVARIANT,
    PRODUCT_MARKET_FIT_INTELLIGENCE_SCHEMA_VERSION,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_evaluator import (
    build_capability_demand_report,
    build_customer_value_realization_report,
    build_expansion_value_report,
    build_pmf_opportunity_registry,
    build_pmf_scorecard,
    build_problem_solution_fit_report,
    build_product_market_fit_dashboard,
    build_retention_value_report,
    build_value_signal_registry,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_evidence import (
    collect_pmf_evidence,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_store import (
    has_pmf_review_decision_approve,
    list_pmf_review_records,
)


@dataclass(frozen=True)
class ProductMarketFitIntelligenceResult:
    ok: bool
    session_id: str
    product_market_fit_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_product_market_fit_intelligence(*, session_id: str = "default") -> ProductMarketFitIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"

    from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guard import (
        evaluate_heavy_compose_guard,
    )
    from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalable_compose_bridge import (
        load_pmf_snapshot,
    )

    snapshot_board = load_pmf_snapshot(session_id=sid)
    guard = evaluate_heavy_compose_guard(
        module="FIX 322",
        session_id=sid,
        snapshot_available=bool(snapshot_board),
    )
    if not guard.allowed and guard.mode != "test":
        if snapshot_board:
            return ProductMarketFitIntelligenceResult(
                ok=True,
                session_id=sid,
                product_market_fit_intelligence=snapshot_board,
                detail="Product-market fit intelligence served from snapshot — heavy compose guarded.",
            )
        return ProductMarketFitIntelligenceResult(
            ok=True,
            session_id=sid,
            product_market_fit_intelligence={
                "schema_version": PRODUCT_MARKET_FIT_INTELLIGENCE_SCHEMA_VERSION,
                "fix": PRODUCT_MARKET_FIT_INTELLIGENCE_FIX,
                "session_id": sid,
                "read_only": True,
                "runtime_guardrail_blocked": True,
                "runtime_mode": guard.mode,
                "detail": (
                    "Heavy FIX 322 compose blocked in operator mode. "
                    "Use `run critical compose benchmark` for full evidence compose."
                ),
                "sections": {},
            },
            blockers=["heavy_compose_guarded"],
            detail="Heavy FIX 322 compose guarded — snapshot unavailable.",
        )

    evidence = collect_pmf_evidence(session_id=sid)

    value_signal_registry = build_value_signal_registry(evidence=evidence)
    problem_solution_fit_report = build_problem_solution_fit_report(evidence=evidence)
    customer_value_realization_report = build_customer_value_realization_report(evidence=evidence)
    capability_demand_report = build_capability_demand_report(evidence=evidence)
    retention_value_report = build_retention_value_report(evidence=evidence)
    expansion_value_report = build_expansion_value_report(evidence=evidence)
    pmf_scorecard = build_pmf_scorecard(evidence=evidence)
    pmf_opportunity_registry = build_pmf_opportunity_registry(
        problem_solution_report=problem_solution_fit_report,
        value_report=customer_value_realization_report,
        capability_demand=capability_demand_report,
        retention_value=retention_value_report,
        expansion_value=expansion_value_report,
    )
    product_market_fit_dashboard = build_product_market_fit_dashboard(
        value_registry=value_signal_registry,
        problem_solution_report=problem_solution_fit_report,
        value_report=customer_value_realization_report,
        capability_demand=capability_demand_report,
        scorecard=pmf_scorecard,
        opportunity_registry=pmf_opportunity_registry,
    )
    product_market_fit_dashboard["human_pmf_review_decision_approve"] = has_pmf_review_decision_approve(session_id=sid)

    pmf_review_registry = {
        "records": list_pmf_review_records(),
        "commands": (
            "pmf note: ...",
            "pmf review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "value_signal_registry": [value_signal_registry],
        "problem_solution_fit_report": [problem_solution_fit_report],
        "customer_value_realization_report": [customer_value_realization_report],
        "capability_demand_report": [capability_demand_report],
        "retention_value_report": [retention_value_report],
        "expansion_value_report": [expansion_value_report],
        "pmf_opportunity_registry": [pmf_opportunity_registry],
        "pmf_scorecard": [pmf_scorecard],
        "product_market_fit_dashboard": [product_market_fit_dashboard],
        "pmf_review_registry": [pmf_review_registry],
    }

    board = {
        "schema_version": PRODUCT_MARKET_FIT_INTELLIGENCE_SCHEMA_VERSION,
        "fix": PRODUCT_MARKET_FIT_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": PRODUCT_MARKET_FIT_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_322,
        "execution_performed": EXECUTION_PERFORMED_FIX_322,
        "pmf_authority": PMF_AUTHORITY_FIX_322,
        "automatic_product_strategy_enabled": AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322,
        "automatic_feature_creation_enabled": AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_322,
        "automatic_pricing_changes_enabled": AUTOMATIC_PRICING_CHANGES_ENABLED_FIX_322,
        "product_market_fit_compose_artifacts_only": PRODUCT_MARKET_FIT_COMPOSES_EVIDENCE_ONLY_FIX_322,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_322,
        "domains": list(PRODUCT_MARKET_FIT_INTELLIGENCE_DOMAINS),
        "pmf_scorecard_dimensions": list(PMF_SCORECARD_DIMENSIONS),
        "human_pmf_review_decision_kinds": list(HUMAN_PMF_REVIEW_DECISION_KINDS),
        "forbidden_pmf_actions": [label for label, _detail in FORBIDDEN_PMF_ACTIONS],
        "fix_322_certification_requirements": list(FIX_322_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalable_compose_bridge import (
        is_scalable_compose_enabled,
        record_pmf_snapshot,
    )

    if is_scalable_compose_enabled(session_id=sid):
        record_pmf_snapshot(session_id=sid, board=board)

    return ProductMarketFitIntelligenceResult(
        ok=True,
        session_id=sid,
        product_market_fit_intelligence=board,
        detail="Product-market fit intelligence composed without automatic product strategy changes.",
    )

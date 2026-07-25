# SPDX-License-Identifier: Apache-2.0
"""FIX 329 — enterprise operating review intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_contract import (
    AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_329,
    AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_329,
    AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_329,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_329,
    ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_DOMAINS,
    ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_ROUTE_ID,
    ENTERPRISE_RISK_CATEGORIES,
    EXECUTIVE_ACTION_TYPES,
    EXECUTIVE_OPERATING_LEVELS,
    EXECUTIVE_OPERATING_SCORECARD_DIMENSIONS,
    OPERATING_REVIEW_AUTHORITY_FIX_329,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_evaluator import (
    build_enterprise_opportunity_review,
    build_enterprise_risk_review,
    build_executive_action_registry,
    build_executive_operating_scorecard,
    build_executive_operating_snapshot,
    build_organizational_health_review,
    build_program_health_review,
    build_strategic_health_review,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_intent import (
    parse_enterprise_operating_review_intelligence_intent,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_router import (
    route_enterprise_operating_review_intelligence,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_service import (
    build_enterprise_operating_review_intelligence,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_store import (
    append_operating_review_record,
    clear_operating_review_records_for_tests,
    list_operating_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "eori-329",
    "sources_ok": {f"fix_{n}": True for n in (309, 313, 316, 324, 325, 326, 327, 328)},
    "fix_309": {"sections": {"launch_risk_registry": [{"risks": ["Incomplete security checklist"]}]}},
    "fix_313": {"sections": {"launch_blocker_registry": [{"blockers": ["Pending launch review"]}]}},
    "fix_316": {"sections": {"incident_baseline": [{"active_incidents": ["API latency spike"]}]}},
    "fix_324": {
        "sections": {
            "strategic_portfolio_dashboard": [{"business_value_score": 0.75}],
            "strategic_value_report": [{"business_value_score": 0.75}],
            "strategic_alignment_report": [{"alignment_nodes": 6}],
            "investment_opportunity_report": [{"high_value_opportunities": [{"title": "Accelerate Mission Control"}]}],
            "portfolio_risk_report": [{"operational_risk": ["Pending launch review"], "product_risk": ["Security gap"]}],
            "portfolio_opportunity_registry": [{"opportunities": [{"title": "Portfolio acceleration"}]}],
        }
    },
    "fix_325": {
        "sections": {
            "executive_decision_dashboard": [{"pending_decision_count": 2, "recommendation_count": 4}],
            "executive_decision_registry": [{"pending_count": 2, "reviewed_count": 3, "deferred_count": 1}],
            "executive_recommendation_report": [
                {"recommendations": [{"title": "Review governance backlog", "recommendation_level": "REVIEW"}]}
            ],
            "executive_opportunity_registry": [{"opportunities": [{"title": "Expand adoption", "source_type": "growth"}]}],
        }
    },
    "fix_326": {
        "sections": {
            "strategic_planning_dashboard": [{"scenario_count": 5, "generated_plan_count": 5}],
            "strategic_comparison_matrix": [{"strongest_plan": {"scenario": "Balanced growth", "comparison_score": 8.2}}],
            "strategic_risk_forecast": [{"execution_risks": ["Address portfolio risk before acceleration"]}],
            "strategic_opportunity_forecast": [
                {"growth_opportunities": [{"title": "Balanced growth path"}], "efficiency_opportunities": [{"title": "Efficiency optimization"}]}
            ],
        }
    },
    "fix_327": {
        "sections": {
            "program_health_report": [
                {
                    "programs": [{"name": "Mission Control Program", "health_status": "warning"}],
                    "health_status_counts": {"healthy": 1, "warning": 2, "at_risk": 1, "blocked": 1},
                }
            ],
            "enterprise_program_dashboard": [
                {
                    "program_count": 6,
                    "healthy_program_count": 1,
                    "blocked_program_count": 1,
                    "at_risk_program_count": 1,
                    "leadership_intervention_programs": ["Mission Control Program"],
                }
            ],
            "program_risk_report": [{"program_risks": [{"title": "Incomplete security checklist", "risk_signal": "elevated"}]}],
            "program_opportunity_registry": [{"opportunities": [{"title": "Accelerate healthy program", "opportunity_type": "acceleration"}]}],
        }
    },
    "fix_328": {
        "sections": {
            "organizational_effectiveness_scorecard": [
                {
                    "dimension_scores": {
                        "governance": 0.62,
                        "coordination": 0.58,
                        "capacity": 0.55,
                        "decision_velocity": 0.68,
                    },
                    "overall_score": 0.61,
                    "overall_level": "STABLE",
                }
            ],
            "organizational_effectiveness_dashboard": [
                {"overall_effectiveness_level": "STABLE", "friction_signal_count": 4, "coordination_failure_count": 1}
            ],
            "organizational_risk_report": [
                {"governance_risk": ["Review delay"], "dependency_risk": ["Pending launch review"]}
            ],
            "organizational_opportunity_registry": [
                {"opportunities": [{"title": "Reduce governance friction", "opportunity_type": "governance"}]}
            ],
        }
    },
    "operating_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_service.collect_enterprise_operating_review_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_evidence.collect_enterprise_operating_review_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_operating_review_records_for_tests()
    yield
    clear_operating_review_records_for_tests()


def test_operating_review_domains_and_authority_flags():
    result = build_enterprise_operating_review_intelligence(session_id="eori-329")
    board = result.enterprise_operating_review_intelligence
    assert board["operating_review_authority"] is False
    assert board["automatic_strategy_execution_enabled"] is False
    assert board["automatic_program_execution_enabled"] is False
    assert board["automatic_organizational_changes_enabled"] is False
    assert board["automatic_decision_execution_enabled"] is False
    for key in ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_operating_snapshot_regression():
    snapshot = build_executive_operating_snapshot(evidence=_MOCK_EVIDENCE)
    assert snapshot["sources"] == ["FIX 324", "FIX 325", "FIX 326", "FIX 327", "FIX 328"]
    assert snapshot["current_state"]
    assert snapshot["major_risks"]
    assert snapshot["major_opportunities"]
    assert snapshot["major_decisions"]
    assert snapshot["validated"] is True


def test_strategic_review_regression():
    review = build_strategic_health_review(evidence=_MOCK_EVIDENCE)
    assert review["sources"] == ["FIX 324", "FIX 326"]
    assert set(review["dimensions"]) == {"strategy_health", "planning_health", "alignment_health"}
    assert review["overall_score"] > 0


def test_program_review_regression():
    review = build_program_health_review(evidence=_MOCK_EVIDENCE)
    assert review["sources"] == ["FIX 327"]
    assert review["healthy_count"] == 1
    assert review["blocked_count"] == 1
    assert review["validated"] is True


def test_organizational_review_regression():
    review = build_organizational_health_review(evidence=_MOCK_EVIDENCE)
    assert review["sources"] == ["FIX 328"]
    assert set(review["dimensions"]) == {"governance", "coordination", "capacity", "decision_velocity"}
    assert review["overall_level"] == "STABLE"


def test_risk_review_regression():
    review = build_enterprise_risk_review(evidence=_MOCK_EVIDENCE)
    assert set(review["risk_categories"]) == set(ENTERPRISE_RISK_CATEGORIES)
    assert review["strategic_risks"]
    assert review["program_risks"]
    assert review["organizational_risks"]
    assert review["operational_risks"]


def test_opportunity_review_regression():
    review = build_enterprise_opportunity_review(evidence=_MOCK_EVIDENCE)
    assert review["opportunities"]
    assert review["count"] >= 4
    assert review["validated"] is True


def test_scorecard_regression():
    snapshot = build_executive_operating_snapshot(evidence=_MOCK_EVIDENCE)
    strategic = build_strategic_health_review(evidence=_MOCK_EVIDENCE)
    program = build_program_health_review(evidence=_MOCK_EVIDENCE)
    organization = build_organizational_health_review(evidence=_MOCK_EVIDENCE)
    risk = build_enterprise_risk_review(evidence=_MOCK_EVIDENCE)
    scorecard = build_executive_operating_scorecard(
        strategic_review=strategic,
        program_review=program,
        organization_review=organization,
        risk_review=risk,
        snapshot=snapshot,
    )
    assert set(scorecard["dimensions"]) == set(EXECUTIVE_OPERATING_SCORECARD_DIMENSIONS)
    assert scorecard["overall_level"] in EXECUTIVE_OPERATING_LEVELS
    assert scorecard["automatic_decision_execution_forbidden"] is True


def test_dashboard_regression():
    routed = route_enterprise_operating_review_intelligence(
        "show enterprise operating review dashboard",
        session_id="eori-329",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_enterprise_operating_review_intelligence"
    assert meta["route_id"] == ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert OPERATING_REVIEW_AUTHORITY_FIX_329 is False


def test_success_question_routing_regression():
    assert parse_enterprise_operating_review_intelligence_intent("What is the current state of the organization?") == {
        "action": "view",
        "focus": "executive_operating_snapshot",
    }
    routed = route_enterprise_operating_review_intelligence(
        "What requires executive attention?",
        session_id="eori-329-q",
    )
    assert routed is not None
    assert "action" in routed[0].lower() or "Executive action" in routed[0]


def test_executive_action_registry_regression():
    snapshot = build_executive_operating_snapshot(evidence=_MOCK_EVIDENCE)
    strategic = build_strategic_health_review(evidence=_MOCK_EVIDENCE)
    program = build_program_health_review(evidence=_MOCK_EVIDENCE)
    organization = build_organizational_health_review(evidence=_MOCK_EVIDENCE)
    risk = build_enterprise_risk_review(evidence=_MOCK_EVIDENCE)
    opportunity = build_enterprise_opportunity_review(evidence=_MOCK_EVIDENCE)
    registry = build_executive_action_registry(
        snapshot=snapshot,
        risk_review=risk,
        opportunity_review=opportunity,
        program_review=program,
        organization_review=organization,
    )
    assert registry["actions"]
    assert set(registry["action_types"]) == set(EXECUTIVE_ACTION_TYPES)
    assert all(a["advisory_only"] for a in registry["actions"])


def test_operating_review_registry_record_only():
    append_operating_review_record(
        kind="operating_review_note",
        content="Review unified operating snapshot before board meeting",
        session_id="eori-329",
    )
    routed = route_enterprise_operating_review_intelligence(
        "operating review note: monitor major risks weekly",
        session_id="eori-329",
    )
    assert routed is not None
    assert "humans make decisions" in routed[0].lower()
    assert len(list_operating_review_records()) == 2

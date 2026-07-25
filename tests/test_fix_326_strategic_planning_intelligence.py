# SPDX-License-Identifier: Apache-2.0
"""FIX 326 — strategic planning intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_326,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_326,
    AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_326,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326,
    COMPARISON_MATRIX_DIMENSIONS,
    RESOURCE_PLANNING_DIMENSIONS,
    SCENARIO_IMPACT_DIMENSIONS,
    STRATEGIC_PLANNING_AUTHORITY_FIX_326,
    STRATEGIC_PLANNING_INTELLIGENCE_DOMAINS,
    STRATEGIC_PLANNING_INTELLIGENCE_ROUTE_ID,
    STRATEGIC_PLAN_STATUSES,
    STRATEGIC_RISK_FORECAST_CATEGORIES,
    STRATEGIC_SCENARIO_TYPES,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_evaluator import (
    build_resource_planning_report,
    build_scenario_impact_report,
    build_strategic_comparison_matrix,
    build_strategic_opportunity_forecast,
    build_strategic_plan_registry,
    build_strategic_planning_registry,
    build_strategic_risk_forecast,
    build_strategic_scenario_report,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_intent import (
    parse_strategic_planning_intelligence_intent,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_router import (
    route_strategic_planning_intelligence,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_service import (
    build_strategic_planning_intelligence,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_store import (
    append_planning_review_record,
    clear_planning_review_records_for_tests,
    list_planning_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "spi-326",
    "sources_ok": {f"fix_{n}": True for n in (309, 313, 324, 325)},
    "fix_309": {
        "sections": {
            "launch_risk_registry": [{"risks": ["Incomplete security checklist"]}],
        }
    },
    "fix_313": {
        "sections": {
            "launch_blocker_registry": [{"blockers": ["Pending launch review"]}],
        }
    },
    "fix_324": {
        "sections": {
            "strategic_value_report": [
                {"business_value_score": 0.75, "strategic_value_score": 0.78, "customer_value_score": 0.72}
            ],
            "investment_opportunity_report": [
                {
                    "high_value_opportunities": [{"title": "Accelerate Mission Control workflows"}],
                    "underinvested_areas": [{"title": "Education for underused capabilities"}],
                }
            ],
            "portfolio_risk_report": [
                {
                    "operational_risk": ["Pending launch review"],
                    "product_risk": ["Incomplete security checklist"],
                    "customer_risk": ["customer_health:STABLE"],
                    "commercial_risk": ["commercial_status:ON_TRACK"],
                }
            ],
            "resource_allocation_report": [
                {"engineering_effort_units": 6, "operational_effort_units": 3, "support_effort_units": 2}
            ],
            "portfolio_opportunity_registry": [
                {
                    "opportunities": [
                        {"title": "Efficiency through automation", "opportunity_type": "efficiency", "value": 0.7}
                    ]
                }
            ],
        }
    },
    "fix_325": {
        "sections": {
            "executive_decision_dashboard": [{"recommendation_count": 4}],
            "decision_risk_report": [
                {
                    "operational_risk_signals": ["Pending launch review"],
                    "commercial_risk_signals": ["commercial_status:ON_TRACK"],
                    "highest_risk_decisions": [{"title": "Address portfolio risk before acceleration"}],
                }
            ],
            "executive_recommendation_report": [
                {
                    "recommendations": [
                        {"title": "Prioritize Mission Control adoption", "recommendation_level": "PRIORITIZE"},
                        {"title": "Review launch blockers", "recommendation_level": "REVIEW"},
                    ]
                }
            ],
            "tradeoff_analysis_report": [
                {
                    "tradeoffs": [
                        {"title": "Prioritize Mission Control adoption", "value": 0.85, "effort": "medium", "risk": 0.3}
                    ]
                }
            ],
            "executive_opportunity_registry": [
                {
                    "opportunities": [
                        {"title": "Expand enterprise workflows", "source_type": "growth"},
                        {"title": "Strengthen PMF signals", "source_type": "pmf"},
                    ]
                }
            ],
        }
    },
    "planning_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_service.collect_strategic_planning_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_evidence.collect_strategic_planning_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_planning_review_records_for_tests()
    yield
    clear_planning_review_records_for_tests()


def test_strategic_planning_domains_and_authority_flags():
    result = build_strategic_planning_intelligence(session_id="spi-326")
    board = result.strategic_planning_intelligence
    assert board["strategic_planning_authority"] is False
    assert board["automatic_strategy_execution_enabled"] is False
    assert board["automatic_project_creation_enabled"] is False
    assert board["automatic_budget_allocation_enabled"] is False
    assert board["automatic_resource_assignment_enabled"] is False
    for key in STRATEGIC_PLANNING_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_planning_registry_regression():
    registry = build_strategic_planning_registry(evidence=_MOCK_EVIDENCE)
    assert registry["proposed_plans"]
    assert registry["cross_tenant_planning_visibility_forbidden"] is True
    assert set(registry["plan_statuses"]) == set(STRATEGIC_PLAN_STATUSES)


def test_scenario_generation_regression():
    report = build_strategic_scenario_report(evidence=_MOCK_EVIDENCE)
    assert report["count"] == 5
    assert set(report["scenario_types"]) == set(STRATEGIC_SCENARIO_TYPES)
    assert all(s["automatic_strategy_execution_forbidden"] for s in report["scenarios"])
    assert report["validated"] is True


def test_impact_analysis_regression():
    scenarios = build_strategic_scenario_report(evidence=_MOCK_EVIDENCE)
    report = build_scenario_impact_report(scenario_report=scenarios, evidence=_MOCK_EVIDENCE)
    assert report["count"] == 5
    assert set(report["impact_dimensions"]) == set(SCENARIO_IMPACT_DIMENSIONS)
    assert report["impacts"][0]["customer_impact"] > 0
    assert report["validated"] is True


def test_risk_forecasting_regression():
    report = build_strategic_risk_forecast(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 309", "FIX 313", "FIX 324", "FIX 325"]
    assert set(report["risk_categories"]) == set(STRATEGIC_RISK_FORECAST_CATEGORIES)
    assert report["operational_risks"]
    assert report["execution_risks"]
    assert report["validated"] is True


def test_opportunity_forecasting_regression():
    report = build_strategic_opportunity_forecast(evidence=_MOCK_EVIDENCE)
    assert report["growth_opportunities"]
    assert report["expansion_opportunities"]
    assert report["efficiency_opportunities"]
    assert report["validated"] is True


def test_resource_planning_regression():
    report = build_resource_planning_report(evidence=_MOCK_EVIDENCE)
    assert report["engineering_allocation"] == 6
    assert report["operational_allocation"] == 3
    assert report["support_allocation"] == 2
    assert report["investment_allocation"] >= 2
    assert set(report["planning_dimensions"]) == set(RESOURCE_PLANNING_DIMENSIONS)
    assert report["validated"] is True


def test_comparison_matrix_regression():
    scenarios = build_strategic_scenario_report(evidence=_MOCK_EVIDENCE)
    impacts = build_scenario_impact_report(scenario_report=scenarios, evidence=_MOCK_EVIDENCE)
    risks = build_strategic_risk_forecast(evidence=_MOCK_EVIDENCE)
    opportunities = build_strategic_opportunity_forecast(evidence=_MOCK_EVIDENCE)
    plans = build_strategic_plan_registry(
        scenario_report=scenarios,
        impact_report=impacts,
        risk_forecast=risks,
        opportunity_forecast=opportunities,
    )
    matrix = build_strategic_comparison_matrix(
        plan_registry=plans,
        scenario_report=scenarios,
        risk_forecast=risks,
    )
    assert matrix["comparisons"]
    assert matrix["strongest_plan"]
    assert set(matrix["comparison_dimensions"]) == set(COMPARISON_MATRIX_DIMENSIONS)
    assert matrix["automatic_strategy_execution_forbidden"] is True


def test_dashboard_regression():
    routed = route_strategic_planning_intelligence("show strategic planning dashboard", session_id="spi-326")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_strategic_planning_intelligence"
    assert meta["route_id"] == STRATEGIC_PLANNING_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert STRATEGIC_PLANNING_AUTHORITY_FIX_326 is False
    assert AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326 is False


def test_success_question_routing_regression():
    assert parse_strategic_planning_intelligence_intent("What strategic paths exist?") == {
        "action": "view",
        "focus": "strategic_scenario_report",
    }
    routed = route_strategic_planning_intelligence(
        "Which plans appear strongest?",
        session_id="spi-326-q",
    )
    assert routed is not None
    assert "Strongest plan" in routed[0] or "comparison" in routed[0].lower()


def test_planning_review_registry_record_only():
    append_planning_review_record(kind="planning_note", content="Compare balanced vs aggressive growth", session_id="spi-326")
    routed = route_strategic_planning_intelligence(
        "planning note: review scenario impacts before approval",
        session_id="spi-326",
    )
    assert routed is not None
    assert "humans choose plans" in routed[0].lower()
    assert len(list_planning_review_records()) == 2

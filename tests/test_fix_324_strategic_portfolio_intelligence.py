# SPDX-License-Identifier: Apache-2.0
"""FIX 324 — strategic portfolio intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324,
    PORTFOLIO_ASSET_TYPES,
    PORTFOLIO_OPPORTUNITY_TYPES,
    PORTFOLIO_RISK_CATEGORIES,
    STRATEGIC_AUTHORITY_FIX_324,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_DOMAINS,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_ROUTE_ID,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_evaluator import (
    build_investment_opportunity_report,
    build_portfolio_asset_registry,
    build_portfolio_opportunity_registry,
    build_portfolio_risk_report,
    build_resource_allocation_report,
    build_strategic_alignment_report,
    build_strategic_priority_matrix,
    build_strategic_value_report,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_intent import (
    parse_strategic_portfolio_intelligence_intent,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_router import (
    route_strategic_portfolio_intelligence,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_service import (
    build_strategic_portfolio_intelligence,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_store import (
    append_strategic_review_record,
    clear_strategic_review_records_for_tests,
    list_strategic_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "spi-324",
    "sources_ok": {f"fix_{n}": True for n in (290, 300, 309, 313, 316, 322, 323)},
    "fix_290": {
        "sections": {
            "strategic_alignment_graph": [{"node_count": 5}],
            "business_goal_registry": [{"objectives": ["Accelerate Mission Control adoption", "Reduce ops friction"]}],
            "project_portfolio_registry": [{"projects": ["Onboarding automation", "Portfolio intelligence"]}],
            "product_portfolio_registry": [{"products": ["Mission Control", "Atlas Trader"]}],
            "business_opportunity_portfolio": [{"opportunities": [{"title": "Enterprise portfolio analytics"}]}],
            "team_operating_registry": [{"engineering_capacity": 6}],
            "business_operations_registry": [{"operational_load": 3}],
        }
    },
    "fix_300": {
        "sections": {
            "tenant_dashboard": [{"project_count": 2}],
        }
    },
    "fix_309": {
        "sections": {
            "launch_risk_registry": [{"risks": ["Incomplete launch checklist"]}],
        }
    },
    "fix_313": {
        "sections": {
            "launch_blocker_registry": [{"blockers": ["Pending security review"]}],
        }
    },
    "fix_316": {
        "sections": {
            "platform_health_baseline": [{"status": "HEALTHY"}],
            "customer_health_baseline": [{"status": "STABLE"}],
            "commercial_baseline": [{"status": "ON_TRACK"}],
            "incident_baseline": [{"active_incidents": ["Minor API latency spike"]}],
            "portfolio_baseline": [{"repositories": ["aethos-core", "mission-control-ui"]}],
            "operations_baseline_registry": [{"support_load": 2}],
        }
    },
    "fix_322": {
        "sections": {
            "pmf_scorecard": [{"overall_score": 0.78, "overall_level": "STRONG"}],
            "pmf_opportunity_registry": [
                {
                    "opportunities": [
                        {"title": "Expand Mission Control workflows", "impact": "high", "category": "adoption"},
                        {"title": "Improve onboarding completion", "impact": "medium", "category": "onboarding"},
                    ]
                }
            ],
            "product_market_fit_dashboard": [{"pmf_opportunity_count": 2}],
        }
    },
    "fix_323": {
        "sections": {
            "value_realization_scorecard": [{"overall_score": 0.72, "overall_level": "HIGH"}],
            "value_opportunity_registry": [
                {
                    "opportunities": [
                        {"title": "Close value gap on autonomous deploy", "impact": "high", "opportunity_type": "adoption"},
                        {"title": "Education for underused capabilities", "impact": "medium", "opportunity_type": "education"},
                    ]
                }
            ],
            "customer_value_dashboard": [{"value_opportunity_count": 2}],
            "value_gap_report": [{"gaps": ["Autonomous deploy not adopted", "Manual ops still high"]}],
        }
    },
    "strategic_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_service.collect_strategic_portfolio_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_evidence.collect_strategic_portfolio_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_strategic_review_records_for_tests()
    yield
    clear_strategic_review_records_for_tests()


def test_strategic_portfolio_domains_and_authority_flags():
    result = build_strategic_portfolio_intelligence(session_id="spi-324")
    board = result.strategic_portfolio_intelligence
    assert board["strategic_authority"] is False
    assert board["automatic_budget_allocation_enabled"] is False
    assert board["automatic_project_creation_enabled"] is False
    assert board["automatic_resource_reallocation_enabled"] is False
    assert board["automatic_strategy_execution_enabled"] is False
    for key in STRATEGIC_PORTFOLIO_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_portfolio_asset_regression():
    registry = build_portfolio_asset_registry(evidence=_MOCK_EVIDENCE)
    assert registry["count"] >= 5
    assert registry["cross_tenant_portfolio_visibility_forbidden"] is True
    assert set(registry["asset_types"]) == set(PORTFOLIO_ASSET_TYPES)


def test_strategic_value_regression():
    report = build_strategic_value_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 322", "FIX 323"]
    assert report["strategic_value_score"] == 0.78
    assert report["customer_value_score"] == 0.72
    assert report["business_value_score"] == 0.75
    assert report["validated"] is True


def test_investment_opportunity_regression():
    report = build_investment_opportunity_report(evidence=_MOCK_EVIDENCE)
    assert report["high_value_opportunities"]
    assert report["underinvested_areas"]
    assert report["emerging_opportunities"]
    assert report["validated"] is True


def test_portfolio_risk_regression():
    report = build_portfolio_risk_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 309", "FIX 313", "FIX 316"]
    assert set(report["risk_categories"]) == set(PORTFOLIO_RISK_CATEGORIES)
    assert report["operational_risk"]
    assert report["product_risk"]
    assert report["customer_risk"]
    assert report["commercial_risk"]


def test_resource_allocation_regression():
    report = build_resource_allocation_report(evidence=_MOCK_EVIDENCE)
    assert report["engineering_effort_units"] == 6
    assert report["operational_effort_units"] == 3
    assert report["support_effort_units"] == 2
    assert report["value_gap_pressure"] == 2
    assert report["validated"] is True


def test_strategic_alignment_regression():
    report = build_strategic_alignment_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 290"]
    assert report["goals"]
    assert report["initiatives"]
    assert report["products"]
    assert report["aligned_pairs"]
    assert report["validated"] is True


def test_priority_matrix_regression():
    strategic_value = build_strategic_value_report(evidence=_MOCK_EVIDENCE)
    investment = build_investment_opportunity_report(evidence=_MOCK_EVIDENCE)
    alignment = build_strategic_alignment_report(evidence=_MOCK_EVIDENCE)
    risk = build_portfolio_risk_report(evidence=_MOCK_EVIDENCE)
    registry = build_portfolio_opportunity_registry(
        investment_report=investment,
        strategic_value=strategic_value,
        alignment_report=alignment,
        risk_report=risk,
    )
    matrix = build_strategic_priority_matrix(
        registry=registry,
        investment_report=investment,
        risk_report=risk,
    )
    assert matrix["ranked_opportunities"]
    assert matrix["highest_value_opportunities"]
    assert matrix["highest_risk_opportunities"]
    assert matrix["highest_roi_opportunities"]
    assert matrix["automatic_strategy_execution_forbidden"] is True
    assert set(registry["opportunity_types"]) == set(PORTFOLIO_OPPORTUNITY_TYPES)


def test_dashboard_regression():
    routed = route_strategic_portfolio_intelligence("show strategic portfolio dashboard", session_id="spi-324")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_strategic_portfolio_intelligence"
    assert meta["route_id"] == STRATEGIC_PORTFOLIO_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert STRATEGIC_AUTHORITY_FIX_324 is False
    assert AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324 is False
    assert AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324 is False
    assert AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324 is False
    assert AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324 is False


def test_success_question_routing_regression():
    assert parse_strategic_portfolio_intelligence_intent("Which products create the most value?") == {
        "action": "view",
        "focus": "strategic_value_report",
    }
    routed = route_strategic_portfolio_intelligence(
        "Which initiatives deserve investment?",
        session_id="spi-324-q",
    )
    assert routed is not None
    assert "Investment opportunity" in routed[0] or "investment" in routed[0].lower()


def test_strategic_review_registry_record_only():
    append_strategic_review_record(kind="strategic_note", content="Track portfolio ROI before acceleration", session_id="spi-324")
    routed = route_strategic_portfolio_intelligence(
        "strategic note: monitor underinvested value gaps",
        session_id="spi-324",
    )
    assert routed is not None
    assert "humans make investment decisions" in routed[0].lower()
    assert len(list_strategic_review_records()) == 2

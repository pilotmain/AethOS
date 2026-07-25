# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_325,
    AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_325,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_325,
    EXECUTIVE_AUTHORITY_FIX_325,
    EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS,
    EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID,
    EXECUTIVE_RECOMMENDATION_LEVELS,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_evaluator import (
    build_decision_opportunity_report,
    build_decision_risk_report,
    build_executive_alignment_report,
    build_executive_decision_registry,
    build_executive_opportunity_registry,
    build_executive_priority_matrix,
    build_executive_recommendation_report,
    build_tradeoff_analysis_report,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_intent import (
    parse_executive_decision_intelligence_intent,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_router import (
    route_executive_decision_intelligence,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_service import (
    build_executive_decision_intelligence,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_store import (
    append_executive_review_record,
    clear_executive_review_records_for_tests,
    list_executive_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "edi-325",
    "sources_ok": {f"fix_{n}": True for n in (290, 309, 313, 316, 317, 320, 322, 323, 324)},
    "fix_290": {
        "sections": {
            "business_goal_registry": [{"objectives": ["Accelerate platform adoption", "Reduce operational friction"]}],
            "strategic_alignment_graph": [{"node_count": 6}],
        }
    },
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
    "fix_316": {
        "sections": {
            "incident_baseline": [{"active_incidents": ["API latency spike"]}],
        }
    },
    "fix_317": {
        "sections": {
            "improvement_opportunity_registry": [
                {"opportunities": [{"title": "Reduce onboarding friction", "priority_score": 0.7}]}
            ],
        }
    },
    "fix_320": {
        "sections": {
            "growth_opportunity_registry": [
                {"opportunities": [{"title": "Expand Mission Control adoption", "value": 0.65}]}
            ],
        }
    },
    "fix_322": {
        "sections": {
            "pmf_opportunity_registry": [
                {
                    "opportunities": [
                        {"title": "Strengthen workflow PMF", "impact": "high"},
                        {"title": "Improve onboarding PMF", "impact": "medium"},
                    ]
                }
            ],
        }
    },
    "fix_323": {
        "sections": {
            "value_opportunity_registry": [
                {
                    "opportunities": [
                        {"title": "Close autonomous deploy value gap", "impact": "high", "value": 0.8},
                    ]
                }
            ],
        }
    },
    "fix_324": {
        "sections": {
            "investment_opportunity_report": [
                {
                    "high_value_opportunities": [{"title": "Accelerate Mission Control workflows", "source": "FIX 322"}],
                    "underinvested_areas": [{"title": "Education for underused capabilities", "source": "FIX 323"}],
                    "emerging_opportunities": [{"title": "Enterprise portfolio analytics", "source": "FIX 290"}],
                }
            ],
            "portfolio_risk_report": [
                {
                    "operational_risk": ["Pending launch review", "API latency spike"],
                    "product_risk": ["Incomplete security checklist"],
                    "customer_risk": ["customer_health:STABLE"],
                    "commercial_risk": ["commercial_status:ON_TRACK"],
                }
            ],
            "strategic_alignment_report": [
                {
                    "goals": ["Accelerate platform adoption"],
                    "initiatives": ["Onboarding automation", "Portfolio intelligence"],
                    "alignment_nodes": 6,
                }
            ],
            "strategic_value_report": [{"business_value_score": 0.75, "strategic_value_score": 0.78, "customer_value_score": 0.72}],
            "portfolio_opportunity_registry": [
                {
                    "opportunities": [
                        {
                            "opportunity_id": "growth-accelerate-mc",
                            "title": "Accelerate Mission Control workflows",
                            "opportunity_type": "growth",
                            "value": 0.85,
                            "strategic_alignment": "high",
                        }
                    ]
                }
            ],
            "strategic_priority_matrix": [
                {
                    "highest_risk_opportunities": [
                        {
                            "opportunity_id": "portfolio-risk-attention",
                            "title": "Address portfolio risk before acceleration",
                            "risk_signal": "portfolio_risk",
                        }
                    ],
                    "ranked_opportunities": [{"title": "Accelerate Mission Control workflows", "priority_score": 8.2}],
                }
            ],
        }
    },
    "executive_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_service.collect_executive_decision_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_evidence.collect_executive_decision_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_executive_review_records_for_tests()
    yield
    clear_executive_review_records_for_tests()


def test_executive_decision_domains_and_authority_flags():
    result = build_executive_decision_intelligence(session_id="edi-325")
    board = result.executive_decision_intelligence
    assert board["executive_authority"] is False
    assert board["automatic_strategy_execution_enabled"] is False
    assert board["automatic_resource_reallocation_enabled"] is False
    assert board["automatic_budget_allocation_enabled"] is False
    assert board["automatic_decision_execution_enabled"] is False
    for key in EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_decision_registry_regression():
    registry = build_executive_decision_registry(evidence=_MOCK_EVIDENCE)
    assert registry["pending_decisions"]
    assert registry["cross_tenant_decision_visibility_forbidden"] is True
    assert set(registry["decision_statuses"]) == {"pending", "reviewed", "deferred"}


def test_opportunity_analysis_regression():
    report = build_decision_opportunity_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 324"]
    assert report["high_value_opportunities"]
    assert report["high_urgency_opportunities"]
    assert report["validated"] is True


def test_risk_analysis_regression():
    report = build_decision_risk_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 309", "FIX 313", "FIX 316", "FIX 324"]
    assert report["operational_risk_signals"]
    assert report["highest_risk_decisions"]
    assert report["validated"] is True


def test_recommendation_regression():
    report = build_executive_recommendation_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 317", "FIX 320", "FIX 322", "FIX 323", "FIX 324"]
    assert report["recommendations"]
    assert set(report["recommendation_levels"]) == set(EXECUTIVE_RECOMMENDATION_LEVELS)
    assert all(rec["automatic_decision_execution_forbidden"] for rec in report["recommendations"])


def test_tradeoff_regression():
    opportunity = build_decision_opportunity_report(evidence=_MOCK_EVIDENCE)
    risk = build_decision_risk_report(evidence=_MOCK_EVIDENCE)
    recommendations = build_executive_recommendation_report(evidence=_MOCK_EVIDENCE)
    report = build_tradeoff_analysis_report(
        opportunity_report=opportunity,
        risk_report=risk,
        recommendation_report=recommendations,
    )
    assert report["tradeoffs"]
    assert report["dimensions"] == ("value", "effort", "risk", "confidence")
    assert report["validated"] is True


def test_alignment_regression():
    report = build_executive_alignment_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 290", "FIX 324"]
    assert report["goal_alignment_score"] > 0
    assert report["portfolio_alignment_score"] > 0
    assert report["investment_alignment_score"] > 0
    assert report["validated"] is True


def test_priority_matrix_regression():
    opportunity = build_decision_opportunity_report(evidence=_MOCK_EVIDENCE)
    risk = build_decision_risk_report(evidence=_MOCK_EVIDENCE)
    recommendations = build_executive_recommendation_report(evidence=_MOCK_EVIDENCE)
    tradeoffs = build_tradeoff_analysis_report(
        opportunity_report=opportunity,
        risk_report=risk,
        recommendation_report=recommendations,
    )
    registry = build_executive_opportunity_registry(
        opportunity_report=opportunity,
        recommendation_report=recommendations,
        evidence=_MOCK_EVIDENCE,
    )
    matrix = build_executive_priority_matrix(
        registry=registry,
        recommendation_report=recommendations,
        risk_report=risk,
        tradeoff_report=tradeoffs,
    )
    assert matrix["ranked_decisions"]
    assert matrix["highest_value_decisions"]
    assert matrix["highest_risk_decisions"]
    assert matrix["highest_leverage_decisions"]
    assert matrix["automatic_decision_execution_forbidden"] is True


def test_dashboard_regression():
    routed = route_executive_decision_intelligence("show executive decision dashboard", session_id="edi-325")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_executive_decision_intelligence"
    assert meta["route_id"] == EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert EXECUTIVE_AUTHORITY_FIX_325 is False
    assert AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325 is False


def test_success_question_routing_regression():
    assert parse_executive_decision_intelligence_intent("What should leadership focus on next?") == {
        "action": "view",
        "focus": "executive_recommendation_report",
    }
    routed = route_executive_decision_intelligence(
        "What decisions are most urgent?",
        session_id="edi-325-q",
    )
    assert routed is not None
    assert "urgency" in routed[0].lower() or "Decision opportunit" in routed[0]


def test_executive_review_registry_record_only():
    append_executive_review_record(kind="executive_note", content="Review portfolio acceleration options", session_id="edi-325")
    routed = route_executive_decision_intelligence(
        "executive note: monitor highest-risk decisions",
        session_id="edi-325",
    )
    assert routed is not None
    assert "humans decide" in routed[0].lower()
    assert len(list_executive_review_records()) == 2

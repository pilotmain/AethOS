# SPDX-License-Identifier: Apache-2.0
"""FIX 322 — product-market fit intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_contract import (
    AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322,
    PMF_AUTHORITY_FIX_322,
    PMF_FIT_LEVELS,
    PMF_SCORECARD_DIMENSIONS,
    PRODUCT_MARKET_FIT_INTELLIGENCE_DOMAINS,
    PRODUCT_MARKET_FIT_INTELLIGENCE_ROUTE_ID,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_evaluator import (
    build_capability_demand_report,
    build_customer_value_realization_report,
    build_expansion_value_report,
    build_pmf_opportunity_registry,
    build_pmf_scorecard,
    build_problem_solution_fit_report,
    build_retention_value_report,
    build_value_signal_registry,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_intent import (
    parse_product_market_fit_intelligence_intent,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_router import (
    route_product_market_fit_intelligence,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_service import (
    build_product_market_fit_intelligence,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_store import (
    append_pmf_review_record,
    clear_pmf_review_records_for_tests,
    list_pmf_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "pmf-322",
    "sources_ok": {f"fix_{n}": True for n in (295, 296, 318, 319, 320, 321)},
    "fix_295": {
        "sections": {
            "capability_registry": [{"capabilities": [{"name": "Mission Control"}], "capability_count": 1}],
        }
    },
    "fix_296": {
        "sections": {
            "proven_capabilities": [{"items": ["Mission Control (PROVEN)"]}],
            "operational_capabilities": [{"items": ["Provider inspection (OPERATIONAL)"]}],
            "planned_blocked_capabilities": [{"items": ["Autonomous deploy (PLANNED)"]}],
        }
    },
    "fix_318": {
        "sections": {
            "analytics_dashboard": [
                {"onboarding_completion_rate_percent": 65, "capabilities_used_count": 2, "healthy_customers": 4}
            ],
            "capability_usage_report": [
                {
                    "capabilities_used": ["Mission Control (PROVEN)"],
                    "capabilities_ignored": ["Autonomous deploy (PLANNED)"],
                    "capabilities_confusing": ["Beta workflow (EXPERIMENTAL)"],
                }
            ],
            "commercial_analytics_report": [{"active_subscription_count": 3}],
            "behavioral_opportunity_registry": [{"opportunities": [{"detail": "Improve onboarding completion"}]}],
            "user_journey_report": [{"success_predictors": ["onboarding_completed", "provider_connected"]}],
        }
    },
    "fix_319": {
        "sections": {
            "customer_feedback_dashboard": [
                {"feedback_item_count": 5, "positive_sentiment_count": 3, "negative_sentiment_count": 1}
            ],
            "customer_feedback_registry": [
                {"items": [{"text": "Need clearer provider onboarding", "source": "support_notes"}]}
            ],
            "feedback_classification_report": [
                {
                    "items": [
                        {"text": "Need clearer provider onboarding", "classification": "onboarding_issue"},
                        {"text": "Love Mission Control dashboard", "classification": "positive_feedback"},
                    ],
                    "counts_by_classification": {
                        "onboarding_issue": 1,
                        "positive_feedback": 1,
                        "feature_request": 1,
                    },
                }
            ],
            "feedback_sentiment_report": [{"counts_by_sentiment": {"positive": 3, "neutral": 1, "negative": 1}}],
            "capability_gap_report": [
                {
                    "gaps": [{"requested_capability": "Autonomous deploy workflow", "existing_match": False}],
                    "requested_capabilities": ["Autonomous deploy workflow"],
                }
            ],
            "customer_friction_report": [{"onboarding_friction": ["Connect provider"]}],
        }
    },
    "fix_320": {
        "sections": {
            "growth_adoption_dashboard": [
                {"activated_customers": 4, "retained_customers": 3, "disengaged_customers": 1, "adoption_rate_percent": 65}
            ],
            "adoption_registry": [{"activated_customers": 4}],
            "adoption_analytics_report": [{"adoption_rate_percent": 65.0}],
            "retention_intelligence_report": [
                {"retained_customers": 3, "disengaged_customers": 1, "retention_trend": "rising"}
            ],
            "expansion_intelligence_report": [
                {"plan_expansion": ["Starter to Pro"], "upgrade_candidates": ["Starter to Pro"]}
            ],
            "success_pattern_report": [
                {
                    "behaviors_linked_to_success": ["onboarding_completed"],
                    "onboarding_paths_linked_to_retention": ["completed_onboarding"],
                }
            ],
        }
    },
    "fix_321": {
        "sections": {
            "customer_journey_dashboard": [{"current_stage": "retention", "successful_path_count": 2}],
            "journey_success_report": [
                {
                    "successful_paths": ["onboarding_completed"],
                    "high_retention_paths": ["completed_onboarding"],
                    "expansion_paths": ["Starter to Pro"],
                }
            ],
        }
    },
    "pmf_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_service.collect_pmf_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_evidence.collect_pmf_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_pmf_review_records_for_tests()
    yield
    clear_pmf_review_records_for_tests()


def test_pmf_domains_and_authority_flags():
    result = build_product_market_fit_intelligence(session_id="pmf-322")
    board = result.product_market_fit_intelligence
    assert board["pmf_authority"] is False
    assert board["automatic_product_strategy_enabled"] is False
    assert board["automatic_feature_creation_enabled"] is False
    assert board["automatic_pricing_changes_enabled"] is False
    for key in PRODUCT_MARKET_FIT_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_value_signal_regression():
    registry = build_value_signal_registry(evidence=_MOCK_EVIDENCE)
    assert registry["count"] >= 4
    assert registry["cross_tenant_exposure_forbidden"] is True
    assert registry["sources"] == ["FIX 318", "FIX 319", "FIX 320", "FIX 321"]


def test_problem_solution_fit_regression():
    report = build_problem_solution_fit_report(evidence=_MOCK_EVIDENCE)
    assert report["customer_problems"]
    assert report["product_capabilities"]
    assert report["validated"] is True


def test_value_realization_regression():
    report = build_customer_value_realization_report(evidence=_MOCK_EVIDENCE)
    assert report["realized_value"]
    assert report["unrealized_value"]
    assert report["perceived_value"]


def test_capability_demand_regression():
    report = build_capability_demand_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 295", "FIX 319"]
    assert "Mission Control (PROVEN)" in report["adopted_capabilities"]
    assert report["ignored_capabilities"]
    assert report["requested_capabilities"]


def test_retention_value_regression():
    report = build_retention_value_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 320"]
    assert report["capabilities_driving_retention"]
    assert report["journeys_driving_retention"]
    assert report["retained_customers"] == 3


def test_expansion_value_regression():
    report = build_expansion_value_report(evidence=_MOCK_EVIDENCE)
    assert report["capabilities_driving_expansion"]
    assert report["plan_expansion_paths"]
    assert report["active_subscriptions"] == 3


def test_pmf_scorecard_regression():
    scorecard = build_pmf_scorecard(evidence=_MOCK_EVIDENCE)
    assert set(scorecard["dimensions"]) == set(PMF_SCORECARD_DIMENSIONS)
    assert scorecard["overall_level"] in PMF_FIT_LEVELS
    assert scorecard["validated"] is True


def test_dashboard_regression():
    routed = route_product_market_fit_intelligence("show pmf dashboard", session_id="pmf-322")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_product_market_fit_intelligence"
    assert meta["route_id"] == PRODUCT_MARKET_FIT_INTELLIGENCE_ROUTE_ID
    assert "strategy" in body.lower()
    assert PMF_AUTHORITY_FIX_322 is False
    assert AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322 is False


def test_success_question_routing_regression():
    assert parse_product_market_fit_intelligence_intent("Are customers finding value?") == {
        "action": "view",
        "focus": "customer_value_realization_report",
    }
    routed = route_product_market_fit_intelligence("How strong is product-market fit?", session_id="pmf-322-q")
    assert routed is not None
    assert "scorecard" in routed[0].lower()


def test_pmf_opportunity_regression():
    problem = build_problem_solution_fit_report(evidence=_MOCK_EVIDENCE)
    value = build_customer_value_realization_report(evidence=_MOCK_EVIDENCE)
    demand = build_capability_demand_report(evidence=_MOCK_EVIDENCE)
    retention = build_retention_value_report(evidence=_MOCK_EVIDENCE)
    expansion = build_expansion_value_report(evidence=_MOCK_EVIDENCE)
    registry = build_pmf_opportunity_registry(
        problem_solution_report=problem,
        value_report=value,
        capability_demand=demand,
        retention_value=retention,
        expansion_value=expansion,
    )
    assert registry["count"] >= 2
    assert all(opp["automatic_product_strategy_forbidden"] for opp in registry["opportunities"])


def test_pmf_review_registry_record_only():
    append_pmf_review_record(kind="pmf_note", content="Track capability demand gaps", session_id="pmf-322")
    routed = route_product_market_fit_intelligence("pmf note: monitor retention value drivers", session_id="pmf-322")
    assert routed is not None
    assert "humans decide strategy" in routed[0].lower()
    assert len(list_pmf_review_records()) == 2

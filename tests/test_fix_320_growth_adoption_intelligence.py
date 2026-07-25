# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — growth & adoption intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_contract import (
    AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320,
    GROWTH_ADOPTION_INTELLIGENCE_DOMAINS,
    GROWTH_ADOPTION_INTELLIGENCE_ROUTE_ID,
    GROWTH_AUTHORITY_FIX_320,
    GROWTH_OPPORTUNITY_TYPES,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_evaluator import (
    build_adoption_analytics_report,
    build_adoption_registry,
    build_churn_risk_report,
    build_expansion_intelligence_report,
    build_growth_opportunity_registry,
    build_growth_priority_matrix,
    build_retention_intelligence_report,
    build_success_pattern_report,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_intent import (
    parse_growth_adoption_intelligence_intent,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_router import (
    route_growth_adoption_intelligence,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_service import (
    build_growth_adoption_intelligence,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_store import (
    append_growth_review_record,
    clear_growth_review_records_for_tests,
    list_growth_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "gai-320",
    "sources_ok": {f"fix_{n}": True for n in (300, 301, 303, 304, 305, 308, 310, 312, 318, 319)},
    "fix_300": {
        "sections": {
            "tenant_dashboard": [
                {"organization_count": 4, "workspace_count": 6, "project_count": 9, "user_count": 12}
            ],
        }
    },
    "fix_301": {
        "sections": {
            "onboarding_progress_registry": [
                {
                    "completed_count": 3,
                    "started_count": 5,
                    "incomplete_steps": ["Connect provider"],
                }
            ],
        }
    },
    "fix_303": {
        "sections": {
            "provider_connection_dashboard": [{"connected_provider_count": 2}],
            "provider_connection_reports": [
                {"provider": "github", "connected_count": 2, "readiness": "ready"},
                {"provider": "railway", "connected_count": 0, "readiness": "not_configured"},
            ],
        }
    },
    "fix_304": {
        "sections": {
            "channel_integration_dashboard": [{"connected_channels": ["slack", "email"]}],
            "channel_registry": [{"channels": ["slack", "email"]}],
        }
    },
    "fix_305": {
        "sections": {
            "subscription_registry": [{"active_subscriptions": ["sub-1", "sub-2", "sub-3"]}],
            "usage_registry": [{"expansion_candidates": ["Starter to Pro"]}],
        }
    },
    "fix_308": {
        "sections": {
            "upgrade_path_registry": [{"paths": ["Starter to Pro", "Pro to Enterprise"]}],
        }
    },
    "fix_310": {
        "sections": {
            "customer_health_registry": [{"healthy_count": 3, "at_risk_count": 1}],
            "customer_risk_registry": [{"at_risk_count": 1}],
            "customer_adoption_report": [{"engagement_trend": "rising"}],
            "support_request_registry": [{"requests": [{"summary": "Escalated onboarding issue"}]}],
        }
    },
    "fix_312": {
        "sections": {
            "beta_cohort_registry": [{"participant_count": 2}],
            "beta_success_metrics": [{"activation_rate": 0.6}],
        }
    },
    "fix_318": {
        "sections": {
            "onboarding_analytics_report": [
                {
                    "users_started_onboarding": 5,
                    "users_completed_onboarding": 3,
                    "average_completion_rate_percent": 60.0,
                    "drop_off_points": ["Connect provider"],
                }
            ],
            "provider_analytics_report": [
                {
                    "most_connected_provider": "github",
                    "connected_provider_count": 2,
                    "readiness_failures": ["railway: not_configured"],
                }
            ],
            "capability_usage_report": [{"capabilities_used": ["Mission Control (PROVEN)"]}],
            "customer_success_analytics_report": [
                {"healthy_customers": 3, "at_risk_customers": 1, "engagement_trend": "rising"}
            ],
            "user_journey_report": [
                {
                    "success_predictors": ["onboarding_completed", "provider_connected"],
                    "stages": {
                        "activation": {"onboarding_completed": 3},
                        "retention": {"retained_subscriptions": 3, "at_risk_customers": 1},
                        "expansion": {"upgrade_candidates": 1, "beta_participants": 2},
                    },
                }
            ],
        }
    },
    "fix_319": {
        "sections": {
            "feedback_sentiment_report": [{"counts_by_sentiment": {"positive": 2, "neutral": 1, "negative": 1}}],
            "feedback_classification_report": [{"counts_by_classification": {"positive_feedback": 2}}],
        }
    },
    "growth_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_service.collect_growth_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_evidence.collect_growth_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_growth_review_records_for_tests()
    yield
    clear_growth_review_records_for_tests()


def test_growth_domains_and_authority_flags():
    result = build_growth_adoption_intelligence(session_id="gai-320")
    board = result.growth_adoption_intelligence
    assert board["growth_authority"] is False
    assert board["automatic_customer_outreach_enabled"] is False
    assert board["automatic_plan_upgrade_enabled"] is False
    assert board["automatic_customer_targeting_enabled"] is False
    assert board["automatic_growth_execution_enabled"] is False
    for key in GROWTH_ADOPTION_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_adoption_analytics_regression():
    registry = build_adoption_registry(evidence=_MOCK_EVIDENCE)
    report = build_adoption_analytics_report(evidence=_MOCK_EVIDENCE)
    assert registry["activated_customers"] == 3
    assert registry["cross_tenant_aggregation_forbidden"] is True
    assert report["sources"] == ["FIX 318"]
    assert report["adoption_rate_percent"] == 60.0
    assert report["provider_adoption_count"] == 2


def test_retention_regression():
    report = build_retention_intelligence_report(evidence=_MOCK_EVIDENCE)
    assert report["retained_customers"] == 3
    assert report["disengaged_customers"] == 1
    assert report["retention_cohorts"]


def test_expansion_regression():
    report = build_expansion_intelligence_report(evidence=_MOCK_EVIDENCE)
    assert report["workspace_growth"] == 6
    assert report["project_growth"] == 9
    assert report["plan_expansion"]
    assert report["upgrade_candidates"]


def test_success_pattern_regression():
    report = build_success_pattern_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 318", "FIX 319"]
    assert "onboarding_completed" in report["behaviors_linked_to_success"]
    assert report["provider_usage_linked_to_success"]


def test_churn_risk_regression():
    report = build_churn_risk_report(evidence=_MOCK_EVIDENCE)
    assert report["at_risk_count"] == 1
    assert report["adoption_failures"]
    assert report["validated"] is True


def test_growth_opportunity_regression():
    adoption = build_adoption_analytics_report(evidence=_MOCK_EVIDENCE)
    retention = build_retention_intelligence_report(evidence=_MOCK_EVIDENCE)
    expansion = build_expansion_intelligence_report(evidence=_MOCK_EVIDENCE)
    churn = build_churn_risk_report(evidence=_MOCK_EVIDENCE)
    success = build_success_pattern_report(evidence=_MOCK_EVIDENCE)
    registry = build_growth_opportunity_registry(
        adoption_report=adoption,
        retention_report=retention,
        expansion_report=expansion,
        churn_report=churn,
        success_report=success,
    )
    assert registry["count"] >= 3
    assert set(GROWTH_OPPORTUNITY_TYPES).issuperset(
        {opp["opportunity_type"] for opp in registry["opportunities"]}
    )
    assert all(opp["automatic_growth_execution_forbidden"] for opp in registry["opportunities"])


def test_priority_matrix_regression():
    adoption = build_adoption_analytics_report(evidence=_MOCK_EVIDENCE)
    retention = build_retention_intelligence_report(evidence=_MOCK_EVIDENCE)
    expansion = build_expansion_intelligence_report(evidence=_MOCK_EVIDENCE)
    churn = build_churn_risk_report(evidence=_MOCK_EVIDENCE)
    success = build_success_pattern_report(evidence=_MOCK_EVIDENCE)
    registry = build_growth_opportunity_registry(
        adoption_report=adoption,
        retention_report=retention,
        expansion_report=expansion,
        churn_report=churn,
        success_report=success,
    )
    matrix = build_growth_priority_matrix(registry=registry)
    assert matrix["ranked_opportunities"]
    assert matrix["highest_adoption_roi"]
    assert matrix["automatic_growth_execution_forbidden"] is True


def test_dashboard_regression():
    routed = route_growth_adoption_intelligence("show growth dashboard", session_id="gai-320")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_growth_adoption_intelligence"
    assert meta["route_id"] == GROWTH_ADOPTION_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert GROWTH_AUTHORITY_FIX_320 is False
    assert AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320 is False


def test_success_question_routing_regression():
    assert parse_growth_adoption_intelligence_intent("Which customers are at risk?") == {
        "action": "view",
        "focus": "churn_risk_report",
    }
    routed = route_growth_adoption_intelligence(
        "What growth opportunities have the highest ROI?",
        session_id="gai-320-q",
    )
    assert routed is not None
    assert "priority matrix" in routed[0].lower()


def test_growth_review_registry_record_only():
    append_growth_review_record(kind="growth_note", content="Track expansion candidates", session_id="gai-320")
    routed = route_growth_adoption_intelligence("growth note: monitor retention cohort", session_id="gai-320")
    assert routed is not None
    assert "humans decide actions" in routed[0].lower()
    assert len(list_growth_review_records()) == 2

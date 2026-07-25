# SPDX-License-Identifier: Apache-2.0
"""FIX 321 — customer journey intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_contract import (
    AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321,
    CUSTOMER_JOURNEY_INTELLIGENCE_DOMAINS,
    CUSTOMER_JOURNEY_INTELLIGENCE_ROUTE_ID,
    JOURNEY_AUTHORITY_FIX_321,
    JOURNEY_STAGES,
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
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_intent import (
    parse_customer_journey_intelligence_intent,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_router import (
    route_customer_journey_intelligence,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_service import (
    build_customer_journey_intelligence,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_store import (
    append_journey_review_record,
    clear_journey_review_records_for_tests,
    list_journey_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "cji-321",
    "sources_ok": {f"fix_{n}": True for n in (300, 301, 303, 311, 312, 318, 319, 320)},
    "fix_300": {
        "sections": {
            "tenant_dashboard": [
                {"organization_count": 5, "workspace_count": 7, "project_count": 10, "user_count": 15}
            ],
        }
    },
    "fix_301": {
        "sections": {
            "onboarding_progress_registry": [
                {
                    "started_count": 5,
                    "completed_count": 3,
                    "incomplete_steps": ["Connect provider"],
                }
            ],
        }
    },
    "fix_303": {
        "sections": {
            "provider_connection_dashboard": [{"connected_provider_count": 2}],
            "provider_connection_reports": [{"provider": "github", "connected_count": 2, "readiness": "ready"}],
        }
    },
    "fix_311": {
        "sections": {
            "public_product_dashboard": [{"visitor_count": 8, "feedback_items": ["Clear evaluation path"]}],
        }
    },
    "fix_312": {
        "sections": {
            "beta_cohort_registry": [{"admitted_count": 2, "participant_count": 3}],
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
            "provider_analytics_report": [{"most_connected_provider": "github", "readiness_failures": []}],
            "capability_usage_report": [
                {
                    "capabilities_used": ["Mission Control (PROVEN)"],
                    "capabilities_ignored": ["Autonomous deploy (PLANNED)"],
                    "capabilities_confusing": ["Beta workflow (EXPERIMENTAL)"],
                }
            ],
            "user_journey_report": [
                {
                    "success_predictors": ["onboarding_completed", "provider_connected"],
                    "stages": {
                        "activation": {"onboarding_completed": 3},
                        "retention": {"retained_subscriptions": 3, "at_risk_customers": 1},
                        "expansion": {"upgrade_candidates": 1, "beta_participants": 3},
                    },
                }
            ],
        }
    },
    "fix_319": {
        "sections": {
            "customer_feedback_dashboard": [{"positive_sentiment_count": 2, "negative_sentiment_count": 1}],
            "feedback_trend_report": [{"recurring_complaints": ["Provider setup confusion"]}],
            "customer_friction_report": [
                {
                    "onboarding_friction": ["Connect provider"],
                    "provider_friction": ["Railway not configured"],
                    "adoption_friction": [],
                }
            ],
        }
    },
    "fix_320": {
        "sections": {
            "growth_adoption_dashboard": [
                {
                    "activated_customers": 3,
                    "retained_customers": 3,
                    "workspace_growth": 7,
                }
            ],
            "adoption_registry": [{"activated_customers": 3}],
            "retention_intelligence_report": [
                {
                    "retention_cohorts": [
                        {"cohort": "retained", "count": 3},
                        {"cohort": "at_risk", "count": 1},
                    ],
                    "retention_trend": "rising",
                }
            ],
            "success_pattern_report": [
                {
                    "behaviors_linked_to_success": ["onboarding_completed"],
                    "onboarding_paths_linked_to_retention": ["completed_onboarding"],
                }
            ],
            "expansion_intelligence_report": [
                {
                    "plan_expansion": ["Starter to Pro"],
                    "upgrade_candidates": ["Starter to Pro"],
                }
            ],
        }
    },
    "journey_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_service.collect_journey_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_evidence.collect_journey_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_journey_review_records_for_tests()
    yield
    clear_journey_review_records_for_tests()


def test_journey_domains_and_authority_flags():
    result = build_customer_journey_intelligence(session_id="cji-321")
    board = result.customer_journey_intelligence
    assert board["journey_authority"] is False
    assert board["automatic_customer_targeting_enabled"] is False
    assert board["automatic_customer_intervention_enabled"] is False
    assert board["automatic_journey_modification_enabled"] is False
    for key in CUSTOMER_JOURNEY_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_journey_registry_regression():
    registry = build_customer_journey_registry(evidence=_MOCK_EVIDENCE)
    assert len(registry["entries"]) == len(JOURNEY_STAGES)
    assert registry["cross_tenant_journey_analysis_forbidden"] is True
    assert all(entry.get("tenant") == "cji-321" for entry in registry["entries"])
    assert registry["current_stage"] in JOURNEY_STAGES


def test_funnel_analysis_regression():
    report = build_journey_funnel_report(evidence=_MOCK_EVIDENCE)
    assert len(report["transitions"]) == 7
    assert report["transitions"][0]["from_stage"] == "awareness"
    assert report["validated"] is True


def test_dropoff_regression():
    report = build_journey_dropoff_report(evidence=_MOCK_EVIDENCE)
    assert "Connect provider" in report["abandonment_points"]
    assert report["stalled_journeys"]
    assert report["validated"] is True


def test_success_path_regression():
    report = build_journey_success_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 318", "FIX 319", "FIX 320"]
    assert "onboarding_completed" in report["successful_paths"]
    assert report["expansion_paths"]


def test_friction_regression():
    report = build_journey_friction_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 301", "FIX 303", "FIX 319"]
    assert report["onboarding_friction"]
    assert report["capability_discovery_friction"]


def test_cohort_regression():
    report = build_journey_cohort_report(evidence=_MOCK_EVIDENCE)
    assert report["cohorts"]
    assert report["cohort_retention"]
    assert report["validated"] is True


def test_opportunity_regression():
    dropoff = build_journey_dropoff_report(evidence=_MOCK_EVIDENCE)
    friction = build_journey_friction_report(evidence=_MOCK_EVIDENCE)
    success = build_journey_success_report(evidence=_MOCK_EVIDENCE)
    cohort = build_journey_cohort_report(evidence=_MOCK_EVIDENCE)
    registry = build_journey_opportunity_registry(
        dropoff_report=dropoff,
        friction_report=friction,
        success_report=success,
        cohort_report=cohort,
    )
    matrix = build_journey_priority_matrix(registry=registry)
    assert registry["count"] >= 3
    assert all(opp["automatic_customer_intervention_forbidden"] for opp in registry["opportunities"])
    assert matrix["ranked_opportunities"]
    assert matrix["automatic_customer_intervention_forbidden"] is True


def test_dashboard_regression():
    routed = route_customer_journey_intelligence("show customer journey dashboard", session_id="cji-321")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_customer_journey_intelligence"
    assert meta["route_id"] == CUSTOMER_JOURNEY_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert JOURNEY_AUTHORITY_FIX_321 is False
    assert AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321 is False


def test_success_question_routing_regression():
    assert parse_customer_journey_intelligence_intent("Where do customers drop off?") == {
        "action": "view",
        "focus": "journey_dropoff_report",
    }
    routed = route_customer_journey_intelligence(
        "What should improve in the customer journey?",
        session_id="cji-321-q",
    )
    assert routed is not None
    assert "priority matrix" in routed[0].lower()


def test_journey_review_registry_record_only():
    append_journey_review_record(kind="journey_note", content="Track onboarding drop-off", session_id="cji-321")
    routed = route_customer_journey_intelligence("journey note: monitor activation friction", session_id="cji-321")
    assert routed is not None
    assert "humans decide" in routed[0].lower()
    assert len(list_journey_review_records()) == 2

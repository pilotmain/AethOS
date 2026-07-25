# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — product analytics foundation tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
    ANALYTICS_AUTHORITY_FIX_318,
    AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318,
    CANONICAL_ANALYTICS_EVENTS,
    PRODUCT_ANALYTICS_FOUNDATION_DOMAINS,
    PRODUCT_ANALYTICS_FOUNDATION_ROUTE_ID,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evaluator import (
    build_analytics_event_registry,
    build_behavioral_opportunity_registry,
    build_capability_usage_report,
    build_commercial_analytics_report,
    build_customer_success_analytics_report,
    build_onboarding_analytics_report,
    build_provider_analytics_report,
    build_user_journey_report,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_intent import (
    parse_product_analytics_foundation_intent,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_router import (
    route_product_analytics_foundation,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service import (
    build_product_analytics_foundation,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_store import (
    append_analytics_review_record,
    clear_analytics_review_records_for_tests,
    list_analytics_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "paf-318",
    "sources_ok": {f"fix_{n}": True for n in (295, 296, 300, 301, 303, 305, 308, 310, 312)},
    "fix_300": {
        "sections": {
            "tenant_dashboard": [{"organization_count": 3, "workspace_count": 4, "project_count": 5, "user_count": 8}],
        }
    },
    "fix_301": {
        "sections": {
            "onboarding_progress_registry": [
                {
                    "completed_count": 2,
                    "started_count": 5,
                    "incomplete_steps": ["Connect provider", "Activate Mission Control"],
                    "drop_off_points": ["Connect provider"],
                }
            ],
        }
    },
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
            "experimental_capabilities": [{"items": ["Beta workflow (EXPERIMENTAL)"]}],
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
    "fix_305": {
        "sections": {
            "plan_registry": [{"plans": ["Starter", "Pro"]}],
            "subscription_registry": [{"active_subscriptions": ["sub-1", "sub-2"]}],
            "entitlement_registry": [{"utilization_summary": "partial"}],
        }
    },
    "fix_308": {
        "sections": {
            "upgrade_path_registry": [{"paths": ["Starter to Pro"]}],
            "commercial_analytics_dashboard": [{"top_plans": ["Pro"]}],
        }
    },
    "fix_310": {
        "sections": {
            "customer_health_registry": [{"healthy_count": 4, "at_risk_count": 1}],
            "customer_risk_registry": [{"at_risk_count": 1}],
            "customer_adoption_report": [{"engagement_trend": "rising"}],
        }
    },
    "fix_312": {
        "sections": {
            "beta_cohort_registry": [{"admitted_count": 1, "participant_count": 2}],
            "beta_success_metrics": [{"activation_rate": 0.5}],
        }
    },
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service.collect_analytics_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_evidence.collect_analytics_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_analytics_review_records_for_tests()
    yield
    clear_analytics_review_records_for_tests()


def test_product_analytics_domains_and_authority_flags():
    result = build_product_analytics_foundation(session_id="paf-318")
    board = result.product_analytics_foundation
    assert board["analytics_authority"] is False
    assert board["automatic_behavior_modification_enabled"] is False
    assert board["automatic_user_targeting_enabled"] is False
    for key in PRODUCT_ANALYTICS_FOUNDATION_DOMAINS:
        assert board["sections"][key]


def test_event_registry_regression():
    registry = build_analytics_event_registry(evidence=_MOCK_EVIDENCE)
    event_names = [row["event"] for row in registry["events"]]
    assert list(CANONICAL_ANALYTICS_EVENTS) == event_names
    assert registry["cross_tenant_analytics_forbidden"] is True


def test_onboarding_analytics_regression():
    report = build_onboarding_analytics_report(evidence=_MOCK_EVIDENCE)
    assert report["users_completed_onboarding"] == 2
    assert report["average_completion_rate_percent"] == 40.0
    assert "Connect provider" in report["drop_off_points"]


def test_capability_analytics_regression():
    report = build_capability_usage_report(evidence=_MOCK_EVIDENCE)
    assert "Mission Control (PROVEN)" in report["capabilities_used"]
    assert report["capabilities_ignored"]


def test_provider_analytics_regression():
    report = build_provider_analytics_report(evidence=_MOCK_EVIDENCE)
    assert report["most_connected_provider"] == "github"
    assert report["provider_adoption"]["github"] == 2


def test_commercial_analytics_regression():
    report = build_commercial_analytics_report(evidence=_MOCK_EVIDENCE)
    assert report["active_subscription_count"] == 2
    assert report["most_successful_plans"]


def test_customer_success_analytics_regression():
    report = build_customer_success_analytics_report(evidence=_MOCK_EVIDENCE)
    assert report["healthy_customers"] == 4
    assert report["at_risk_customers"] == 1


def test_behavioral_opportunity_regression():
    onboarding = build_onboarding_analytics_report(evidence=_MOCK_EVIDENCE)
    capability = build_capability_usage_report(evidence=_MOCK_EVIDENCE)
    provider = build_provider_analytics_report(evidence=_MOCK_EVIDENCE)
    journey = build_user_journey_report(evidence=_MOCK_EVIDENCE)
    registry = build_behavioral_opportunity_registry(
        onboarding_report=onboarding,
        capability_report=capability,
        provider_report=provider,
        journey_report=journey,
    )
    assert registry["count"] >= 2
    assert all(opp["automatic_behavior_modification_forbidden"] for opp in registry["opportunities"])


def test_dashboard_regression():
    routed = route_product_analytics_foundation("show analytics dashboard", session_id="paf-318")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_product_analytics_foundation"
    assert meta["route_id"] == PRODUCT_ANALYTICS_FOUNDATION_ROUTE_ID
    assert "surveillance" in body.lower()
    assert ANALYTICS_AUTHORITY_FIX_318 is False
    assert AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318 is False


def test_success_question_routing_regression():
    assert parse_product_analytics_foundation_intent("How many users complete onboarding?") == {
        "action": "view",
        "focus": "onboarding_analytics_report",
    }
    routed = route_product_analytics_foundation("Which behaviors predict success?", session_id="paf-318-q")
    assert routed is not None
    assert "Success predictors" in routed[0]


def test_analytics_review_registry_record_only():
    append_analytics_review_record(kind="analytics_note", content="Track onboarding drop-off", session_id="paf-318")
    routed = route_product_analytics_foundation("analytics note: monitor provider adoption", session_id="paf-318")
    assert routed is not None
    assert "surveillance" in routed[0].lower()
    assert len(list_analytics_review_records()) == 2

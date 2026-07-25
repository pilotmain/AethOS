# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — customer feedback intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_contract import (
    AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319,
    CUSTOMER_FEEDBACK_INTELLIGENCE_DOMAINS,
    CUSTOMER_FEEDBACK_INTELLIGENCE_ROUTE_ID,
    FEEDBACK_AUTHORITY_FIX_319,
    FEEDBACK_CLASSIFICATIONS,
    SENTIMENT_LABELS,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_evaluator import (
    build_capability_gap_report,
    build_customer_feedback_registry,
    build_customer_friction_report,
    build_feedback_classification_report,
    build_feedback_opportunity_registry,
    build_feedback_priority_matrix,
    build_feedback_sentiment_report,
    build_feedback_trend_report,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_intent import (
    parse_customer_feedback_intelligence_intent,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_router import (
    route_customer_feedback_intelligence,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_service import (
    build_customer_feedback_intelligence,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_store import (
    append_feedback_review_record,
    clear_feedback_review_records_for_tests,
    list_feedback_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "cfi-319",
    "sources_ok": {f"fix_{n}": True for n in (295, 296, 301, 303, 310, 311, 312, 317, 318)},
    "fix_295": {
        "sections": {
            "capability_registry": [{"capabilities": [{"name": "Mission Control"}], "capability_count": 1}],
        }
    },
    "fix_296": {
        "sections": {
            "proven_capabilities": [{"items": ["Mission Control (PROVEN)"]}],
            "operational_capabilities": [{"items": ["Provider inspection (OPERATIONAL)"]}],
        }
    },
    "fix_301": {
        "sections": {
            "onboarding_progress_registry": [
                {
                    "incomplete_steps": ["Connect provider", "Activate Mission Control"],
                }
            ],
        }
    },
    "fix_303": {
        "sections": {
            "provider_connection_dashboard": [{"connected_provider_count": 1}],
        }
    },
    "fix_310": {
        "sections": {
            "support_request_registry": [
                {"requests": [{"summary": "Need clearer onboarding guidance for provider setup"}]}
            ],
            "customer_success_dashboard": [{"observations": ["Customer loves Mission Control dashboard"]}],
        }
    },
    "fix_311": {
        "sections": {
            "public_product_dashboard": [{"feedback_items": ["Would like billing upgrade path clarity"]}],
        }
    },
    "fix_312": {
        "sections": {
            "beta_feedback_registry": [
                {"feedback_items": [{"summary": "Missing capability for autonomous deploy workflow"}]}
            ],
        }
    },
    "fix_317": {
        "sections": {
            "improvement_opportunity_registry": [{"opportunities": [{"title": "Improve onboarding"}]}],
        }
    },
    "fix_318": {
        "sections": {
            "onboarding_analytics_report": [{"drop_off_points": ["Connect provider"]}],
            "provider_analytics_report": [{"readiness_failures": ["Railway not configured"]}],
            "behavioral_opportunity_registry": [{"opportunities": [{"detail": "Low provider adoption"}]}],
        }
    },
    "feedback_review_records": [],
    "improvement_review_records": [],
    "analytics_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_service.collect_feedback_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_evidence.collect_feedback_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_feedback_review_records_for_tests()
    yield
    clear_feedback_review_records_for_tests()


def test_customer_feedback_domains_and_authority_flags():
    result = build_customer_feedback_intelligence(session_id="cfi-319")
    board = result.customer_feedback_intelligence
    assert board["feedback_authority"] is False
    assert board["automatic_feature_creation_enabled"] is False
    assert board["automatic_backlog_creation_enabled"] is False
    assert board["automatic_customer_contact_enabled"] is False
    for key in CUSTOMER_FEEDBACK_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_feedback_registry_regression():
    registry = build_customer_feedback_registry(evidence=_MOCK_EVIDENCE)
    assert registry["count"] >= 3
    assert registry["cross_tenant_aggregation_forbidden"] is True
    sources = {item["source"] for item in registry["items"]}
    assert "support_notes" in sources
    assert "beta_feedback" in sources


def test_classification_regression():
    registry = build_customer_feedback_registry(evidence=_MOCK_EVIDENCE)
    report = build_feedback_classification_report(items=registry["items"])
    assert set(report["counts_by_classification"]) <= set(FEEDBACK_CLASSIFICATIONS)
    assert report["validated"] is True


def test_sentiment_regression():
    registry = build_customer_feedback_registry(evidence=_MOCK_EVIDENCE)
    report = build_feedback_sentiment_report(items=registry["items"])
    assert set(report["counts_by_sentiment"]) <= set(SENTIMENT_LABELS)
    assert report["validated"] is True


def test_trend_analysis_regression():
    registry = build_customer_feedback_registry(evidence=_MOCK_EVIDENCE)
    classified = build_feedback_classification_report(items=registry["items"])
    trends = build_feedback_trend_report(classified_items=classified["items"])
    assert trends["emerging_themes"]
    assert trends["validated"] is True


def test_capability_gap_regression():
    registry = build_customer_feedback_registry(evidence=_MOCK_EVIDENCE)
    classified = build_feedback_classification_report(items=registry["items"])
    report = build_capability_gap_report(evidence=_MOCK_EVIDENCE, classified_items=classified["items"])
    assert report["sources"] == ["FIX 295", "FIX 296", "FIX 317"]
    assert report["validated"] is True


def test_friction_analysis_regression():
    report = build_customer_friction_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 301", "FIX 303", "FIX 318"]
    assert "Connect provider" in report["onboarding_friction"]
    assert report["provider_friction"]


def test_opportunity_ranking_regression():
    registry = build_customer_feedback_registry(evidence=_MOCK_EVIDENCE)
    classified = build_feedback_classification_report(items=registry["items"])
    trends = build_feedback_trend_report(classified_items=classified["items"])
    gaps = build_capability_gap_report(evidence=_MOCK_EVIDENCE, classified_items=classified["items"])
    friction = build_customer_friction_report(evidence=_MOCK_EVIDENCE)
    opportunities = build_feedback_opportunity_registry(
        classified_items=classified["items"],
        trend_report=trends,
        capability_gap_report=gaps,
        friction_report=friction,
    )
    matrix = build_feedback_priority_matrix(registry=opportunities)
    assert opportunities["count"] >= 2
    assert all(opp["automatic_work_creation_forbidden"] for opp in opportunities["opportunities"])
    assert matrix["ranked_opportunities"]
    assert matrix["automatic_work_creation_forbidden"] is True


def test_dashboard_regression():
    routed = route_customer_feedback_intelligence("show customer feedback dashboard", session_id="cfi-319")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_customer_feedback_intelligence"
    assert meta["route_id"] == CUSTOMER_FEEDBACK_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert FEEDBACK_AUTHORITY_FIX_319 is False
    assert AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319 is False


def test_success_question_routing_regression():
    assert parse_customer_feedback_intelligence_intent("What are customers asking for?") == {
        "action": "view",
        "focus": "feedback_trend_report",
    }
    routed = route_customer_feedback_intelligence(
        "What should the team consider improving next?",
        session_id="cfi-319-q",
    )
    assert routed is not None
    assert "priority matrix" in routed[0].lower()


def test_feedback_review_registry_record_only():
    append_feedback_review_record(kind="feedback_note", content="Track onboarding confusion", session_id="cfi-319")
    routed = route_customer_feedback_intelligence("feedback note: monitor trust concerns", session_id="cfi-319")
    assert routed is not None
    assert "automatic work creation" in routed[0].lower()
    assert len(list_feedback_review_records()) == 2

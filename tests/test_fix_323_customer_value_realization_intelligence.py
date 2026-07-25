# SPDX-License-Identifier: Apache-2.0
"""FIX 323 — customer value realization intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_contract import (
    AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323,
    CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_DOMAINS,
    CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_ROUTE_ID,
    VALUE_REALIZATION_AUTHORITY_FIX_323,
    VALUE_REALIZATION_LEVELS,
    VALUE_REALIZATION_SCORECARD_DIMENSIONS,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_evaluator import (
    build_capability_value_report,
    build_customer_success_outcome_report,
    build_expected_value_registry,
    build_journey_value_report,
    build_value_gap_report,
    build_value_opportunity_registry,
    build_value_outcome_registry,
    build_value_realization_scorecard,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_intent import (
    parse_customer_value_realization_intelligence_intent,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_router import (
    route_customer_value_realization_intelligence,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_service import (
    build_customer_value_realization_intelligence,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_store import (
    append_value_review_record,
    clear_value_review_records_for_tests,
    list_value_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "cvr-323",
    "sources_ok": {f"fix_{n}": True for n in (295, 301, 310, 318, 320, 321, 322)},
    "fix_295": {
        "sections": {
            "capability_registry": [{"capabilities": [{"name": "Mission Control"}], "capability_count": 2}],
        }
    },
    "fix_301": {
        "sections": {
            "onboarding_progress_registry": [
                {"steps": ["Create workspace", "Connect provider"], "completed_count": 1, "started_count": 2}
            ],
            "onboarding_activation_registry": [{"success_objectives": ["Activate Mission Control"]}],
        }
    },
    "fix_310": {
        "sections": {
            "customer_health_registry": [{"healthy_count": 4, "at_risk_count": 1}],
            "customer_risk_registry": [{"at_risk_count": 1}],
            "customer_adoption_report": [{"engagement_trend": "rising"}],
            "customer_success_dashboard": [{"observations": ["Reduce manual ops review time"]}],
        }
    },
    "fix_318": {
        "sections": {
            "onboarding_analytics_report": [{"average_completion_rate_percent": 70.0}],
            "capability_usage_report": [
                {
                    "capabilities_used": ["Mission Control (PROVEN)"],
                    "capabilities_ignored": ["Autonomous deploy (PLANNED)"],
                }
            ],
        }
    },
    "fix_320": {
        "sections": {
            "growth_adoption_dashboard": [{"workspace_growth": 5, "retained_customers": 4, "disengaged_customers": 1}],
            "retention_value_report": [{"capabilities_driving_retention": ["Mission Control (PROVEN)"]}],
        }
    },
    "fix_321": {
        "sections": {
            "customer_journey_registry": [{"current_stage": "retention"}],
            "journey_success_report": [
                {
                    "successful_paths": ["onboarding_completed"],
                    "high_retention_paths": ["completed_onboarding"],
                    "expansion_paths": ["Starter to Pro"],
                }
            ],
            "journey_funnel_report": [
                {"transitions": [{"from_stage": "onboarding", "to_stage": "activation", "conversion_rate_percent": 75.0}]}
            ],
        }
    },
    "fix_322": {
        "sections": {
            "customer_value_realization_report": [
                {
                    "realized_value": ["Mission Control adoption reduces manual coordination"],
                    "unrealized_value": ["Autonomous deploy workflow not yet adopted"],
                }
            ],
            "problem_solution_fit_report": [{"customer_problems": ["Manual ops overhead"]}],
        }
    },
    "value_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_service.collect_value_realization_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_evidence.collect_value_realization_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_value_review_records_for_tests()
    yield
    clear_value_review_records_for_tests()


def test_value_realization_domains_and_authority_flags():
    result = build_customer_value_realization_intelligence(session_id="cvr-323")
    board = result.customer_value_realization_intelligence
    assert board["value_realization_authority"] is False
    assert board["automatic_customer_success_enabled"] is False
    assert board["automatic_customer_outreach_enabled"] is False
    assert board["automatic_goal_modification_enabled"] is False
    for key in CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_value_outcome_regression():
    registry = build_value_outcome_registry(evidence=_MOCK_EVIDENCE)
    assert registry["count"] >= 3
    assert registry["cross_tenant_exposure_forbidden"] is True


def test_expected_value_regression():
    registry = build_expected_value_registry(evidence=_MOCK_EVIDENCE)
    assert registry["count"] >= 2
    assert "onboarding_expectations" in registry["sources"]


def test_value_gap_regression():
    outcomes = build_value_outcome_registry(evidence=_MOCK_EVIDENCE)
    expected = build_expected_value_registry(evidence=_MOCK_EVIDENCE)
    report = build_value_gap_report(outcome_registry=outcomes, expected_registry=expected, evidence=_MOCK_EVIDENCE)
    assert report["gaps"]
    assert report["validated"] is True


def test_capability_attribution_regression():
    report = build_capability_value_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 295", "FIX 318", "FIX 320"]
    assert report["highest_value_capabilities"]
    assert "Mission Control (PROVEN)" in [c["capability"] for c in report["capabilities"]]


def test_journey_attribution_regression():
    report = build_journey_value_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 321"]
    assert report["highest_value_journeys"]
    assert report["validated"] is True


def test_success_outcome_regression():
    report = build_customer_success_outcome_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 310", "FIX 320"]
    assert report["successful_customers"] == 4
    assert report["unsuccessful_customers"] == 1


def test_scorecard_regression():
    outcomes = build_value_outcome_registry(evidence=_MOCK_EVIDENCE)
    expected = build_expected_value_registry(evidence=_MOCK_EVIDENCE)
    gaps = build_value_gap_report(outcome_registry=outcomes, expected_registry=expected, evidence=_MOCK_EVIDENCE)
    capability = build_capability_value_report(evidence=_MOCK_EVIDENCE)
    success = build_customer_success_outcome_report(evidence=_MOCK_EVIDENCE)
    scorecard = build_value_realization_scorecard(
        outcome_registry=outcomes,
        gap_report=gaps,
        capability_value=capability,
        success_outcome=success,
        evidence=_MOCK_EVIDENCE,
    )
    assert set(scorecard["dimensions"]) == set(VALUE_REALIZATION_SCORECARD_DIMENSIONS)
    assert scorecard["overall_level"] in VALUE_REALIZATION_LEVELS


def test_dashboard_regression():
    routed = route_customer_value_realization_intelligence("show customer value dashboard", session_id="cvr-323")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_customer_value_realization_intelligence"
    assert meta["route_id"] == CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert VALUE_REALIZATION_AUTHORITY_FIX_323 is False
    assert AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323 is False


def test_success_question_routing_regression():
    assert parse_customer_value_realization_intelligence_intent("What value are customers realizing?") == {
        "action": "view",
        "focus": "value_outcome_registry",
    }
    routed = route_customer_value_realization_intelligence(
        "Which capabilities create the most value?",
        session_id="cvr-323-q",
    )
    assert routed is not None
    assert "Capability value" in routed[0]


def test_value_opportunity_regression():
    outcomes = build_value_outcome_registry(evidence=_MOCK_EVIDENCE)
    expected = build_expected_value_registry(evidence=_MOCK_EVIDENCE)
    gaps = build_value_gap_report(outcome_registry=outcomes, expected_registry=expected, evidence=_MOCK_EVIDENCE)
    capability = build_capability_value_report(evidence=_MOCK_EVIDENCE)
    journey = build_journey_value_report(evidence=_MOCK_EVIDENCE)
    success = build_customer_success_outcome_report(evidence=_MOCK_EVIDENCE)
    registry = build_value_opportunity_registry(
        gap_report=gaps,
        capability_value=capability,
        journey_value=journey,
        success_outcome=success,
    )
    assert registry["count"] >= 2
    assert all(opp["automatic_customer_success_forbidden"] for opp in registry["opportunities"])


def test_value_review_registry_record_only():
    append_value_review_record(kind="value_note", content="Track unrealized workflow value", session_id="cvr-323")
    routed = route_customer_value_realization_intelligence("value note: monitor capability value gaps", session_id="cvr-323")
    assert routed is not None
    assert "humans decide customer strategy" in routed[0].lower()
    assert len(list_value_review_records()) == 2

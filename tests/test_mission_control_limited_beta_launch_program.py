# SPDX-License-Identifier: Apache-2.0
"""FIX 312 — limited beta launch program tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_contract import (
    AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312,
    BETA_AUTHORITY_FIX_312,
    BETA_LAUNCH_RECOMMENDATIONS,
    LIMITED_BETA_LAUNCH_PROGRAM_ROUTE_ID,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_evaluator import (
    derive_beta_launch_recommendation,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_intent import (
    parse_limited_beta_launch_program_intent,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
    build_limited_beta_launch_program,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
    append_limited_beta_launch_program_record,
    clear_limited_beta_launch_program_records_for_tests,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_store import (
    clear_public_product_experience_records_for_tests,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_store import (
    clear_saas_launch_readiness_assessment_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_limited_beta_launch_program_records_for_tests()
    clear_saas_launch_readiness_assessment_records_for_tests()
    clear_public_product_experience_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_limited_beta_launch_program_records_for_tests()
    clear_saas_launch_readiness_assessment_records_for_tests()
    clear_public_product_experience_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_limited_beta_launch_program_intent():
    assert parse_limited_beta_launch_program_intent("show beta launch program") == {
        "action": "view",
        "focus": "beta_operations_dashboard",
    }
    assert parse_limited_beta_launch_program_intent("show beta cohorts") == {
        "action": "view",
        "focus": "beta_cohort_registry",
    }
    parsed = parse_limited_beta_launch_program_intent(
        "beta admission review approve: Human approves beta admission review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "beta_admission_review_decision_approve",
        "content": "Human approves beta admission review only",
    }


def test_build_limited_beta_launch_program():
    result = build_limited_beta_launch_program(session_id="mc-lblp-312")
    assert result.ok is True
    board = result.limited_beta_launch_program
    assert board["beta_authority"] is False
    assert board["automatic_customer_provisioning_enabled"] is False
    sections = board["sections"]
    for key in (
        "beta_cohort_registry",
        "beta_candidate_registry",
        "beta_admission_review_registry",
        "beta_readiness_report",
        "beta_feedback_registry",
        "beta_risk_registry",
        "beta_success_metrics",
        "beta_operations_dashboard",
        "beta_evidence_registry",
        "beta_launch_recommendation",
    ):
        assert sections[key]


def test_cohorts_compose_correctly():
    result = build_limited_beta_launch_program(session_id="mc-lblp-cohorts")
    registry = result.limited_beta_launch_program["sections"]["beta_cohort_registry"][0]
    assert registry["cohort_count"] >= 1
    assert all("cohort_name" in row for row in registry["cohorts"])


def test_admission_reviews_compose_correctly():
    append_limited_beta_launch_program_record(
        kind="beta_admission_review_decision_approve",
        content="Human approves first beta cohort admission",
        session_id="mc-lblp-admission",
    )
    result = build_limited_beta_launch_program(session_id="mc-lblp-admission")
    registry = result.limited_beta_launch_program["sections"]["beta_admission_review_registry"][0]
    assert registry["admission_review_decision_approve"] is True
    assert len(registry["review_history"]) >= 1


def test_beta_readiness_includes_fix_309():
    result = build_limited_beta_launch_program(session_id="mc-lblp-readiness")
    readiness = result.limited_beta_launch_program["sections"]["beta_readiness_report"][0]
    assert "FIX 309" in readiness["evidence_sources"]
    assert any(check["check_id"] == "launch_assessment" for check in readiness["checks"])


def test_success_metrics_aggregate():
    result = build_limited_beta_launch_program(session_id="mc-lblp-metrics")
    metrics = result.limited_beta_launch_program["sections"]["beta_success_metrics"][0]
    assert "activation_rate" in metrics
    assert "onboarding_completion" in metrics
    assert "customer_health_score" in metrics


def test_launch_recommendation_derived_from_evidence():
    recommendation = derive_beta_launch_recommendation(
        overall_launch_status="BLOCKED",
        at_risk_count=2,
        risk_count=6,
        healthy_count=0,
        admission_approve_count=0,
        feedback_count=0,
    )
    assert recommendation == "DO_NOT_LAUNCH"
    assert recommendation in BETA_LAUNCH_RECOMMENDATIONS

    result = build_limited_beta_launch_program(session_id="mc-lblp-rec")
    rec = result.limited_beta_launch_program["sections"]["beta_launch_recommendation"][0]
    assert rec["recommendation"] in BETA_LAUNCH_RECOMMENDATIONS
    assert rec["automatic_launch_performed"] is False


def test_no_provisioning_authority():
    result = build_limited_beta_launch_program(session_id="mc-lblp-no-prov")
    board = result.limited_beta_launch_program
    sources = board["sources"]
    rec = board["sections"]["beta_launch_recommendation"][0]
    assert board["beta_authority"] is False
    assert sources["user_provisioning_performed"] is False
    assert rec["customer_provisioning_performed"] is False


def test_regression_show_beta_launch_program():
    turn = resolve_chat_turn("show beta launch program", session_id="mc-lblp-regression")
    assert turn.intent == "mission_control_limited_beta_launch_program"
    lowered = turn.reply.lower()
    assert "beta" in lowered
    assert "recommendation" in lowered or "cohort" in lowered
    assert "provisioning" in lowered or "admission" in lowered or "humans" in lowered


def test_authority_flags():
    assert BETA_AUTHORITY_FIX_312 is False
    assert AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312 is False


def test_chat_route():
    turn = resolve_chat_turn("show beta dashboard", session_id="mc-lblp-chat")
    assert turn.intent == "mission_control_limited_beta_launch_program"
    assert (turn.meta or {}).get("route_id") == LIMITED_BETA_LAUNCH_PROGRAM_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/limited-beta-launch-program",
        params={"session_id": "mc-lblp-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["beta_authority"] is False
    assert body["limited_beta_launch_program"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/limited-beta-launch-program",
        json={
            "session_id": "mc-lblp-api",
            "kind": "beta_candidate_note",
            "content": "Candidate org reviewed for limited beta — no provisioning performed",
            "domain": "beta_candidate_registry",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

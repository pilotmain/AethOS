# SPDX-License-Identifier: Apache-2.0
"""FIX 313 — launch operations center tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.launch_operations_center.launch_operations_center_contract import (
    AUTOMATIC_LAUNCH_ENABLED_FIX_313,
    LAUNCH_OPERATIONS_AUTHORITY_FIX_313,
    LAUNCH_OPERATIONS_CENTER_ROUTE_ID,
    LAUNCH_RECOMMENDATIONS,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_evaluator import (
    aggregate_blockers,
    derive_launch_recommendation,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_intent import (
    parse_launch_operations_center_intent,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
    build_launch_operations_center,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_store import (
    clear_launch_operations_center_records_for_tests,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
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
    clear_launch_operations_center_records_for_tests()
    clear_limited_beta_launch_program_records_for_tests()
    clear_saas_launch_readiness_assessment_records_for_tests()
    clear_public_product_experience_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_launch_operations_center_records_for_tests()
    clear_limited_beta_launch_program_records_for_tests()
    clear_saas_launch_readiness_assessment_records_for_tests()
    clear_public_product_experience_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_launch_operations_center_intent():
    assert parse_launch_operations_center_intent("show launch operations") == {
        "action": "view",
        "focus": "launch_operations_dashboard",
    }
    assert parse_launch_operations_center_intent("show launch blockers") == {
        "action": "view",
        "focus": "launch_blocker_registry",
    }
    parsed = parse_launch_operations_center_intent(
        "launch operations review approve: Human approves launch operations review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "launch_operations_review_decision_approve",
        "content": "Human approves launch operations review only",
    }


def test_build_launch_operations_center():
    result = build_launch_operations_center(session_id="mc-loc-313")
    assert result.ok is True
    board = result.launch_operations_center
    assert board["launch_operations_authority"] is False
    assert board["automatic_launch_enabled"] is False
    sections = board["sections"]
    for key in (
        "launch_status_registry",
        "launch_blocker_registry",
        "launch_risk_dashboard",
        "beta_operations_monitor",
        "customer_operations_monitor",
        "platform_operations_monitor",
        "provider_operations_monitor",
        "launch_evidence_registry",
        "launch_recommendation",
        "launch_operations_dashboard",
    ):
        assert sections[key]


def test_launch_blockers_aggregate():
    blockers = aggregate_blockers(
        launch_blockers=["launch blocker"],
        beta_blockers=["beta blocker"],
        operational_blockers=["ops blocker"],
        customer_blockers=["customer blocker"],
    )
    assert len(blockers) == 4
    sources = {row["source"] for row in blockers}
    assert "FIX 309" in sources
    assert "FIX 312" in sources


def test_beta_operations_compose():
    result = build_launch_operations_center(session_id="mc-loc-beta")
    monitor = result.launch_operations_center["sections"]["beta_operations_monitor"][0]
    assert monitor["evidence_sources"] == ["FIX 312"]
    assert "active_cohort_count" in monitor


def test_customer_operations_compose():
    result = build_launch_operations_center(session_id="mc-loc-customer")
    monitor = result.launch_operations_center["sections"]["customer_operations_monitor"][0]
    assert monitor["evidence_sources"] == ["FIX 310"]
    assert "healthy_count" in monitor


def test_launch_risks_aggregate():
    result = build_launch_operations_center(session_id="mc-loc-risks")
    dashboard = result.launch_operations_center["sections"]["launch_risk_dashboard"][0]
    assert "product" in dashboard
    assert "operational" in dashboard
    assert dashboard["risk_count"] >= 0


def test_recommendation_derived_from_evidence():
    recommendation = derive_launch_recommendation(
        overall_launch_status="BLOCKED",
        beta_recommendation="DO_NOT_LAUNCH",
        blocker_count=2,
        critical_risk_count=1,
        at_risk_count=3,
        healthy_count=0,
        platform_healthy=False,
    )
    assert recommendation == "BLOCK_LAUNCH"
    assert recommendation in LAUNCH_RECOMMENDATIONS

    result = build_launch_operations_center(session_id="mc-loc-rec")
    rec = result.launch_operations_center["sections"]["launch_recommendation"][0]
    assert rec["recommendation"] in LAUNCH_RECOMMENDATIONS
    assert rec["launch_execution_performed"] is False


def test_no_launch_authority_paths():
    result = build_launch_operations_center(session_id="mc-loc-no-launch")
    board = result.launch_operations_center
    sources = board["sources"]
    dashboard = board["sections"]["launch_operations_dashboard"][0]
    assert board["launch_operations_authority"] is False
    assert sources["launch_execution_performed"] is False
    assert dashboard["launch_execution_performed"] is False


def test_regression_show_launch_operations():
    turn = resolve_chat_turn("show launch operations", session_id="mc-loc-regression")
    assert turn.intent == "mission_control_launch_operations_center"
    lowered = turn.reply.lower()
    assert "launch" in lowered
    assert "recommendation" in lowered or "phase" in lowered
    assert "authority" in lowered or "humans" in lowered


def test_authority_flags():
    assert LAUNCH_OPERATIONS_AUTHORITY_FIX_313 is False
    assert AUTOMATIC_LAUNCH_ENABLED_FIX_313 is False


def test_chat_route():
    turn = resolve_chat_turn("show launch status", session_id="mc-loc-chat")
    assert turn.intent == "mission_control_launch_operations_center"
    assert (turn.meta or {}).get("route_id") == LAUNCH_OPERATIONS_CENTER_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/launch-operations-center",
        params={"session_id": "mc-loc-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["launch_operations_authority"] is False
    assert body["launch_operations_center"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/launch-operations-center",
        json={
            "session_id": "mc-loc-api",
            "kind": "launch_operations_note",
            "content": "Launch ops review complete — no launch execution performed",
            "domain": "launch_operations_dashboard",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

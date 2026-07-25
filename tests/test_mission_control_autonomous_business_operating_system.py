# SPDX-License-Identifier: Apache-2.0
"""FIX 290 — autonomous business operating system tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_contract import (
    AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_ROUTE_ID,
    BUSINESS_AUTHORITY_FIX_290,
    BUSINESS_DOMAINS,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_intent import (
    parse_autonomous_business_operating_system_intent,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_service import (
    build_autonomous_business_operating_system,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_store import (
    append_autonomous_business_operating_system_record,
    clear_autonomous_business_operating_system_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_autonomous_business_operating_system_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_autonomous_business_operating_system_records_for_tests()
    get_settings.cache_clear()


def test_autonomous_business_operating_system_intent():
    assert parse_autonomous_business_operating_system_intent(
        "show business operating system"
    ) == {"action": "view"}
    parsed = parse_autonomous_business_operating_system_intent(
        "business decision approve: Operator approves initiative portfolio for Q3 delivery"
    )
    assert parsed == {
        "action": "record",
        "kind": "human_business_decision_approve",
        "content": "Operator approves initiative portfolio for Q3 delivery",
    }
    note = parse_autonomous_business_operating_system_intent(
        "customer domain note: Enterprise segment requesting faster onboarding workflow"
    )
    assert note is not None
    assert note["kind"] == "customer_domain_note"
    assert note["business_domain"] == "customer"


def test_build_autonomous_business_operating_system():
    result = build_autonomous_business_operating_system(session_id="mc-abos-290")
    assert result.ok is True
    board = result.autonomous_business_operating_system
    assert board["business_authority"] is False
    assert board["automatic_business_execution_enabled"] is False
    assert board["customer_mutation_authority"] is False
    assert board["billing_authority"] is False
    sections = board["sections"]
    assert sections["product_portfolio_registry"]
    assert sections["customer_intelligence_registry"]
    assert sections["revenue_intelligence_registry"]
    assert sections["team_operating_registry"]
    assert sections["project_portfolio_registry"]
    assert sections["business_operations_registry"]
    assert sections["business_goal_registry"]
    assert sections["strategic_alignment_graph"]
    assert sections["business_opportunity_portfolio"]
    assert sections["business_health_dashboard"]
    assert sections["business_risk_dashboard"]
    assert sections["business_operating_memory"]
    assert sections["business_operating_dashboard"]
    assert len(sections["business_domain_registries"]) == len(BUSINESS_DOMAINS)


def test_human_business_decision_updates_dashboard():
    append_autonomous_business_operating_system_record(
        kind="human_business_decision_approve",
        content="Operator approves business initiative recommendations for governed delivery planning",
        session_id="mc-abos-290",
    )
    result = build_autonomous_business_operating_system(session_id="mc-abos-290")
    dashboard = result.autonomous_business_operating_system["sections"]["business_operating_dashboard"][0]
    assert result.autonomous_business_operating_system["human_business_decision_approve"] is True
    assert dashboard["recommends_future_initiatives"] is True


def test_business_goal_note_in_memory():
    append_autonomous_business_operating_system_record(
        kind="business_goal_note",
        content="Increase portfolio delivery velocity while maintaining governance compliance",
        session_id="mc-abos-290",
        goal_id="goal-delivery-velocity",
    )
    result = build_autonomous_business_operating_system(session_id="mc-abos-290")
    memory = result.autonomous_business_operating_system["sections"]["business_operating_memory"][0]
    goals = result.autonomous_business_operating_system["sections"]["business_goal_registry"][0]
    assert memory["goal_count"] >= 1
    assert goals["objective_count"] >= 1


def test_authority_flags():
    assert BUSINESS_AUTHORITY_FIX_290 is False
    assert AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290 is False


def test_chat_route():
    turn = resolve_chat_turn("show business operating dashboard", session_id="mc-abos-chat")
    assert turn.intent == "mission_control_autonomous_business_operating_system"
    assert (turn.meta or {}).get("route_id") == AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/autonomous-business-operating-system",
        params={"session_id": "mc-abos-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["business_authority"] is False
    assert body["autonomous_business_operating_system"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/autonomous-business-operating-system/record",
        json={
            "session_id": "mc-abos-api",
            "kind": "customer_insight_note",
            "content": "Pilot customers report friction in multi-repo trust onboarding",
            "business_domain": "customer",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

# SPDX-License-Identifier: Apache-2.0
"""FIX 270 — autonomous product stewardship tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_contract import (
    AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_ROUTE_ID,
    PORTFOLIO_REPOSITORIES,
    PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_intent import (
    parse_autonomous_product_stewardship_intent,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_service import (
    build_autonomous_product_stewardship,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_store import (
    append_autonomous_product_stewardship_record,
    clear_autonomous_product_stewardship_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_autonomous_product_stewardship_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_autonomous_product_stewardship_records_for_tests()
    get_settings.cache_clear()


def test_autonomous_product_stewardship_intent():
    assert parse_autonomous_product_stewardship_intent("show product stewardship") == {"action": "view"}
    parsed = parse_autonomous_product_stewardship_intent(
        "stewardship decision approve: Operator approves stewardship backlog for governed delivery planning"
    )
    assert parsed == {
        "action": "record",
        "kind": "human_stewardship_decision_approve",
        "content": "Operator approves stewardship backlog for governed delivery planning",
    }
    note = parse_autonomous_product_stewardship_intent(
        "engineering stewardship observation: Reduce verification friction in Atlas Trader pilots"
    )
    assert note is not None
    assert note["kind"] == "engineering_stewardship_observation"


def test_build_autonomous_product_stewardship():
    result = build_autonomous_product_stewardship(session_id="mc-aps-270")
    assert result.ok is True
    board = result.autonomous_product_stewardship
    assert board["product_stewardship_authority"] is False
    assert board["automatic_improvement_enabled"] is False
    assert board["deployment_authority"] is False
    sections = board["sections"]
    assert sections["product_health_report"]
    assert sections["engineering_stewardship_report"]
    assert sections["operational_stewardship_report"]
    assert sections["governance_stewardship_report"]
    assert sections["portfolio_stewardship_report"]
    assert sections["stewardship_opportunity_registry"]
    assert sections["stewardship_priority_matrix"]
    assert sections["stewardship_backlog"]
    assert sections["product_stewardship_dashboard"]
    assert sections["product_stewardship_memory"]
    assert len(board["repositories"]) == len(PORTFOLIO_REPOSITORIES)


def test_human_stewardship_decision_updates_dashboard():
    append_autonomous_product_stewardship_record(
        kind="human_stewardship_decision_approve",
        content="Operator approves top stewardship recommendations for governed delivery planning",
        session_id="mc-aps-270",
    )
    result = build_autonomous_product_stewardship(session_id="mc-aps-270")
    dashboard = result.autonomous_product_stewardship["sections"]["product_stewardship_dashboard"][0]
    assert result.autonomous_product_stewardship["human_stewardship_decision_approve"] is True
    assert dashboard["feeds_governed_delivery_planning"] is True


def test_operator_observation_in_registry():
    append_autonomous_product_stewardship_record(
        kind="operational_stewardship_observation",
        content="Deploy quality signals suggest monitoring gaps across Nexora services",
        session_id="mc-aps-270",
        repository="pilotmain/nexora-monorepo-starter",
    )
    result = build_autonomous_product_stewardship(session_id="mc-aps-270")
    registry = result.autonomous_product_stewardship["sections"]["stewardship_opportunity_registry"][0]
    assert registry["operator_observations"]


def test_authority_flags():
    assert PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270 is False
    assert AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270 is False


def test_chat_route():
    turn = resolve_chat_turn("show portfolio stewardship dashboard", session_id="mc-aps-chat")
    assert turn.intent == "mission_control_autonomous_product_stewardship"
    assert (turn.meta or {}).get("route_id") == AUTONOMOUS_PRODUCT_STEWARDSHIP_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/autonomous-product-stewardship",
        params={"session_id": "mc-aps-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["product_stewardship_authority"] is False
    assert body["autonomous_product_stewardship"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/autonomous-product-stewardship/record",
        json={
            "session_id": "mc-aps-api",
            "kind": "stewardship_backlog_note",
            "content": "Prioritize governance friction reduction after human review",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

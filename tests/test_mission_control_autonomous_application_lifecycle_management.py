# SPDX-License-Identifier: Apache-2.0
"""FIX 280 — autonomous application lifecycle management tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_contract import (
    AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_ROUTE_ID,
    LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280,
    LIFECYCLE_STAGES,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_intent import (
    parse_autonomous_application_lifecycle_management_intent,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_service import (
    build_autonomous_application_lifecycle_management,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_store import (
    append_autonomous_application_lifecycle_management_record,
    clear_autonomous_application_lifecycle_management_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_autonomous_application_lifecycle_management_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_autonomous_application_lifecycle_management_records_for_tests()
    get_settings.cache_clear()


def test_autonomous_application_lifecycle_management_intent():
    assert parse_autonomous_application_lifecycle_management_intent(
        "show application lifecycle management"
    ) == {"action": "view"}
    parsed = parse_autonomous_application_lifecycle_management_intent(
        "lifecycle decision approve: Operator approves lifecycle transition into governed delivery planning"
    )
    assert parsed == {
        "action": "record",
        "kind": "human_lifecycle_decision_approve",
        "content": "Operator approves lifecycle transition into governed delivery planning",
    }
    note = parse_autonomous_application_lifecycle_management_intent(
        "delivery lifecycle note: Track PR readiness across portfolio repositories"
    )
    assert note is not None
    assert note["kind"] == "delivery_lifecycle_note"
    assert note["lifecycle_stage"] == "delivery"


def test_build_autonomous_application_lifecycle_management():
    result = build_autonomous_application_lifecycle_management(session_id="mc-aalm-280")
    assert result.ok is True
    board = result.autonomous_application_lifecycle_management
    assert board["lifecycle_management_authority"] is False
    assert board["automatic_lifecycle_execution_enabled"] is False
    assert board["deployment_authority"] is False
    assert board["rollback_authority"] is False
    sections = board["sections"]
    assert len(sections["lifecycle_stage_registry"]) == len(LIFECYCLE_STAGES)
    assert sections["application_lifecycle_timeline"]
    assert sections["lifecycle_health_dashboard"]
    assert sections["lifecycle_risk_dashboard"]
    assert sections["lifecycle_opportunity_registry"]
    assert sections["application_lifecycle_memory"]
    assert sections["lifecycle_management_dashboard"]
    assert board["current_lifecycle_stage"] in LIFECYCLE_STAGES


def test_human_lifecycle_decision_updates_dashboard():
    append_autonomous_application_lifecycle_management_record(
        kind="human_lifecycle_decision_approve",
        content="Operator approves lifecycle recommendations for governed delivery planning",
        session_id="mc-aalm-280",
    )
    result = build_autonomous_application_lifecycle_management(session_id="mc-aalm-280")
    dashboard = result.autonomous_application_lifecycle_management["sections"]["lifecycle_management_dashboard"][0]
    assert result.autonomous_application_lifecycle_management["human_lifecycle_decision_approve"] is True
    assert dashboard["feeds_governed_delivery_planning"] is True


def test_lifecycle_note_in_memory():
    append_autonomous_application_lifecycle_management_record(
        kind="operations_lifecycle_note",
        content="Monitoring gaps detected in Nexora deployment stage",
        session_id="mc-aalm-280",
        lifecycle_stage="operations",
    )
    result = build_autonomous_application_lifecycle_management(session_id="mc-aalm-280")
    memory = result.autonomous_application_lifecycle_management["sections"]["application_lifecycle_memory"][0]
    assert memory["observation_count"] >= 1


def test_authority_flags():
    assert LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280 is False
    assert AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280 is False


def test_chat_route():
    turn = resolve_chat_turn("show lifecycle management dashboard", session_id="mc-aalm-chat")
    assert turn.intent == "mission_control_autonomous_application_lifecycle_management"
    assert (turn.meta or {}).get("route_id") == AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/autonomous-application-lifecycle-management",
        params={"session_id": "mc-aalm-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["lifecycle_management_authority"] is False
    assert body["autonomous_application_lifecycle_management"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/autonomous-application-lifecycle-management/record",
        json={
            "session_id": "mc-aalm-api",
            "kind": "lifecycle_transition_note",
            "content": "Reviewed transition from delivery to deployment readiness",
            "lifecycle_stage": "deployment",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

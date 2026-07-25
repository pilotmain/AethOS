# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — bounded multi-agent delivery execution tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
    AGENT_EXECUTION_AUTHORITY_FIX_189,
    AGENT_EXECUTION_PIPELINE_ORDER,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ROUTE_ID,
    MERGE_AUTHORITY_FIX_189,
    PROVIDER_AUTHORITY_FIX_189,
    RAILWAY_AUTHORITY_FIX_189,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_intent import (
    is_bounded_multi_agent_delivery_execution_intent,
    parse_bounded_multi_agent_delivery_execution_record_intent,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
    build_bounded_multi_agent_delivery_execution,
    run_bounded_multi_agent_delivery_execution,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
    clear_bounded_multi_agent_delivery_execution_records_for_tests,
)
from tests.test_mission_control_bounded_execution_participation import _participation_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    get_settings.cache_clear()


def test_bounded_agent_delivery_execution_intent():
    assert is_bounded_multi_agent_delivery_execution_intent("show bounded agent delivery execution")
    assert not is_bounded_multi_agent_delivery_execution_intent("agent merge now")


def test_agent_execution_record_intent():
    parsed = parse_bounded_multi_agent_delivery_execution_record_intent(
        "agent execution receipt: planner package complete within envelope"
    )
    assert parsed == ("agent_execution_receipt", "planner package complete within envelope")


def test_build_agent_execution_blocked_without_gates():
    result = build_bounded_multi_agent_delivery_execution(session_id="fix-189-test")
    assert result.ok is True
    report = result.bounded_multi_agent_delivery_execution
    assert report["agent_execution_authority"] is AGENT_EXECUTION_AUTHORITY_FIX_189
    assert report["merge_authority"] is MERGE_AUTHORITY_FIX_189
    assert report["railway_authority"] is RAILWAY_AUTHORITY_FIX_189
    assert report["provider_authority"] is PROVIDER_AUTHORITY_FIX_189
    assert report["pipeline_state"] == "BLOCKED"
    assert "fix_170_authorization_not_granted" in result.blockers


def test_build_agent_execution_ready_with_participation_stack():
    _participation_stack("fix-189-stack")
    result = build_bounded_multi_agent_delivery_execution(session_id="fix-189-stack")
    gates = result.bounded_multi_agent_delivery_execution["sections"]["execution_gates"][0]
    assert gates["eligible_to_run_pipeline"] is True
    packages = result.bounded_multi_agent_delivery_execution["sections"]["agent_execution_packages"]
    assert len(packages) == len(AGENT_EXECUTION_PIPELINE_ORDER)


def test_run_pipeline_mocked_executors():
    _participation_stack("fix-189-run")
    mock_output = {
        "agent_role_id": "planner_agent",
        "status": "completed",
        "work_performed": True,
        "artifact_type": "governed_implementation_plan",
        "blockers": [],
    }

    def _mock_runner(*, session_id: str, plan_id: str | None) -> dict:
        return {**mock_output, "agent_role_id": "planner_agent"}

    with patch.dict(
        "aethos_core.mission_control.bounded_multi_agent_delivery_execution."
        "bounded_multi_agent_delivery_execution_executors.EXECUTION_RUNNERS",
        {role: _mock_runner for role in AGENT_EXECUTION_PIPELINE_ORDER},
    ):
        outcome = run_bounded_multi_agent_delivery_execution(session_id="fix-189-run")

    assert len(outcome.agent_outputs) == len(AGENT_EXECUTION_PIPELINE_ORDER)
    assert all(o.get("work_performed") for o in outcome.agent_outputs)


def test_run_pipeline_blocked_without_gates():
    outcome = run_bounded_multi_agent_delivery_execution(session_id="fix-189-blocked")
    assert outcome.ok is False
    assert outcome.blockers


def test_chat_route_show_bounded_agent_delivery_execution():
    _participation_stack("fix-189-chat")
    turn = resolve_chat_turn("show bounded agent delivery execution", session_id="fix-189-chat")
    assert turn.intent == "mission_control_bounded_multi_agent_delivery_execution"
    assert (turn.meta or {}).get("route_id") == BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ROUTE_ID


def test_agent_execution_api():
    _participation_stack("fix-189-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/bounded-multi-agent-delivery-execution",
        params={"session_id": "fix-189-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_execution_authority"] is False
    assert payload["bounded_multi_agent_delivery_execution"]["execution_ready"] is True

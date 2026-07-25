# SPDX-License-Identifier: Apache-2.0
"""FIX 182 — repo pilot readiness dashboard."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_contract import (
    REPO_PILOT_READINESS_DASHBOARD_ROUTE_ID,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_intent import (
    is_repo_pilot_readiness_dashboard_intent,
    parse_repo_pilot_readiness_dashboard_record_intent,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    build_repo_pilot_readiness_dashboard,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_store import (
    clear_repo_pilot_readiness_dashboard_records_for_tests,
)
from tests.test_mission_control_end_to_end_repo_development_pilot_harness import _pilot_harness_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
        clear_bounded_execution_participation_records_for_tests,
    )
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
        clear_frozen_gate_execution_request_adapter_records_for_tests,
    )
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
        clear_frozen_gate_intake_preview_records_for_tests,
    )
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
        clear_gate_routed_lane_entry_handoff_records_for_tests,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_store import (
        clear_governed_chat_command_invocation_from_handoff_records_for_tests,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
        clear_human_lane_admission_decision_records_for_tests,
    )
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_repo_pilot_readiness_dashboard_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_repo_pilot_readiness_dashboard_records_for_tests()
    get_settings.cache_clear()


def _readiness_stack(session: str) -> None:
    _pilot_harness_stack(session)


def test_repo_pilot_readiness_dashboard_intent():
    assert is_repo_pilot_readiness_dashboard_intent("show pilot readiness")
    assert is_repo_pilot_readiness_dashboard_intent("pilot readiness dashboard")
    assert is_repo_pilot_readiness_dashboard_intent("repo pilot preflight")
    assert not is_repo_pilot_readiness_dashboard_intent("run pilot")


def test_repo_pilot_readiness_dashboard_record_intent_parse():
    parsed = parse_repo_pilot_readiness_dashboard_record_intent(
        "readiness repo: pilotmain/AethOS"
    )
    assert parsed == ("repo_selection_note", "pilotmain/AethOS")


def test_repo_pilot_readiness_dashboard_composes_upstream_not_duplicates():
    session = "mc-rprd-compose-182"
    _readiness_stack(session)
    result = build_repo_pilot_readiness_dashboard(session_id=session)
    assert result.ok is True
    dashboard = result.repo_pilot_readiness_dashboard
    section_keys = set(dashboard.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_181)
    assert dashboard["composes_upstream_layers_not_duplicates"] is True
    assert dashboard["sources"]["composes_end_to_end_repo_development_pilot_harness"] is True
    assert dashboard["readiness_dashboard_not_pilot_execution"] is True
    assert dashboard["pilot_execution_performed"] is False
    assert "pilot_blocker_list" in section_keys
    assert "approval_friction_summary" in section_keys


def test_repo_pilot_readiness_dashboard_api_readonly():
    session = "mc-rprd-182"
    _readiness_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/repo-pilot-readiness-dashboard",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["pilot_execution_performed"] is False
    assert body["readiness_visibility_only"] is True
    dashboard = body["repo_pilot_readiness_dashboard"]
    assert dashboard["schema_version"] == "mission_control_repo_pilot_readiness_dashboard_v1"
    assert "github_auth_status_readiness" in dashboard["sections"]
    assert "Repo Pilot Readiness Dashboard" in body["markdown"]


def test_repo_pilot_readiness_dashboard_record_persists():
    session = "mc-rprd-record-182"
    _readiness_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/repo-pilot-readiness-dashboard/record",
        json={
            "session_id": session,
            "kind": "readiness_artifact",
            "content": "Preflight for pilotmain/AethOS#80 documentation change",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["repo_pilot_readiness_dashboard_memory_only"] is True


def test_repo_pilot_readiness_dashboard_chat_intent():
    session = "mc-rprd-chat-182"
    _readiness_stack(session)
    turn = resolve_chat_turn("show pilot readiness", session_id=session)
    assert turn.meta.get("route_id") == REPO_PILOT_READINESS_DASHBOARD_ROUTE_ID
    assert turn.meta.get("pilot_execution_performed") == "false"

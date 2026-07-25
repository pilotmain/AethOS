# SPDX-License-Identifier: Apache-2.0
"""FIX 230 — governed rollback lifecycle tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_store import (
    append_governed_monitoring_lifecycle_record,
    clear_governed_monitoring_lifecycle_records_for_tests,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_contract import (
    AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
    GOVERNED_ROLLBACK_LIFECYCLE_ROUTE_ID,
    ROLLBACK_AUTHORITY_FIX_230,
    ROLLBACK_RECOMMENDATIONS,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_intent import (
    is_governed_rollback_lifecycle_intent,
    parse_governed_rollback_lifecycle_record_intent,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_service import (
    build_governed_rollback_lifecycle,
    prepare_governed_rollback_handoff,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_store import (
    append_governed_rollback_lifecycle_record,
    clear_governed_rollback_lifecycle_records_for_tests,
)
from tests.test_mission_control_governed_monitoring_lifecycle import _seed_monitoring_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_rollback_lifecycle_records_for_tests()
    clear_governed_monitoring_lifecycle_records_for_tests()
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
        clear_governed_deploy_lifecycle_records_for_tests,
    )
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_store import (
        clear_governed_merge_lifecycle_records_for_tests,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        clear_bounded_multi_agent_delivery_execution_records_for_tests,
    )
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
        clear_issue_intent_alignment_records_for_tests,
    )
    from aethos_core.software_delivery.github_pr_open_store import clear_for_tests as clear_pr_open
    from aethos_core.software_delivery.github_pr_preflight_store import clear_for_tests as clear_preflight
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plan
    from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as clear_verify

    clear_governed_deploy_lifecycle_records_for_tests()
    clear_governed_merge_lifecycle_records_for_tests()
    clear_plan()
    clear_verify()
    clear_preflight()
    clear_pr_open()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_governed_rollback_lifecycle_records_for_tests()
    clear_governed_monitoring_lifecycle_records_for_tests()
    clear_governed_deploy_lifecycle_records_for_tests()
    clear_governed_merge_lifecycle_records_for_tests()
    clear_plan()
    clear_verify()
    clear_preflight()
    clear_pr_open()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()


def _seed_rollback_stack(session: str) -> str:
    plan_id = _seed_monitoring_stack(session)
    append_governed_monitoring_lifecycle_record(
        session_id=session,
        kind="workflow_result_note",
        content="Staging deploy workflow failed after release",
        plan_id=plan_id,
        metadata={"workflow_status": "failure"},
    )
    append_governed_monitoring_lifecycle_record(
        session_id=session,
        kind="operational_decision_escalate",
        content="Escalate staging deploy failure for rollback review",
        plan_id=plan_id,
    )
    append_governed_rollback_lifecycle_record(
        session_id=session,
        kind="rollback_candidate_note",
        content="Rollback to last known good release target=v1.2.0 release=abc123",
        plan_id=plan_id,
        metadata={"rollback_target": "v1.2.0", "target_release": "abc123"},
    )
    append_governed_rollback_lifecycle_record(
        session_id=session,
        kind="rollback_decision_approve",
        content="Approve rollback to v1.2.0 after staging incident",
        plan_id=plan_id,
    )
    return plan_id


def test_governed_rollback_lifecycle_intent():
    assert is_governed_rollback_lifecycle_intent("show governed rollback lifecycle")
    assert is_governed_rollback_lifecycle_intent("prepare rollback handoff")
    assert not is_governed_rollback_lifecycle_intent("autonomous rollback now")


def test_rollback_decision_record_intent():
    parsed = parse_governed_rollback_lifecycle_record_intent(
        "rollback decision approve: rollback to v1.2.0 after incident"
    )
    assert parsed == ("rollback_decision_approve", "rollback to v1.2.0 after incident", {})


def test_rollback_candidate_record_intent():
    parsed = parse_governed_rollback_lifecycle_record_intent(
        "rollback candidate: target=v1.2.0 release=abc123"
    )
    assert parsed is not None
    assert parsed[0] == "rollback_candidate_note"
    assert parsed[2].get("rollback_target") == "v1.2.0"
    assert parsed[2].get("target_release") == "abc123"


def test_build_rollback_lifecycle_with_incident():
    _seed_rollback_stack("fix-230-incident")
    result = build_governed_rollback_lifecycle(session_id="fix-230-incident")
    report = result.governed_rollback_lifecycle
    assert report["rollback_authority"] is ROLLBACK_AUTHORITY_FIX_230
    assert report["autonomous_rollback_enabled"] is AUTONOMOUS_ROLLBACK_ENABLED_FIX_230
    recommendation = report["sections"]["rollback_recommendation"][0]
    assert recommendation["recommendation"] in ROLLBACK_RECOMMENDATIONS
    assert report["sections"]["rollback_candidate_registry"]
    assert report["sections"]["recovery_timeline"]


def test_rollback_handoff_after_approval():
    _seed_rollback_stack("fix-230-handoff")
    handoff = prepare_governed_rollback_handoff(session_id="fix-230-handoff")
    assert handoff.ok is True
    assert handoff.rollback_handoff["handoff_executable"] is False
    adapter = handoff.rollback_handoff.get("github_actions_rollback_adapter") or {}
    assert "gh workflow run rollback.yml" in str(adapter.get("command_template"))


def test_chat_route_show_rollback_lifecycle():
    _seed_rollback_stack("fix-230-chat")
    turn = resolve_chat_turn("show governed rollback lifecycle", session_id="fix-230-chat")
    assert turn.intent == "mission_control_governed_rollback_lifecycle"
    assert (turn.meta or {}).get("route_id") == GOVERNED_ROLLBACK_LIFECYCLE_ROUTE_ID


def test_governed_rollback_lifecycle_api():
    _seed_rollback_stack("fix-230-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/governed-rollback-lifecycle",
        params={"session_id": "fix-230-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["rollback_authority"] is False
    assert payload["autonomous_rollback_enabled"] is False
    assert payload["markdown"]

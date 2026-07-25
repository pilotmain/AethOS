# SPDX-License-Identifier: Apache-2.0
"""FIX 210 — governed deploy lifecycle tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_contract import (
    AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
    DEPLOY_AUTHORITY_FIX_210,
    DEPLOY_RECOMMENDATIONS,
    GOVERNED_DEPLOY_LIFECYCLE_ROUTE_ID,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_intent import (
    is_governed_deploy_lifecycle_intent,
    parse_governed_deploy_lifecycle_record_intent,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_service import (
    build_governed_deploy_lifecycle,
    prepare_governed_deploy_handoff,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
    append_governed_deploy_lifecycle_record,
    clear_governed_deploy_lifecycle_records_for_tests,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_store import (
    append_governed_merge_lifecycle_record,
    clear_governed_merge_lifecycle_records_for_tests,
)
from tests.test_mission_control_governed_merge_lifecycle import _seed_merge_lifecycle_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_deploy_lifecycle_records_for_tests()
    clear_governed_merge_lifecycle_records_for_tests()
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

    clear_plan()
    clear_verify()
    clear_preflight()
    clear_pr_open()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_governed_deploy_lifecycle_records_for_tests()
    clear_governed_merge_lifecycle_records_for_tests()
    clear_plan()
    clear_verify()
    clear_preflight()
    clear_pr_open()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()


def _seed_deploy_lifecycle_stack(session: str) -> str:
    plan_id = _seed_merge_lifecycle_stack(session)
    append_governed_merge_lifecycle_record(
        session_id=session,
        kind="merge_decision_approve",
        content="Operator approves merge for deploy path",
        plan_id=plan_id,
    )
    append_governed_deploy_lifecycle_record(
        session_id=session,
        kind="merge_completed_acknowledgment",
        content="Human executed merge via gh pr merge",
        plan_id=plan_id,
    )
    return plan_id


def test_governed_deploy_lifecycle_intent():
    assert is_governed_deploy_lifecycle_intent("show governed deploy lifecycle")
    assert is_governed_deploy_lifecycle_intent("prepare deploy handoff")
    assert not is_governed_deploy_lifecycle_intent("railway deploy now")


def test_deploy_decision_record_intent():
    parsed = parse_governed_deploy_lifecycle_record_intent(
        "deploy decision approve: staging deploy approved environment=staging"
    )
    assert parsed is not None
    assert parsed[0] == "deploy_decision_approve"
    assert parsed[2].get("environment") == "staging"


def test_build_deploy_lifecycle_without_plan():
    result = build_governed_deploy_lifecycle(session_id="fix-210-empty")
    report = result.governed_deploy_lifecycle
    assert report["deploy_authority"] is DEPLOY_AUTHORITY_FIX_210
    assert report["autonomous_deploy_enabled"] is AUTONOMOUS_DEPLOY_ENABLED_FIX_210


def test_build_deploy_lifecycle_with_evidence():
    _seed_deploy_lifecycle_stack("fix-210-stack")
    result = build_governed_deploy_lifecycle(session_id="fix-210-stack")
    sections = result.governed_deploy_lifecycle["sections"]
    readiness = sections["deploy_readiness_assessment"][0]
    recommendation = sections["deploy_recommendation"][0]

    assert readiness["merge_status"]["merge_completed_acknowledged"] is True
    assert recommendation["recommendation"] in DEPLOY_RECOMMENDATIONS
    assert sections["github_actions_deployment_adapter"][0]["provider"] == "github_actions"
    assert sections["deploy_handoff_artifact"] == []


def test_deploy_handoff_after_human_approval():
    _seed_deploy_lifecycle_stack("fix-210-handoff")
    append_governed_deploy_lifecycle_record(
        session_id="fix-210-handoff",
        kind="deploy_decision_approve",
        content="Deploy to staging after merge verification",
        plan_id="plan-fix-210-handoff",
        metadata={"environment": "staging"},
    )
    handoff = prepare_governed_deploy_handoff(session_id="fix-210-handoff")
    assert handoff.ok is True
    assert handoff.deploy_handoff["handoff_executable"] is False
    assert "gh workflow run" in str(
        handoff.deploy_handoff.get("github_actions_deployment_adapter", {}).get("command_template")
    )


def test_chat_route_show_deploy_lifecycle():
    _seed_deploy_lifecycle_stack("fix-210-chat")
    turn = resolve_chat_turn("show governed deploy lifecycle", session_id="fix-210-chat")
    assert turn.intent == "mission_control_governed_deploy_lifecycle"
    assert (turn.meta or {}).get("route_id") == GOVERNED_DEPLOY_LIFECYCLE_ROUTE_ID


def test_governed_deploy_lifecycle_api():
    _seed_deploy_lifecycle_stack("fix-210-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/governed-deploy-lifecycle",
        params={"session_id": "fix-210-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["deploy_authority"] is False
    assert payload["railway_authority"] is False
    assert payload["markdown"]

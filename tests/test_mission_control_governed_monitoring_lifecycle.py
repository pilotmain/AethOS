# SPDX-License-Identifier: Apache-2.0
"""FIX 220 — governed monitoring lifecycle tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
    append_governed_deploy_lifecycle_record,
    clear_governed_deploy_lifecycle_records_for_tests,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_contract import (
    AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
    GOVERNED_MONITORING_LIFECYCLE_ROUTE_ID,
    INCIDENT_CLASSIFICATIONS,
    MONITORING_AUTHORITY_FIX_220,
    MONITORING_RECOMMENDATIONS,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_intent import (
    is_governed_monitoring_lifecycle_intent,
    parse_governed_monitoring_lifecycle_record_intent,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
    build_governed_monitoring_lifecycle,
    prepare_governed_monitoring_escalation,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_store import (
    append_governed_monitoring_lifecycle_record,
    clear_governed_monitoring_lifecycle_records_for_tests,
)
from tests.test_mission_control_governed_deploy_lifecycle import _seed_deploy_lifecycle_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_monitoring_lifecycle_records_for_tests()
    clear_governed_deploy_lifecycle_records_for_tests()
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

    clear_governed_merge_lifecycle_records_for_tests()
    clear_plan()
    clear_verify()
    clear_preflight()
    clear_pr_open()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()
    yield
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


def _seed_monitoring_stack(session: str) -> str:
    plan_id = _seed_deploy_lifecycle_stack(session)
    append_governed_deploy_lifecycle_record(
        session_id=session,
        kind="deploy_decision_approve",
        content="Deploy to staging approved",
        plan_id=plan_id,
        metadata={"environment": "staging"},
    )
    append_governed_deploy_lifecycle_record(
        session_id=session,
        kind="deploy_execution_request_note",
        content="Human dispatched gh workflow run deploy.yml",
        plan_id=plan_id,
        metadata={"workflow_status": "success", "workflow_run_id": "12345"},
    )
    append_governed_monitoring_lifecycle_record(
        session_id=session,
        kind="operator_review_note",
        content="Post-deploy smoke check passed",
        plan_id=plan_id,
    )
    return plan_id


def test_governed_monitoring_lifecycle_intent():
    assert is_governed_monitoring_lifecycle_intent("show governed monitoring lifecycle")
    assert is_governed_monitoring_lifecycle_intent("prepare incident escalation")
    assert not is_governed_monitoring_lifecycle_intent("autonomous remediation now")


def test_operational_decision_record_intent():
    parsed = parse_governed_monitoring_lifecycle_record_intent(
        "operational decision escalate: staging deploy degraded after workflow failure"
    )
    assert parsed == ("operational_decision_escalate", "staging deploy degraded after workflow failure", {})


def test_workflow_result_record_intent():
    parsed = parse_governed_monitoring_lifecycle_record_intent(
        "workflow result: GitHub Actions deploy.yml completed status=success"
    )
    assert parsed is not None
    assert parsed[0] == "workflow_result_note"
    assert parsed[2].get("workflow_status") == "success"


def test_build_monitoring_lifecycle_healthy():
    _seed_monitoring_stack("fix-220-healthy")
    result = build_governed_monitoring_lifecycle(session_id="fix-220-healthy")
    report = result.governed_monitoring_lifecycle
    assert report["monitoring_authority"] is MONITORING_AUTHORITY_FIX_220
    assert report["autonomous_remediation_enabled"] is AUTONOMOUS_REMEDIATION_ENABLED_FIX_220
    incident = report["sections"]["incident_detection"][0]
    assert incident["classification"] == "HEALTHY"
    recommendation = report["sections"]["monitoring_recommendation"][0]
    assert recommendation["recommendation"] in MONITORING_RECOMMENDATIONS
    assert report["sections"]["operational_timeline"]


def test_incident_escalation_after_failure():
    _seed_monitoring_stack("fix-220-incident")
    append_governed_monitoring_lifecycle_record(
        session_id="fix-220-incident",
        kind="workflow_result_note",
        content="Workflow failed on staging deploy",
        plan_id="plan-fix-220-incident",
        metadata={"workflow_status": "failure"},
    )
    append_governed_monitoring_lifecycle_record(
        session_id="fix-220-incident",
        kind="operational_decision_escalate",
        content="Escalate staging deploy failure for human review",
        plan_id="plan-fix-220-incident",
    )
    lifecycle = build_governed_monitoring_lifecycle(session_id="fix-220-incident")
    assert lifecycle.governed_monitoring_lifecycle["incident_classification"] in INCIDENT_CLASSIFICATIONS
    escalation = prepare_governed_monitoring_escalation(session_id="fix-220-incident")
    assert escalation.ok is True
    assert escalation.incident_escalation["escalation_executable"] is False


def test_chat_route_show_monitoring_lifecycle():
    _seed_monitoring_stack("fix-220-chat")
    turn = resolve_chat_turn("show governed monitoring lifecycle", session_id="fix-220-chat")
    assert turn.intent == "mission_control_governed_monitoring_lifecycle"
    assert (turn.meta or {}).get("route_id") == GOVERNED_MONITORING_LIFECYCLE_ROUTE_ID


def test_governed_monitoring_lifecycle_api():
    _seed_monitoring_stack("fix-220-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/governed-monitoring-lifecycle",
        params={"session_id": "fix-220-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["monitoring_authority"] is False
    assert payload["rollback_authority"] is False
    assert payload["markdown"]

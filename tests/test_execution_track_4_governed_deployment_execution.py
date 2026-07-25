# SPDX-License-Identifier: Apache-2.0
"""EXECUTION_TRACK_4 — governed deployment execution tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_intent import (
    handle_governed_code_generation_intent,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_contract import (
    EXECUTION_TRACK_4_ID,
    EXECUTION_TRACK_4_PHASES,
    ROLLBACK_AUTHORITY_FIX_337,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_executor import (
    execute_deployment,
    verify_deployment,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_intent import (
    handle_governed_deployment_execution_intent,
    parse_governed_deployment_execution_intent,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_renderer import (
    render_all_governed_deployment_execution_deliverables,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_service import (
    build_governed_deployment_execution,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    clear_governed_deployment_execution_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_intent import (
    handle_governed_git_delivery_intent,
    parse_governed_git_delivery_intent,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_intent import (
    handle_governed_workspace_creation_intent,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()


def _seed_et1_et2_et3(session_id: str) -> None:
    handle_governed_workspace_creation_intent(
        {
            "action": "record",
            "kind": "workspace_creation_review_note",
            "content": "name=demo-api template=fastapi_service org=org-demo",
            "metadata": {
                "workspace_name": "demo-api",
                "template_id": "fastapi_service",
                "org_id": "org-demo",
            },
        },
        session_id=session_id,
    )
    handle_governed_workspace_creation_intent(
        {
            "action": "record",
            "kind": "workspace_decision_approve",
            "content": "Human approves workspace for deployment chain",
        },
        session_id=session_id,
    )
    handle_governed_code_generation_intent(
        {
            "action": "record",
            "kind": "generation_request_review_note",
            "content": "type=story feature=user-health-check Add health check endpoint",
            "metadata": {
                "type": "story",
                "feature_name": "user-health-check",
                "title": "User Health Check",
            },
        },
        session_id=session_id,
    )
    handle_governed_code_generation_intent(
        {
            "action": "record",
            "kind": "generation_decision_approve",
            "content": "Human approves code generation for deployment chain",
        },
        session_id=session_id,
    )
    for text in (
        "git delivery review: work_item=user-health-check target_branch=main",
        "branch delivery review: Approve delivery branch",
        "commit delivery review: Approve commit assembly",
        "pull request review: Approve PR creation",
        "git delivery decision approve: Human approves git delivery",
    ):
        intent = parse_governed_git_delivery_intent(text)
        assert intent is not None
        handle_governed_git_delivery_intent(intent, session_id=session_id)


def _seed_and_deploy(session_id: str = "et4-test") -> dict:
    _seed_et1_et2_et3(session_id)
    for text in (
        "deployment review: provider=railway environment=staging target=demo-api",
        "deployment readiness review: Provider configured and permissions valid",
        "deployment execution review: Approve staging deployment execution",
    ):
        intent = parse_governed_deployment_execution_intent(text)
        assert intent is not None
        handle_governed_deployment_execution_intent(intent, session_id=session_id)
    intent = parse_governed_deployment_execution_intent(
        "deployment decision approve: Human approves governed Railway staging deployment"
    )
    assert intent is not None
    return handle_governed_deployment_execution_intent(intent, session_id=session_id)


def test_execution_track_phases():
    assert EXECUTION_TRACK_4_ID == "EXECUTION_TRACK_4"
    assert len(EXECUTION_TRACK_4_PHASES) == 9


def test_intent_parsing():
    assert parse_governed_deployment_execution_intent("show deployment dashboard") == {
        "action": "view",
        "focus": "deployment_execution_dashboard",
    }
    parsed = parse_governed_deployment_execution_intent(
        "deployment decision approve: Human approves governed deployment only"
    )
    assert parsed == {
        "action": "record",
        "kind": "deployment_decision_approve",
        "content": "Human approves governed deployment only",
    }


def test_program_phases_and_outputs():
    result = build_governed_deployment_execution(session_id="et4-empty")
    board = result.governed_deployment_execution
    assert board["execution_track_id"] == EXECUTION_TRACK_4_ID
    assert board["rollback_authority"] is False
    assert board["autonomous_deployment_enabled"] is False
    for phase in EXECUTION_TRACK_4_PHASES:
        assert phase in board["sections"]


def test_deployment_execution_and_verification():
    handled = _seed_and_deploy(session_id="et4-deploy")
    deployment = handled["deployment"]
    assert deployment["executed"] is True
    assert deployment["receipt"]["rollback_performed"] is False
    assert deployment["receipt"]["provider"] == "Railway"
    assert deployment["receipt"]["environment"] == "staging"
    assert deployment["receipt"]["deployment_url"]

    verification = verify_deployment(session_id="et4-deploy")
    assert verification["verified"] is True
    assert verification["deployment_succeeded"] is True
    assert verification["rollback_performed"] is False

    blocked = execute_deployment(session_id="et4-deploy")
    assert blocked["executed"] is False


def test_deliverable_renderers():
    _seed_and_deploy(session_id="et4-render")
    result = build_governed_deployment_execution(session_id="et4-render")
    deliverables = render_all_governed_deployment_execution_deliverables(
        result.governed_deployment_execution
    )
    assert set(deliverables) == {
        "DEPLOYMENT_EXECUTION_REPORT.md",
        "DEPLOYMENT_VERIFICATION_REPORT.md",
        "DEPLOYMENT_EVIDENCE_REPORT.md",
    }
    assert "Deployment execution ≠ deployment authority" in deliverables["DEPLOYMENT_EXECUTION_REPORT.md"]
    assert ROLLBACK_AUTHORITY_FIX_337 is False

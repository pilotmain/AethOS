# SPDX-License-Identifier: Apache-2.0
"""EXECUTION_TRACK_3 — governed Git delivery tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_intent import (
    handle_governed_code_generation_intent,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_contract import (
    EXECUTION_TRACK_3_ID,
    EXECUTION_TRACK_3_PHASES,
    MERGE_AUTHORITY_FIX_336,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_executor import (
    execute_git_delivery,
    verify_git_delivery,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_intent import (
    handle_governed_git_delivery_intent,
    parse_governed_git_delivery_intent,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_renderer import (
    render_all_governed_git_delivery_deliverables,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_service import (
    build_governed_git_delivery,
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
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()


def _seed_et1_et2(session_id: str) -> None:
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
            "content": "Human approves workspace for delivery chain",
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
            "content": "Human approves code generation for delivery chain",
        },
        session_id=session_id,
    )


def _seed_and_deliver(session_id: str = "et3-test") -> dict:
    _seed_et1_et2(session_id)
    reviews = (
        ("git delivery review: work_item=user-health-check target_branch=main",),
        ("branch delivery review: Approve delivery branch aethos/user-health-check",),
        ("commit delivery review: Approve commit assembly for user-health-check",),
        ("pull request review: Approve PR creation for governed delivery",),
    )
    for (text,) in reviews:
        intent = parse_governed_git_delivery_intent(text)
        assert intent is not None
        handle_governed_git_delivery_intent(intent, session_id=session_id)
    intent = parse_governed_git_delivery_intent("git delivery decision approve: Human approves governed Git delivery")
    assert intent is not None
    return handle_governed_git_delivery_intent(intent, session_id=session_id)


def test_execution_track_phases():
    assert EXECUTION_TRACK_3_ID == "EXECUTION_TRACK_3"
    assert len(EXECUTION_TRACK_3_PHASES) == 9


def test_intent_parsing():
    assert parse_governed_git_delivery_intent("show git delivery dashboard") == {
        "action": "view",
        "focus": "git_delivery_dashboard",
    }
    assert parse_governed_git_delivery_intent("show delivery verification") == {
        "action": "view",
        "focus": "git_delivery_verification",
    }
    parsed = parse_governed_git_delivery_intent(
        "git delivery decision approve: Human approves governed Git delivery only"
    )
    assert parsed == {
        "action": "record",
        "kind": "git_delivery_decision_approve",
        "content": "Human approves governed Git delivery only",
    }


def test_program_phases_and_outputs():
    result = build_governed_git_delivery(session_id="et3-empty")
    board = result.governed_git_delivery
    assert board["execution_track_id"] == EXECUTION_TRACK_3_ID
    assert board["merge_authority"] is False
    for phase in EXECUTION_TRACK_3_PHASES:
        assert phase in board["sections"]


def test_git_delivery_execution_and_verification():
    handled = _seed_and_deliver(session_id="et3-deliver")
    delivery = handled["delivery"]
    assert delivery["executed"] is True
    assert delivery["receipt"]["merge_performed"] is False
    assert delivery["receipt"]["branch_name"].startswith("aethos/user-health-check/")
    assert delivery["receipt"]["commit_hash"]

    verification = verify_git_delivery(session_id="et3-deliver")
    assert verification["verified"] is True
    assert verification["branch_exists"] is True
    assert verification["commit_exists"] is True
    assert verification["merge_performed"] is False

    blocked = execute_git_delivery(session_id="et3-deliver")
    assert blocked["executed"] is False


def test_deliverable_renderers():
    _seed_and_deliver(session_id="et3-render")
    result = build_governed_git_delivery(session_id="et3-render")
    deliverables = render_all_governed_git_delivery_deliverables(result.governed_git_delivery)
    assert set(deliverables) == {
        "GIT_DELIVERY_REPORT.md",
        "PULL_REQUEST_REPORT.md",
        "GIT_DELIVERY_VERIFICATION_REPORT.md",
    }
    assert "Git delivery ≠ merge authority" in deliverables["GIT_DELIVERY_REPORT.md"]
    assert MERGE_AUTHORITY_FIX_336 is False

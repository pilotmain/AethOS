# SPDX-License-Identifier: Apache-2.0
"""EXECUTION_TRACK_1 — governed workspace creation and repository bootstrap tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_contract import (
    DEPLOYMENT_AUTHORITY_FIX_334,
    EXECUTION_TRACK_1_ID,
    EXECUTION_TRACK_1_PHASES,
    GIT_PUSH_AUTHORITY_FIX_334,
    SUPPORTED_REPOSITORY_TEMPLATES,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_executor import (
    execute_repository_bootstrap,
    verify_workspace_bootstrap,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_intent import (
    handle_governed_workspace_creation_intent,
    parse_governed_workspace_creation_intent,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_renderer import (
    render_all_governed_workspace_creation_deliverables,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_service import (
    build_governed_workspace_creation_repository_bootstrap,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_templates import (
    get_project_template,
    list_project_templates,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()


def _seed_and_bootstrap(session_id: str = "et1-test") -> dict:
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
            "kind": "workspace_bootstrap_review_note",
            "content": "Bootstrap fastapi_service skeleton under governance review",
        },
        session_id=session_id,
    )
    return handle_governed_workspace_creation_intent(
        {
            "action": "record",
            "kind": "workspace_decision_approve",
            "content": "Human approves governed workspace bootstrap for demo-api",
        },
        session_id=session_id,
    )


def test_execution_track_phases_and_templates():
    assert EXECUTION_TRACK_1_ID == "EXECUTION_TRACK_1"
    assert len(EXECUTION_TRACK_1_PHASES) == 6
    assert len(SUPPORTED_REPOSITORY_TEMPLATES) == 5
    assert get_project_template("spring_boot_service") is not None
    assert get_project_template("invalid") is None
    assert len(list_project_templates()) == 5


def test_intent_parsing():
    assert parse_governed_workspace_creation_intent("show workspace dashboard") == {
        "action": "view",
        "focus": "workspace_creation_dashboard",
    }
    assert parse_governed_workspace_creation_intent("show repository bootstrap") == {
        "action": "view",
        "focus": "repository_bootstrap_report",
    }
    parsed = parse_governed_workspace_creation_intent(
        "workspace decision approve: Human approves local repository bootstrap only"
    )
    assert parsed == {
        "action": "record",
        "kind": "workspace_decision_approve",
        "content": "Human approves local repository bootstrap only",
    }


def test_program_phases_and_outputs():
    result = build_governed_workspace_creation_repository_bootstrap(session_id="et1-empty")
    board = result.governed_workspace_creation_repository_bootstrap
    assert board["execution_track_id"] == EXECUTION_TRACK_1_ID
    assert board["deployment_authority"] is False
    assert board["git_push_authority"] is False
    for phase in EXECUTION_TRACK_1_PHASES:
        assert phase in board["sections"]


def test_bootstrap_execution_and_verification():
    handled = _seed_and_bootstrap(session_id="et1-bootstrap")
    bootstrap = handled["bootstrap"]
    assert bootstrap["executed"] is True
    assert bootstrap["receipt"]["git_push_performed"] is False
    assert bootstrap["receipt"]["deployment_performed"] is False

    verification = verify_workspace_bootstrap(session_id="et1-bootstrap")
    assert verification["verified"] is True
    assert verification["governance_metadata_valid"] is True

    blocked = execute_repository_bootstrap(session_id="et1-bootstrap")
    assert blocked["executed"] is False


def test_deliverable_renderers():
    _seed_and_bootstrap(session_id="et1-render")
    result = build_governed_workspace_creation_repository_bootstrap(session_id="et1-render")
    deliverables = render_all_governed_workspace_creation_deliverables(
        result.governed_workspace_creation_repository_bootstrap
    )
    assert set(deliverables) == {
        "WORKSPACE_CREATION_REPORT.md",
        "REPOSITORY_BOOTSTRAP_REPORT.md",
        "WORKSPACE_VERIFICATION_REPORT.md",
    }
    assert "Workspace creation ≠ deployment authority" in deliverables["WORKSPACE_CREATION_REPORT.md"]
    assert DEPLOYMENT_AUTHORITY_FIX_334 is False
    assert GIT_PUSH_AUTHORITY_FIX_334 is False

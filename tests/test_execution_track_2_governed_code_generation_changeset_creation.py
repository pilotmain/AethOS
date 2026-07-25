# SPDX-License-Identifier: Apache-2.0
"""EXECUTION_TRACK_2 — governed code generation and changeset creation tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_contract import (
    EXECUTION_TRACK_2_ID,
    EXECUTION_TRACK_2_PHASES,
    GIT_COMMIT_AUTHORITY_FIX_335,
    GIT_PUSH_AUTHORITY_FIX_335,
    PR_CREATION_AUTHORITY_FIX_335,
    SUPPORTED_GENERATION_STACKS,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_executor import (
    execute_code_generation,
    verify_code_generation,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_generators import (
    build_generation_plan,
    resolve_generation_stack,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_intent import (
    handle_governed_code_generation_intent,
    parse_governed_code_generation_intent,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_renderer import (
    render_all_governed_code_generation_deliverables,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_service import (
    build_governed_code_generation_changeset_creation,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
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
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()


def _seed_workspace(session_id: str) -> None:
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
            "content": "Human approves workspace for code generation",
        },
        session_id=session_id,
    )


def _seed_and_generate(session_id: str = "et2-test") -> dict:
    _seed_workspace(session_id)
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
            "kind": "generate_code_review_note",
            "content": "Generate FastAPI route and tests for user-health-check",
        },
        session_id=session_id,
    )
    return handle_governed_code_generation_intent(
        {
            "action": "record",
            "kind": "generation_decision_approve",
            "content": "Human approves governed code generation for user-health-check",
        },
        session_id=session_id,
    )


def test_execution_track_phases_and_stacks():
    assert EXECUTION_TRACK_2_ID == "EXECUTION_TRACK_2"
    assert len(EXECUTION_TRACK_2_PHASES) == 9
    assert len(SUPPORTED_GENERATION_STACKS) == 5
    assert resolve_generation_stack(template_id="fastapi_service", stack=None) == "python_fastapi"


def test_intent_parsing():
    assert parse_governed_code_generation_intent("show code generation dashboard") == {
        "action": "view",
        "focus": "code_generation_dashboard",
    }
    assert parse_governed_code_generation_intent("show changeset review package") == {
        "action": "view",
        "focus": "changeset_review_package",
    }
    parsed = parse_governed_code_generation_intent(
        "generation decision approve: Human approves local code generation only"
    )
    assert parsed == {
        "action": "record",
        "kind": "generation_decision_approve",
        "content": "Human approves local code generation only",
    }


def test_program_phases_and_outputs():
    result = build_governed_code_generation_changeset_creation(session_id="et2-empty")
    board = result.governed_code_generation_changeset_creation
    assert board["execution_track_id"] == EXECUTION_TRACK_2_ID
    assert board["git_commit_authority"] is False
    assert board["git_push_authority"] is False
    assert board["pr_creation_authority"] is False
    for phase in EXECUTION_TRACK_2_PHASES:
        assert phase in board["sections"]


def test_generation_planning():
    plan = build_generation_plan(
        request={
            "feature_name": "user-health-check",
            "requirement_type": "story",
            "template_id": "fastapi_service",
            "description": "Add health check endpoint",
        }
    )
    assert plan["stack"] == "python_fastapi"
    assert plan["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert any(a["kind"] == "code" for a in plan["artifacts"])
    assert any(a["kind"] == "test" for a in plan["artifacts"])


def test_code_generation_execution_and_verification():
    handled = _seed_and_generate(session_id="et2-generate")
    generation = handled["generation"]
    assert generation["executed"] is True
    assert generation["receipt"]["git_commit_performed"] is False
    assert generation["receipt"]["git_push_performed"] is False
    assert generation["receipt"]["pr_creation_performed"] is False
    assert len(generation["receipt"]["new_files"]) >= 2

    verification = verify_code_generation(session_id="et2-generate")
    assert verification["verified"] is True
    assert verification["compilation_ready"] is True

    blocked = execute_code_generation(session_id="et2-generate")
    assert blocked["executed"] is False


def test_deliverable_renderers():
    _seed_and_generate(session_id="et2-render")
    result = build_governed_code_generation_changeset_creation(session_id="et2-render")
    deliverables = render_all_governed_code_generation_deliverables(
        result.governed_code_generation_changeset_creation
    )
    assert set(deliverables) == {
        "CODE_GENERATION_REPORT.md",
        "CHANGESET_REVIEW_PACKAGE.md",
        "GENERATION_VERIFICATION_REPORT.md",
    }
    assert "Code generation ≠ repository authority" in deliverables["CODE_GENERATION_REPORT.md"]
    assert GIT_COMMIT_AUTHORITY_FIX_335 is False
    assert GIT_PUSH_AUTHORITY_FIX_335 is False
    assert PR_CREATION_AUTHORITY_FIX_335 is False

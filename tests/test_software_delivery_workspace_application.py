# SPDX-License-Identifier: Apache-2.0
"""FIX 125D — governed workspace code application."""

from __future__ import annotations

from pathlib import Path

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_orchestration_receipts import clear_for_tests as clear_branch_receipts
from aethos_core.software_delivery.branch_orchestration_service import create_implementation_branch
from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch_store
from aethos_core.software_delivery.governed_workspace import workspace_file_path
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_service import (
    analyze_github_issue,
    approve_implementation_planning,
    create_implementation_plan,
)
from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plans
from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_APPROVAL_PHRASE
from aethos_core.software_delivery.patch_proposal_receipts import clear_for_tests as clear_patch_receipts
from aethos_core.software_delivery.patch_proposal_service import (
    approve_patch_proposal,
    generate_patch_intent,
    propose_patch_files,
    show_patch_diff_preview,
)
from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch_store
from aethos_core.software_delivery.workspace_application_contract import (
    GIT_COMMIT_ENABLED_FIX_125D,
    REPO_WRITE_ENABLED_FIX_125D,
    WORKSPACE_APPLY_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.workspace_application_receipts import (
    clear_for_tests as clear_ws_receipts,
)
from aethos_core.software_delivery.workspace_application_service import (
    apply_approved_patch_to_workspace,
    is_workspace_application_intent,
)
from aethos_core.software_delivery.workspace_application_store import clear_for_tests as clear_ws_store


@pytest.fixture(autouse=True)
def _clean():
    clear_plans()
    clear_branch_store()
    clear_branch_receipts()
    clear_patch_store()
    clear_patch_receipts()
    clear_ws_store()
    clear_ws_receipts()
    get_settings.cache_clear()
    yield
    clear_plans()
    clear_branch_store()
    clear_branch_receipts()
    clear_patch_store()
    clear_patch_receipts()
    clear_ws_store()
    clear_ws_receipts()
    get_settings.cache_clear()


def test_workspace_intents():
    assert is_workspace_application_intent("apply approved patch to workspace")
    assert is_workspace_application_intent("show governed workspace diff")


def test_safety_constants():
    assert REPO_WRITE_ENABLED_FIX_125D is False
    assert GIT_COMMIT_ENABLED_FIX_125D is False


def _full_stack_to_approved_patch(session: str) -> str:
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#61")
    create_implementation_plan(session_id=session)
    approve_implementation_planning(
        session_id=session,
        user_text=f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}",
    )
    create_implementation_branch(
        session_id=session,
        user_text=f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
    )
    propose_patch_files(session_id=session)
    generate_patch_intent(session_id=session)
    show_patch_diff_preview(session_id=session)
    approve_patch_proposal(
        session_id=session,
        user_text=f"approve patch proposal\n{PATCH_PROPOSAL_APPROVAL_PHRASE}",
    )
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    plan = load_issue_plan_for_session(session_id=session)
    return str(plan.get("plan_id") or "")


def test_workspace_apply_writes_only_under_tree():
    session = "sd-ws-125d"
    plan_id = _full_stack_to_approved_patch(session)

    blocked = apply_approved_patch_to_workspace(session_id=session, user_text="apply approved patch to workspace")
    assert not blocked.ok

    applied = apply_approved_patch_to_workspace(
        session_id=session,
        user_text=f"apply approved patch to workspace\n{WORKSPACE_APPLY_APPROVAL_PHRASE}",
    )
    assert applied.ok
    assert applied.application.get("status") == "applied"

    repo_root = Path(__file__).resolve().parents[1]
    for rel in applied.application.get("files_applied") or []:
        ws_file = workspace_file_path(plan_id=plan_id, rel=rel)
        assert ws_file and ws_file.is_file()
        repo_file = repo_root / rel
        if repo_file.is_file():
            assert ws_file.read_text() != repo_file.read_text()


def test_chat_workspace_apply_meta():
    session = "sd-route-125d"
    _full_stack_to_approved_patch(session)
    result = resolve_chat_turn(
        f"apply approved patch to workspace\n{WORKSPACE_APPLY_APPROVAL_PHRASE}",
        session_id=session,
        apply_relational_layer=False,
    )
    assert result.intent == "software_delivery_workspace_patch_applied"
    assert result.meta.get("workspace_write_performed") == "true"
    assert result.meta.get("repo_mutation_performed") == "false"

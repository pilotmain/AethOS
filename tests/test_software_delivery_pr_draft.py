# SPDX-License-Identifier: Apache-2.0
"""FIX 125F — governed PR draft artifact."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_orchestration_service import create_implementation_branch
from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch_store
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_service import (
    analyze_github_issue,
    approve_implementation_planning,
    create_implementation_plan,
)
from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plans
from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_APPROVAL_PHRASE
from aethos_core.software_delivery.patch_proposal_service import (
    approve_patch_proposal,
    generate_patch_intent,
    propose_patch_files,
    show_patch_diff_preview,
)
from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch_store
from aethos_core.software_delivery.pr_draft_contract import GITHUB_PR_CREATION_ENABLED_FIX_125F
from aethos_core.software_delivery.pr_draft_receipts import clear_for_tests as clear_pr_receipts
from aethos_core.software_delivery.pr_draft_service import (
    create_software_delivery_pr_draft,
    is_pr_draft_intent,
)
from aethos_core.software_delivery.pr_draft_store import clear_for_tests as clear_pr_store
from aethos_core.software_delivery.workspace_application_contract import WORKSPACE_APPLY_APPROVAL_PHRASE
from aethos_core.software_delivery.workspace_application_service import apply_approved_patch_to_workspace
from aethos_core.software_delivery.workspace_application_store import clear_for_tests as clear_ws_store
from aethos_core.software_delivery.workspace_verification_receipts import clear_for_tests as clear_vfy_receipts
from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification
from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as clear_vfy_store

@pytest.fixture(autouse=True)
def _clean():
    clear_plans()
    clear_branch_store()
    clear_patch_store()
    clear_ws_store()
    clear_vfy_store()
    clear_vfy_receipts()
    clear_pr_store()
    clear_pr_receipts()
    get_settings.cache_clear()
    yield
    clear_plans()
    clear_branch_store()
    clear_patch_store()
    clear_ws_store()
    clear_vfy_store()
    clear_vfy_receipts()
    clear_pr_store()
    clear_pr_receipts()
    get_settings.cache_clear()


def test_pr_draft_intents():
    assert is_pr_draft_intent("create software delivery pr draft")
    assert is_pr_draft_intent("show pr draft status")


def test_github_pr_disabled():
    assert GITHUB_PR_CREATION_ENABLED_FIX_125F is False


def _full_stack(session: str) -> None:
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
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
    apply_approved_patch_to_workspace(
        session_id=session,
        user_text=f"apply approved patch to workspace\n{WORKSPACE_APPLY_APPROVAL_PHRASE}",
    )
    run_workspace_verification(session_id=session)


def test_pr_draft_requires_verification():
    session = "sd-pr-125f"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
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
    apply_approved_patch_to_workspace(
        session_id=session,
        user_text=f"apply approved patch to workspace\n{WORKSPACE_APPLY_APPROVAL_PHRASE}",
    )
    blocked = create_software_delivery_pr_draft(session_id=session)
    assert not blocked.ok
    assert any("workspace_verification" in b for b in blocked.blockers)

    run_workspace_verification(session_id=session)
    created = create_software_delivery_pr_draft(session_id=session)
    assert created.ok
    assert created.draft.get("github_pr_created") is False
    assert "Verification summary" in created.draft.get("body", "")
    assert created.draft.get("human_review_requirements")


def test_chat_pr_draft_route():
    session = "sd-route-125f"
    _full_stack(session)
    result = resolve_chat_turn(
        "create software delivery pr draft",
        session_id=session,
        apply_relational_layer=False,
    )
    assert result.intent == "software_delivery_pr_draft_created"
    assert "Human review requirements" in result.reply

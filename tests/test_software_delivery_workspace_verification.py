# SPDX-License-Identifier: Apache-2.0
"""FIX 125E — workspace verification."""

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
from aethos_core.software_delivery.workspace_application_contract import WORKSPACE_APPLY_APPROVAL_PHRASE
from aethos_core.software_delivery.workspace_application_service import apply_approved_patch_to_workspace
from aethos_core.software_delivery.workspace_application_store import clear_for_tests as clear_ws_store
from aethos_core.software_delivery.workspace_verification_contract import (
    ARBITRARY_SHELL_ENABLED_FIX_125E,
    PR_DRAFTING_REQUIRES_VERIFICATION_FIX_125E,
)
from aethos_core.software_delivery.workspace_verification_receipts import clear_for_tests as clear_vfy_receipts
from aethos_core.software_delivery.workspace_verification_service import (
    is_workspace_verification_intent,
    pr_drafting_blocked_for_session,
    run_workspace_verification,
)
from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as clear_vfy_store


@pytest.fixture(autouse=True)
def _clean():
    clear_plans()
    clear_branch_store()
    clear_patch_store()
    clear_ws_store()
    clear_vfy_store()
    clear_vfy_receipts()
    get_settings.cache_clear()
    yield
    clear_plans()
    clear_branch_store()
    clear_patch_store()
    clear_ws_store()
    clear_vfy_store()
    clear_vfy_receipts()
    get_settings.cache_clear()


def test_verification_intents():
    assert is_workspace_verification_intent("run workspace verification")
    assert is_workspace_verification_intent("show workspace verification report")


def test_pr_gate_constants():
    assert PR_DRAFTING_REQUIRES_VERIFICATION_FIX_125E is True
    assert ARBITRARY_SHELL_ENABLED_FIX_125E is False


def _stack_through_apply(session: str) -> None:
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#70")
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


def test_verification_and_pr_gate():
    session = "sd-vfy-125e"
    assert pr_drafting_blocked_for_session(session_id=session)[0] is True

    _stack_through_apply(session)
    blocked_before, _ = pr_drafting_blocked_for_session(session_id=session)
    assert blocked_before is True

    verified = run_workspace_verification(session_id=session)
    assert verified.ok
    assert verified.verification.get("pr_drafting_unblocked") is True

    blocked_after, _ = pr_drafting_blocked_for_session(session_id=session)
    assert blocked_after is False


def test_chat_verification_route():
    session = "sd-route-125e"
    _stack_through_apply(session)
    result = resolve_chat_turn(
        "run workspace verification",
        session_id=session,
        apply_relational_layer=False,
    )
    assert result.intent == "software_delivery_workspace_verification_passed"
    assert "pr_drafting_unblocked" in result.reply

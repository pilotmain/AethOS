# SPDX-License-Identifier: Apache-2.0
"""FIX 125C — governed patch proposal."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_orchestration_receipts import clear_for_tests as clear_branch_receipts
from aethos_core.software_delivery.branch_orchestration_service import create_implementation_branch
from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch_store
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_service import (
    analyze_github_issue,
    approve_implementation_planning,
    create_implementation_plan,
)
from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plans
from aethos_core.software_delivery.patch_proposal_contract import (
    DEPLOY_ENABLED_FIX_125C,
    FILE_WRITE_ENABLED_FIX_125C,
    PATCH_PROPOSAL_APPROVAL_PHRASE,
    PR_CREATION_ENABLED_FIX_125C,
)
from aethos_core.software_delivery.patch_proposal_receipts import clear_for_tests as clear_patch_receipts
from aethos_core.software_delivery.patch_proposal_service import (
    approve_patch_proposal,
    generate_patch_intent,
    is_patch_proposal_intent,
    propose_patch_files,
    show_patch_diff_preview,
)
from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch_store


@pytest.fixture(autouse=True)
def _clean():
    clear_plans()
    clear_branch_store()
    clear_branch_receipts()
    clear_patch_store()
    clear_patch_receipts()
    get_settings.cache_clear()
    yield
    clear_plans()
    clear_branch_store()
    clear_branch_receipts()
    clear_patch_store()
    clear_patch_receipts()
    get_settings.cache_clear()


def test_patch_intents():
    assert is_patch_proposal_intent("propose patch files")
    assert is_patch_proposal_intent("propose files to change")
    assert is_patch_proposal_intent("generate patch intent")
    assert is_patch_proposal_intent("show patch diff preview")


def test_safety_constants():
    assert FILE_WRITE_ENABLED_FIX_125C is False
    assert PR_CREATION_ENABLED_FIX_125C is False
    assert DEPLOY_ENABLED_FIX_125C is False


def _setup_plan_and_branch(session: str) -> None:
    analyze_github_issue(
        session_id=session,
        user_text="analyze github issue pilotmain/AethOS#60",
    )
    create_implementation_plan(session_id=session)
    approve_implementation_planning(
        session_id=session,
        user_text=f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}",
    )
    create_implementation_branch(
        session_id=session,
        user_text=f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
    )


def test_patch_proposal_flow():
    session = "sd-patch-125c"
    _setup_plan_and_branch(session)

    proposed = propose_patch_files(session_id=session)
    assert proposed.ok
    assert proposed.proposal.get("proposed_files")

    intent = generate_patch_intent(session_id=session)
    assert intent.ok
    assert intent.proposal.get("patch_intent")

    preview = show_patch_diff_preview(session_id=session)
    assert preview.ok
    assert preview.proposal.get("unified_diffs")

    blocked = approve_patch_proposal(session_id=session, user_text="approve patch proposal")
    assert not blocked.ok

    approved = approve_patch_proposal(
        session_id=session,
        user_text=f"approve patch proposal\n{PATCH_PROPOSAL_APPROVAL_PHRASE}",
    )
    assert approved.ok
    assert approved.proposal.get("patch_proposal_approved") is True
    assert approved.proposal.get("file_write_enabled") is False


def test_chat_routes_patch_commands():
    session = "sd-route-125c"
    _setup_plan_and_branch(session)

    propose = resolve_chat_turn("propose patch files", session_id=session, apply_relational_layer=False)
    assert propose.intent == "software_delivery_patch_files_proposed"

    intent = resolve_chat_turn("generate patch intent", session_id=session, apply_relational_layer=False)
    assert intent.intent == "software_delivery_patch_intent_generated"

    diff = resolve_chat_turn("show patch diff preview", session_id=session, apply_relational_layer=False)
    assert diff.intent == "software_delivery_patch_diff_preview"
    assert "```diff" in diff.reply

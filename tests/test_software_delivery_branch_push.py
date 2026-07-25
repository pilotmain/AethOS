# SPDX-License-Identifier: Apache-2.0
"""FIX 125H — governed GitHub branch push."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_APPROVAL_PHRASE,
    GITHUB_PR_CREATE_ENABLED_FIX_125H,
    MERGE_ENABLED_FIX_125H,
    MUTATION_PREVIEW_ACK_PHRASE,
)
from aethos_core.software_delivery.branch_push_receipts import clear_for_tests as clear_bp_receipts
from aethos_core.software_delivery.branch_push_service import (
    is_branch_push_intent,
    push_governed_branch_to_github,
)
from aethos_core.software_delivery.branch_push_store import (
    branch_push_completed_for_plan,
    clear_for_tests as clear_bp_store,
)
from aethos_core.software_delivery.github_pr_preflight_contract import GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_preflight_service import (
    approve_github_pr_creation_preflight,
    run_github_pr_creation_preflight,
)
from aethos_core.software_delivery.github_pr_preflight_store import clear_for_tests as clear_pf_store
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.pr_draft_service import create_software_delivery_pr_draft
from tests.test_software_delivery_pr_draft import _full_stack


def _push_user_text() -> str:
    return (
        "push governed branch to github\n"
        f"{BRANCH_PUSH_APPROVAL_PHRASE}\n"
        f"{MUTATION_PREVIEW_ACK_PHRASE}"
    )


def _through_preflight_approved(session: str) -> str:
    _full_stack(session)
    from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification

    run_workspace_verification(session_id=session)
    create_software_delivery_pr_draft(session_id=session)
    preflight = run_github_pr_creation_preflight(session_id=session)
    assert preflight.ok
    approved = approve_github_pr_creation_preflight(
        session_id=session,
        user_text=f"approve github pr creation preflight\n{GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
    )
    assert approved.ok
    plan = load_issue_plan_for_session(session_id=session)
    return str(plan.get("plan_id") or "")


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as cb
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as cp
    from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as cpa
    from aethos_core.software_delivery.pr_draft_store import clear_for_tests as cpr
    from aethos_core.software_delivery.workspace_application_store import clear_for_tests as cw
    from aethos_core.software_delivery.workspace_verification_receipts import clear_for_tests as cvr
    from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as cv

    cp()
    cb()
    cpa()
    cw()
    cv()
    cvr()
    cpr()
    clear_pf_store()
    clear_bp_store()
    clear_bp_receipts()
    get_settings.cache_clear()
    yield
    cp()
    cb()
    cpa()
    cw()
    cv()
    cvr()
    cpr()
    clear_pf_store()
    clear_bp_store()
    clear_bp_receipts()
    get_settings.cache_clear()


def test_branch_push_intents():
    assert is_branch_push_intent("push governed branch to github")
    assert is_branch_push_intent("show governed branch push report")


def test_no_pr_merge_constants():
    assert GITHUB_PR_CREATE_ENABLED_FIX_125H is False
    assert MERGE_ENABLED_FIX_125H is False


def test_push_blocked_without_phrases():
    session = "sd-bp-block-125h"
    _through_preflight_approved(session)
    result = push_governed_branch_to_github(session_id=session, user_text="push governed branch to github")
    assert not result.ok
    assert "branch_push_approval_required" in result.blockers


def test_push_flow_and_idempotency():
    session = "sd-bp-flow-125h"
    plan_id = _through_preflight_approved(session)
    result = push_governed_branch_to_github(session_id=session, user_text=_push_user_text())
    assert result.ok
    assert result.push.get("status") == "pushed"
    assert result.push.get("github_pr_created") is False
    assert branch_push_completed_for_plan(plan_id=plan_id)

    replay = push_governed_branch_to_github(session_id=session, user_text=_push_user_text())
    assert replay.ok
    assert "idempotent" in (replay.detail or "").lower()


def test_chat_branch_push_route():
    session = "sd-route-125h"
    _through_preflight_approved(session)
    result = resolve_chat_turn(_push_user_text(), session_id=session, apply_relational_layer=False)
    assert result.intent == "software_delivery_github_branch_pushed"
    assert result.meta.get("github_mutation_performed") == "true"
    assert result.meta.get("github_pr_create_performed") == "false"

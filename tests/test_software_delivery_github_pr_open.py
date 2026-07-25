# SPDX-License-Identifier: Apache-2.0
"""FIX 125I — governed GitHub PR open."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_APPROVAL_PHRASE,
    MUTATION_PREVIEW_ACK_PHRASE,
)
from aethos_core.software_delivery.branch_push_service import push_governed_branch_to_github
from aethos_core.software_delivery.branch_push_store import clear_for_tests as clear_bp_store
from aethos_core.software_delivery.github_pr_open_contract import (
    GITHUB_PR_OPEN_APPROVAL_PHRASE,
    MERGE_ENABLED_FIX_125I,
)
from aethos_core.software_delivery.github_pr_open_receipts import clear_for_tests as clear_po_receipts
from aethos_core.software_delivery.github_pr_open_service import (
    is_github_pr_open_intent,
    open_governed_github_pull_request,
)
from aethos_core.software_delivery.github_pr_open_store import (
    clear_for_tests as clear_po_store,
    github_pr_open_completed_for_plan,
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


def _push_text() -> str:
    return (
        "push governed branch to github\n"
        f"{BRANCH_PUSH_APPROVAL_PHRASE}\n"
        f"{MUTATION_PREVIEW_ACK_PHRASE}"
    )


def _open_text() -> str:
    return f"open governed github pull request\n{GITHUB_PR_OPEN_APPROVAL_PHRASE}"


def _through_branch_pushed(session: str) -> str:
    _full_stack(session)
    from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification

    run_workspace_verification(session_id=session)
    create_software_delivery_pr_draft(session_id=session)
    preflight = run_github_pr_creation_preflight(session_id=session)
    assert preflight.ok
    approve_github_pr_creation_preflight(
        session_id=session,
        user_text=f"approve github pr creation preflight\n{GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
    )
    pushed = push_governed_branch_to_github(session_id=session, user_text=_push_text())
    assert pushed.ok
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
    clear_po_store()
    clear_po_receipts()
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
    clear_po_store()
    clear_po_receipts()
    get_settings.cache_clear()


def test_pr_open_intents():
    assert is_github_pr_open_intent("open governed github pull request")
    assert is_github_pr_open_intent("show governed github pr report")


def test_no_merge_constant():
    assert MERGE_ENABLED_FIX_125I is False


def test_open_blocked_without_phrase():
    session = "sd-pro-block-125i"
    _through_branch_pushed(session)
    result = open_governed_github_pull_request(
        session_id=session,
        user_text="open governed github pull request",
    )
    assert not result.ok
    assert "github_pr_open_approval_required" in result.blockers


def test_open_blocked_without_push():
    session = "sd-pro-nopush-125i"
    _full_stack(session)
    from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification

    run_workspace_verification(session_id=session)
    create_software_delivery_pr_draft(session_id=session)
    run_github_pr_creation_preflight(session_id=session)
    approve_github_pr_creation_preflight(
        session_id=session,
        user_text=f"approve github pr creation preflight\n{GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
    )
    result = open_governed_github_pull_request(session_id=session, user_text=_open_text())
    assert not result.ok
    assert "branch_push_not_completed" in result.blockers or "branch_push_missing" in result.blockers


def test_open_flow_and_idempotency():
    session = "sd-pro-flow-125i"
    plan_id = _through_branch_pushed(session)
    result = open_governed_github_pull_request(session_id=session, user_text=_open_text())
    assert result.ok
    assert result.record.get("status") == "opened"
    assert result.record.get("pr_url")
    assert result.record.get("human_review_required") is True
    assert github_pr_open_completed_for_plan(plan_id=plan_id)

    replay = open_governed_github_pull_request(session_id=session, user_text=_open_text())
    assert replay.ok
    assert "idempotent" in (replay.detail or "").lower()


def test_chat_pr_open_route():
    session = "sd-route-125i"
    _through_branch_pushed(session)
    result = resolve_chat_turn(_open_text(), session_id=session, apply_relational_layer=False)
    assert result.intent == "software_delivery_github_pr_opened"
    assert result.meta.get("github_pr_create_performed") == "true"
    assert result.meta.get("merge_performed") == "false"
    assert result.meta.get("human_review_required") == "true"

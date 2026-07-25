# SPDX-License-Identifier: Apache-2.0
"""FIX 125G — GitHub PR creation preflight."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.github_pr_preflight_contract import (
    GITHUB_PR_CREATE_ENABLED_FIX_125G,
    GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
    GIT_PUSH_ENABLED_FIX_125G,
)
from aethos_core.software_delivery.github_pr_preflight_receipts import clear_for_tests as clear_pf_receipts
from aethos_core.software_delivery.github_pr_preflight_service import (
    approve_github_pr_creation_preflight,
    github_pr_creation_blocked_for_session,
    is_github_pr_preflight_intent,
    run_github_pr_creation_preflight,
)
from aethos_core.software_delivery.github_pr_preflight_store import clear_for_tests as clear_pf_store
from aethos_core.software_delivery.pr_draft_service import create_software_delivery_pr_draft
from tests.test_software_delivery_pr_draft import _full_stack as _stack_to_verify  # noqa: PLC2701


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
    clear_pf_receipts()
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
    clear_pf_receipts()
    get_settings.cache_clear()


def test_preflight_intents():
    assert is_github_pr_preflight_intent("run github pr creation preflight")
    assert is_github_pr_preflight_intent("approve github pr creation preflight")


def test_no_github_mutation_constants():
    assert GIT_PUSH_ENABLED_FIX_125G is False
    assert GITHUB_PR_CREATE_ENABLED_FIX_125G is False


def test_preflight_flow():
    session = "sd-gpf-125g"
    assert github_pr_creation_blocked_for_session(session_id=session)[0] is True

    _stack_to_verify(session)
    from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification

    run_workspace_verification(session_id=session)
    create_software_delivery_pr_draft(session_id=session)

    preflight = run_github_pr_creation_preflight(session_id=session)
    assert preflight.ok
    assert preflight.preflight.get("idempotency_key")
    assert preflight.preflight.get("mutation_preview")

    assert github_pr_creation_blocked_for_session(session_id=session)[0] is True

    approved = approve_github_pr_creation_preflight(
        session_id=session,
        user_text=f"approve github pr creation preflight\n{GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
    )
    assert approved.ok
    assert github_pr_creation_blocked_for_session(session_id=session)[0] is False


def test_chat_preflight_route():
    session = "sd-route-125g"
    _stack_to_verify(session)
    from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification

    run_workspace_verification(session_id=session)
    create_software_delivery_pr_draft(session_id=session)
    result = resolve_chat_turn(
        "run github pr creation preflight",
        session_id=session,
        apply_relational_layer=False,
    )
    assert result.intent == "software_delivery_github_pr_preflight_passed"
    assert "idempotency_key" in result.reply

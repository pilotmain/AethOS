# SPDX-License-Identifier: Apache-2.0
"""FIX 125B — governed branch orchestration."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_orchestration_contract import (
    BRANCH_ARCHIVE_APPROVAL_PHRASE,
    BRANCH_CREATE_APPROVAL_PHRASE,
    BRANCH_RESTORE_APPROVAL_PHRASE,
    CODE_MODIFICATION_ENABLED_FIX_125B,
    MERGE_ENABLED_FIX_125B,
    PR_CREATION_ENABLED_FIX_125B,
)
from aethos_core.software_delivery.branch_orchestration_receipts import clear_for_tests as clear_receipts
from aethos_core.software_delivery.branch_orchestration_service import (
    archive_implementation_branch,
    create_implementation_branch,
    is_branch_orchestration_intent,
    restore_implementation_branch,
)
from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch_store
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_service import (
    analyze_github_issue,
    approve_implementation_planning,
    create_implementation_plan,
)
from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plans


@pytest.fixture(autouse=True)
def _clean():
    clear_plans()
    clear_branch_store()
    clear_receipts()
    get_settings.cache_clear()
    yield
    clear_plans()
    clear_branch_store()
    clear_receipts()
    get_settings.cache_clear()


def test_branch_intents():
    assert is_branch_orchestration_intent("create implementation branch")
    assert is_branch_orchestration_intent("show implementation branch status")
    assert is_branch_orchestration_intent("show software delivery timeline")


def test_branch_safety_constants():
    assert CODE_MODIFICATION_ENABLED_FIX_125B is False
    assert PR_CREATION_ENABLED_FIX_125B is False
    assert MERGE_ENABLED_FIX_125B is False


def _approve_plan(session: str) -> None:
    analyze_github_issue(
        session_id=session,
        user_text="analyze github issue pilotmain/AethOS#55",
    )
    create_implementation_plan(session_id=session)
    approve_implementation_planning(
        session_id=session,
        user_text=f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}",
    )


def test_branch_lifecycle_requires_approval_and_receipts():
    session = "sd-branch-125b"
    _approve_plan(session)

    blocked = create_implementation_branch(session_id=session, user_text="create implementation branch")
    assert not blocked.ok
    assert "branch_create_approval_required" in blocked.blockers

    created = create_implementation_branch(
        session_id=session,
        user_text=f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
    )
    assert created.ok
    assert created.branch_context["lifecycle_state"] == "active"
    assert created.branch_context.get("code_modification_enabled") is False

    again = create_implementation_branch(
        session_id=session,
        user_text=f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
    )
    assert again.ok
    assert again.detail.startswith("Implementation branch already active")

    archived = archive_implementation_branch(
        session_id=session,
        user_text=f"archive implementation branch\n{BRANCH_ARCHIVE_APPROVAL_PHRASE}",
    )
    assert archived.ok
    assert archived.branch_context["lifecycle_state"] == "archived"

    restored = restore_implementation_branch(
        session_id=session,
        user_text=f"restore implementation branch\n{BRANCH_RESTORE_APPROVAL_PHRASE}",
    )
    assert restored.ok
    assert restored.branch_context["lifecycle_state"] == "restored"


def test_chat_routes_branch_commands():
    session = "sd-route-125b"
    _approve_plan(session)

    result = resolve_chat_turn(
        f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
        session_id=session,
        apply_relational_layer=False,
    )
    assert result.meta.get("route_id") == "software_delivery_issue_plan"
    assert result.meta.get("lane_separation") == "software_delivery_not_infra"
    assert result.intent == "software_delivery_branch_created"
    assert "aethos/sd-" in result.reply

    timeline = resolve_chat_turn(
        "show software delivery timeline",
        session_id=session,
        apply_relational_layer=False,
    )
    assert timeline.intent == "software_delivery_timeline"
    assert "Branch receipts" in timeline.reply

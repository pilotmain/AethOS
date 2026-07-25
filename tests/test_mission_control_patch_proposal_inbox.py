# SPDX-License-Identifier: Apache-2.0
"""Patch proposal inbox gating — do not offer approval before diff preview."""

from __future__ import annotations

from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_orchestration_service import create_implementation_branch
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_service import (
    analyze_github_issue,
    approve_implementation_planning,
    create_implementation_plan,
)
from aethos_core.software_delivery.patch_proposal_service import (
    generate_patch_intent,
    propose_patch_files,
    show_patch_diff_preview,
)


def _setup_plan_branch_proposal(session: str) -> None:
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#60")
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


def test_patch_approval_hidden_until_diff_preview():
    session = "mc-patch-gate-prep"
    _setup_plan_branch_proposal(session)
    inbox = build_approval_inbox(session_id=session)
    assert inbox.ok
    assert not any(i.get("gate_id") == "patch_proposal_approved" for i in inbox.items)
    prereq = [i for i in inbox.items if i.get("gate_id") == "patch_proposal_prerequisites"]
    assert len(prereq) == 1
    assert prereq[0].get("ui_approval_eligible") is False
    assert prereq[0].get("execution_mode") == "prerequisites_required"


def test_patch_approval_shown_after_diff_preview():
    session = "mc-patch-gate-ready"
    _setup_plan_branch_proposal(session)
    generate_patch_intent(session_id=session)
    show_patch_diff_preview(session_id=session)
    inbox = build_approval_inbox(session_id=session)
    approved_gates = [i for i in inbox.items if i.get("gate_id") == "patch_proposal_approved"]
    assert len(approved_gates) == 1
    assert approved_gates[0].get("ui_approval_eligible") is True
    assert not any(i.get("gate_id") == "patch_proposal_prerequisites" for i in inbox.items)

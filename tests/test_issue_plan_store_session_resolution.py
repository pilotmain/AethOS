# SPDX-License-Identifier: Apache-2.0
"""Issue plan store — multi-plan session resolution."""

from __future__ import annotations

import pytest

from aethos_core.software_delivery.github_pr_open_store import save_github_pr_open
from aethos_core.software_delivery.issue_plan_store import (
    clear_for_tests,
    load_issue_plan_for_session,
    save_issue_plan,
)


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch
    from aethos_core.software_delivery.branch_push_store import clear_for_tests as clear_push
    from aethos_core.software_delivery.github_pr_open_receipts import clear_for_tests as clear_receipts
    from aethos_core.software_delivery.github_pr_open_store import clear_for_tests as clear_pr

    from aethos_core.software_delivery.pr_draft_store import clear_for_tests as clear_drafts

    clear_for_tests()
    clear_branch()
    clear_push()
    clear_pr()
    clear_receipts()
    clear_drafts()
    yield
    clear_for_tests()
    clear_branch()
    clear_push()
    clear_pr()
    clear_receipts()
    clear_drafts()


def test_load_issue_plan_for_session_prefers_furthest_delivery_progress():
    save_issue_plan(
        {
            "plan_id": "sdplan-stale-operator",
            "session_id": "recover-test-session",
            "repository": "pilotmain/AethOS",
            "status": "planning_approved",
            "updated_at": "2026-06-02T22:00:00+00:00",
        }
    )
    save_issue_plan(
        {
            "plan_id": "sdplan-dogfood-complete",
            "session_id": "recover-test-session",
            "repository": "pilotmain/AethOS",
            "status": "planning_approved",
            "updated_at": "2026-06-02T21:00:00+00:00",
        }
    )
    save_github_pr_open(
        {
            "pr_open_id": "sdgpro-test-complete",
            "plan_id": "sdplan-dogfood-complete",
            "session_id": "recover-test-session",
            "status": "opened",
            "repository": "pilotmain/AethOS",
        }
    )

    plan = load_issue_plan_for_session(session_id="recover-test-session")
    assert plan is not None
    assert plan.get("plan_id") == "sdplan-dogfood-complete"


def test_restore_issue_plan_from_pr_draft_when_plan_file_missing():
    from aethos_core.software_delivery.pr_draft_store import save_pr_draft

    save_pr_draft(
        {
            "draft_id": "sdpr-recover-operator",
            "plan_id": "sdplan-recover-operator",
            "session_id": "recover-test-session",
            "status": "drafted",
            "title": "[AethOS SD] Dogfood Pilot",
            "body": "https://github.com/pilotmain/AethOS/issues/1\n\n`aethos/sd-recover`",
            "branch_name": "aethos/sd-recover",
        }
    )
    plan = load_issue_plan_for_session(session_id="recover-test-session")
    assert plan is not None
    assert plan.get("plan_id") == "sdplan-recover-operator"
    assert plan.get("reconstructed_from_artifacts") is True


def test_reconstruct_issue_plan_from_branch_context_when_plan_file_missing():
    from aethos_core.software_delivery.branch_orchestration_store import save_branch_context

    save_branch_context(
        {
            "branch_context_id": "sdbctx-recover-operator",
            "plan_id": "sdplan-recover-operator",
            "session_id": "recover-test-session",
            "repository": "pilotmain/AethOS",
            "issue_number": 1,
            "branch_name": "aethos/sd-recover",
        }
    )
    plan = load_issue_plan_for_session(session_id="recover-test-session")
    assert plan is not None
    assert plan.get("plan_id") == "sdplan-recover-operator"
    assert plan.get("reconstructed_from_artifacts") is True


def test_github_pr_open_completed_from_receipts_when_store_missing():
    from aethos_core.software_delivery.github_pr_open_receipts import record_github_pr_open_receipt
    from aethos_core.software_delivery.github_pr_open_store import github_pr_open_completed_for_plan

    record_github_pr_open_receipt(
        plan_id="sdplan-receipt-only",
        phase="pull_request_opened",
        status="pr_open_success",
        detail="PR #8",
        pr_url="https://github.com/pilotmain/AethOS/pull/8",
    )
    assert github_pr_open_completed_for_plan(plan_id="sdplan-receipt-only") is True

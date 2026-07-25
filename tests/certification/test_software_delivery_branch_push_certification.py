# SPDX-License-Identifier: Apache-2.0
"""FIX 125H — governed branch push certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_APPROVAL_PHRASE,
    MUTATION_PREVIEW_ACK_PHRASE,
)
from aethos_core.software_delivery.branch_push_receipts import clear_for_tests as clear_bp_receipts
from aethos_core.software_delivery.branch_push_store import clear_for_tests as clear_bp_store
from aethos_core.software_delivery.github_pr_preflight_contract import GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_preflight_store import clear_for_tests as clear_pf_store
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "software-delivery-cert-125h"


def _push_text() -> str:
    return (
        "push governed branch to github\n"
        f"{BRANCH_PUSH_APPROVAL_PHRASE}\n"
        f"{MUTATION_PREVIEW_ACK_PHRASE}"
    )


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as cb
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests
    from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as cpa
    from aethos_core.software_delivery.pr_draft_store import clear_for_tests as cpr
    from aethos_core.software_delivery.workspace_application_store import clear_for_tests as cw
    from aethos_core.software_delivery.workspace_verification_receipts import clear_for_tests as cvr
    from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as cv

    reset_certification_runtime()
    clear_for_tests()
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
    clear_for_tests()
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
    reset_certification_runtime()


class TestSoftwareDeliveryBranchPushCertification:
    def test_github_branch_push_lane(self) -> None:
        _full_stack(SESSION)
        from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification

        run_workspace_verification(session_id=SESSION)
        resolve_chat_turn("create software delivery pr draft", session_id=SESSION, apply_relational_layer=False)
        resolve_chat_turn("run github pr creation preflight", session_id=SESSION, apply_relational_layer=False)
        resolve_chat_turn(
            f"approve github pr creation preflight\n{GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )

        pushed = resolve_chat_turn(_push_text(), session_id=SESSION, apply_relational_layer=False)
        assert_route_owns(pushed, route_id="software_delivery_issue_plan")
        assert pushed.intent == "software_delivery_github_branch_pushed"
        assert pushed.meta.get("mutation_scope") == "feature_branch_push_only"
        assert "125I" in pushed.reply

        timeline = resolve_chat_turn(
            "show software delivery timeline",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert "Branch push receipts" in timeline.reply

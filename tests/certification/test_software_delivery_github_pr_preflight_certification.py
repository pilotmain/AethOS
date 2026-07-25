# SPDX-License-Identifier: Apache-2.0
"""FIX 125G — GitHub PR preflight certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.github_pr_preflight_contract import GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_preflight_receipts import clear_for_tests as clear_pf_receipts
from aethos_core.software_delivery.github_pr_preflight_store import clear_for_tests as clear_pf_store
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "software-delivery-cert-125g"


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
    clear_pf_receipts()
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
    clear_pf_receipts()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestSoftwareDeliveryGithubPrPreflightCertification:
    def test_github_pr_preflight_lane(self) -> None:
        _full_stack(SESSION)
        from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification

        run_workspace_verification(session_id=SESSION)
        resolve_chat_turn("create software delivery pr draft", session_id=SESSION, apply_relational_layer=False)

        preflight = resolve_chat_turn(
            "run github pr creation preflight",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(preflight, route_id="software_delivery_issue_plan")
        assert preflight.intent == "software_delivery_github_pr_preflight_passed"
        assert "Mutation preview" in preflight.reply

        approved = resolve_chat_turn(
            f"approve github pr creation preflight\n{GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert approved.intent == "software_delivery_github_pr_preflight_approved"

        timeline = resolve_chat_turn(
            "show software delivery timeline",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert "GitHub preflight receipts" in timeline.reply

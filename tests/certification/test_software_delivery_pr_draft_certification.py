# SPDX-License-Identifier: Apache-2.0
"""FIX 125F — PR draft certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch_store
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_store import clear_for_tests
from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_APPROVAL_PHRASE
from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch_store
from aethos_core.software_delivery.pr_draft_receipts import clear_for_tests as clear_pr_receipts
from aethos_core.software_delivery.pr_draft_store import clear_for_tests as clear_pr_store
from aethos_core.software_delivery.workspace_application_contract import WORKSPACE_APPLY_APPROVAL_PHRASE
from aethos_core.software_delivery.workspace_application_store import clear_for_tests as clear_ws_store
from aethos_core.software_delivery.workspace_verification_receipts import clear_for_tests as clear_vfy_receipts
from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as clear_vfy_store
from tests.certification.helpers import assert_route_owns, reset_certification_runtime

pytestmark = pytest.mark.certification

SESSION = "software-delivery-cert-125f"


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_for_tests()
    clear_branch_store()
    clear_patch_store()
    clear_ws_store()
    clear_vfy_store()
    clear_vfy_receipts()
    clear_pr_store()
    clear_pr_receipts()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_branch_store()
    clear_patch_store()
    clear_ws_store()
    clear_vfy_store()
    clear_vfy_receipts()
    clear_pr_store()
    clear_pr_receipts()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestSoftwareDeliveryPrDraftCertification:
    def test_governed_pr_draft_lane(self) -> None:
        resolve_chat_turn(
            "analyze github issue pilotmain/AethOS#106",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        resolve_chat_turn("create implementation plan", session_id=SESSION, apply_relational_layer=False)
        resolve_chat_turn(
            f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        resolve_chat_turn(
            f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        resolve_chat_turn("propose patch files", session_id=SESSION, apply_relational_layer=False)
        resolve_chat_turn("generate patch intent", session_id=SESSION, apply_relational_layer=False)
        resolve_chat_turn("show patch diff preview", session_id=SESSION, apply_relational_layer=False)
        resolve_chat_turn(
            f"approve patch proposal\n{PATCH_PROPOSAL_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        resolve_chat_turn(
            f"apply approved patch to workspace\n{WORKSPACE_APPLY_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        resolve_chat_turn("run workspace verification", session_id=SESSION, apply_relational_layer=False)

        draft = resolve_chat_turn(
            "create software delivery pr draft",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(draft, route_id="software_delivery_issue_plan")
        assert draft.intent == "software_delivery_pr_draft_created"
        assert "Human review requirements" in draft.reply
        assert "github_pr_creation" in draft.reply

        timeline = resolve_chat_turn(
            "show software delivery timeline",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert "PR draft receipts" in timeline.reply

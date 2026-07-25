# SPDX-License-Identifier: Apache-2.0
"""FIX 125C — software delivery patch proposal certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_orchestration_receipts import clear_for_tests as clear_branch_receipts
from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch_store
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_store import clear_for_tests
from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_APPROVAL_PHRASE
from aethos_core.software_delivery.patch_proposal_receipts import clear_for_tests as clear_patch_receipts
from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch_store
from tests.certification.helpers import assert_route_owns, reset_certification_runtime

pytestmark = pytest.mark.certification

SESSION = "software-delivery-cert-125c"


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_for_tests()
    clear_branch_store()
    clear_branch_receipts()
    clear_patch_store()
    clear_patch_receipts()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_branch_store()
    clear_branch_receipts()
    clear_patch_store()
    clear_patch_receipts()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestSoftwareDeliveryPatchProposalCertification:
    def test_governed_patch_proposal_lane(self) -> None:
        analyze = resolve_chat_turn(
            "analyze github issue pilotmain/AethOS#103",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(analyze, route_id="software_delivery_issue_plan")

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

        propose = resolve_chat_turn("propose patch files", session_id=SESSION, apply_relational_layer=False)
        assert_route_owns(propose, route_id="software_delivery_issue_plan")
        assert propose.intent == "software_delivery_patch_files_proposed"

        intent = resolve_chat_turn("generate patch intent", session_id=SESSION, apply_relational_layer=False)
        assert intent.intent == "software_delivery_patch_intent_generated"

        preview = resolve_chat_turn("show patch diff preview", session_id=SESSION, apply_relational_layer=False)
        assert preview.intent == "software_delivery_patch_diff_preview"
        assert "file_write_enabled" in preview.reply

        approved = resolve_chat_turn(
            f"approve patch proposal\n{PATCH_PROPOSAL_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert approved.intent == "software_delivery_patch_proposal_approved"

        timeline = resolve_chat_turn(
            "show software delivery timeline",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert "Patch receipts" in timeline.reply

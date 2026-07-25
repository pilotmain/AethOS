# SPDX-License-Identifier: Apache-2.0
"""FIX 125B — software delivery branch orchestration certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_orchestration_contract import (
    BRANCH_ARCHIVE_APPROVAL_PHRASE,
    BRANCH_CREATE_APPROVAL_PHRASE,
    BRANCH_RESTORE_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.branch_orchestration_receipts import clear_for_tests as clear_receipts
from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch_store
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_store import clear_for_tests
from tests.certification.helpers import assert_route_owns, reset_certification_runtime

pytestmark = pytest.mark.certification

SESSION = "software-delivery-cert-125b"


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_for_tests()
    clear_branch_store()
    clear_receipts()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_branch_store()
    clear_receipts()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestSoftwareDeliveryBranchOrchestrationCertification:
    def test_governed_branch_lane(self) -> None:
        analyze = resolve_chat_turn(
            "analyze github issue pilotmain/AethOS#102",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(analyze, route_id="software_delivery_issue_plan")

        plan = resolve_chat_turn(
            "create implementation plan",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(plan, route_id="software_delivery_issue_plan")

        approve = resolve_chat_turn(
            f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert approve.intent == "software_delivery_planning_approved"

        branch = resolve_chat_turn(
            f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(branch, route_id="software_delivery_issue_plan")
        assert branch.intent == "software_delivery_branch_created"
        assert branch.meta.get("software_delivery_stage") == "branch_create"

        status = resolve_chat_turn(
            "show implementation branch status",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert status.intent == "software_delivery_branch_status"
        assert "lifecycle_state" in status.reply

        timeline = resolve_chat_turn(
            "show software delivery timeline",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert timeline.intent == "software_delivery_timeline"
        assert "Branch receipts" in timeline.reply

        archived = resolve_chat_turn(
            f"archive implementation branch\n{BRANCH_ARCHIVE_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert archived.intent == "software_delivery_branch_archived"

        restored = resolve_chat_turn(
            f"restore implementation branch\n{BRANCH_RESTORE_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert restored.intent == "software_delivery_branch_restored"

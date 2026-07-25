# SPDX-License-Identifier: Apache-2.0
"""FIX 125A — software delivery issue plan certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_store import clear_for_tests
from tests.certification.helpers import assert_route_owns, reset_certification_runtime

pytestmark = pytest.mark.certification

SESSION = "software-delivery-cert-125a"


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestSoftwareDeliveryIssuePlanCertification:
    def test_governed_planning_lane(self) -> None:
        analyze = resolve_chat_turn(
            "analyze github issue pilotmain/AethOS#101",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(analyze, route_id="software_delivery_issue_plan")
        assert analyze.intent == "software_delivery_issue_analyzed"

        plan = resolve_chat_turn(
            "create implementation plan",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(plan, route_id="software_delivery_issue_plan")

        scope = resolve_chat_turn(
            "show implementation scope",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(scope, route_id="software_delivery_issue_plan")
        assert "blast_radius" in scope.reply

        risk = resolve_chat_turn(
            "show risk assessment",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(risk, route_id="software_delivery_issue_plan")

        approve = resolve_chat_turn(
            f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(approve, route_id="software_delivery_issue_plan")
        assert approve.intent == "software_delivery_planning_approved"
        assert "auto_merge" in approve.reply

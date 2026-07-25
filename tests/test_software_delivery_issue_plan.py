# SPDX-License-Identifier: Apache-2.0
"""FIX 125A — software delivery issue plan lane."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_contract import (
    AUTONOMOUS_MERGE_PERMITTED,
    CODE_GENERATION_ENABLED_FIX_125A,
    INFRA_MUTATION_PERMITTED,
    PLANNING_APPROVAL_PHRASE,
    SOFTWARE_DELIVERY_LANE_ID,
)
from aethos_core.software_delivery.issue_plan_service import (
    analyze_github_issue,
    approve_implementation_planning,
    create_implementation_plan,
    is_software_delivery_issue_plan_intent,
)
from aethos_core.software_delivery.issue_plan_store import clear_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    get_settings.cache_clear()


def test_intents():
    assert is_software_delivery_issue_plan_intent("analyze github issue pilotmain/AethOS#99")
    assert is_software_delivery_issue_plan_intent("create implementation plan")
    assert is_software_delivery_issue_plan_intent(PLANNING_APPROVAL_PHRASE)


def test_lane_safety_constants():
    assert AUTONOMOUS_MERGE_PERMITTED is False
    assert INFRA_MUTATION_PERMITTED is False
    assert CODE_GENERATION_ENABLED_FIX_125A is False


def test_analyze_create_approve_flow():
    session = "sd-plan-125a"
    analyzed = analyze_github_issue(
        session_id=session,
        user_text="analyze github issue pilotmain/AethOS#42",
    )
    assert analyzed.ok
    assert analyzed.plan["status"] == "analyzed"
    assert analyzed.plan["mutation_performed"] is False

    created = create_implementation_plan(session_id=session)
    assert created.ok
    assert created.plan["status"] == "plan_drafted"

    bad = approve_implementation_planning(session_id=session, user_text="approve")
    assert not bad.ok

    good = approve_implementation_planning(
        session_id=session,
        user_text=f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}",
    )
    assert good.ok
    assert good.plan["planning_approved"] is True


def test_approve_with_phrase_only_via_delivery_api():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    session = "sd-delivery-approve"
    client = TestClient(app)
    assert client.post(
        "/api/v1/delivery/propose",
        json={"message": "analyze github issue pilotmain/AethOS#1", "session_id": session},
    ).json()["ok"]
    assert client.post(
        "/api/v1/delivery/propose",
        json={"message": "create implementation plan", "session_id": session},
    ).json()["intent"] == "software_delivery_plan_created"
    approved = client.post(
        "/api/v1/delivery/propose",
        json={"message": PLANNING_APPROVAL_PHRASE, "session_id": session},
    ).json()
    assert approved["ok"] is True
    assert approved["intent"] == "software_delivery_planning_approved"

    again = client.post(
        "/api/v1/delivery/propose",
        json={"message": PLANNING_APPROVAL_PHRASE, "session_id": session},
    ).json()
    assert again["ok"] is True
    assert again["intent"] == "software_delivery_planning_approved"


def test_branch_create_via_delivery_api():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    session = "sd-delivery-branch"
    client = TestClient(app)
    assert client.post(
        "/api/v1/delivery/propose",
        json={"message": "analyze github issue pilotmain/AethOS#1", "session_id": session},
    ).json()["ok"]
    assert client.post(
        "/api/v1/delivery/propose",
        json={"message": "create implementation plan", "session_id": session},
    ).json()["ok"]
    assert client.post(
        "/api/v1/delivery/propose",
        json={"message": PLANNING_APPROVAL_PHRASE, "session_id": session},
    ).json()["intent"] == "software_delivery_planning_approved"

    blocked = client.post(
        "/api/v1/delivery/propose",
        json={"message": "create implementation branch", "session_id": session},
    ).json()
    assert blocked["ok"] is True
    assert blocked["intent"] == "software_delivery_branch_blocked"

    created = client.post(
        "/api/v1/delivery/propose",
        json={
            "message": f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
            "session_id": session,
        },
    ).json()
    assert created["ok"] is True
    assert created["intent"] == "software_delivery_branch_created"


def test_route_ownership_and_lane_separation():
    session = "sd-route-125a"
    result = resolve_chat_turn(
        "analyze github issue pilotmain/AethOS#7",
        session_id=session,
        apply_relational_layer=False,
    )
    assert result.meta.get("route_id") == SOFTWARE_DELIVERY_LANE_ID
    assert result.meta.get("lane_separation") == "software_delivery_not_infra"
    assert result.meta.get("mutation_performed") in {None, "false"}
    assert "infrastructure orchestration" in result.reply.lower() or "≠" in result.reply

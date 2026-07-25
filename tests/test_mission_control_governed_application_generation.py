# SPDX-License-Identifier: Apache-2.0
"""FIX 250 — governed application generation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governed_application_generation.governed_application_generation_contract import (
    APPLICATION_GENERATION_AUTHORITY_FIX_250,
    GOVERNED_APPLICATION_GENERATION_ROUTE_ID,
    REPOSITORY_CREATION_AUTHORITY_FIX_250,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_intent import (
    is_governed_application_generation_intent,
    parse_governed_application_generation_record_intent,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_service import (
    build_governed_application_generation,
    prepare_governed_application_generation_handoff,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_store import (
    append_governed_application_generation_record,
    clear_governed_application_generation_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_application_generation_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_governed_application_generation_records_for_tests()
    get_settings.cache_clear()


def _seed_generation_stack(session: str) -> None:
    append_governed_application_generation_record(
        session_id=session,
        kind="prd_intake_note",
        content="Pilot Analytics Dashboard — operator-facing metrics for governed delivery",
        metadata={"product_name": "Pilot Analytics Dashboard"},
    )
    append_governed_application_generation_record(
        session_id=session,
        kind="product_vision_note",
        content="Help operators understand delivery health across repositories",
    )
    append_governed_application_generation_record(
        session_id=session,
        kind="requirements_note",
        content="Must integrate with Mission Control evidence and verification gates",
    )
    append_governed_application_generation_record(
        session_id=session,
        kind="constraints_note",
        content="No autonomous deploy; human approval required for all lifecycle stages",
    )
    append_governed_application_generation_record(
        session_id=session,
        kind="architecture_package_note",
        content="API + web dashboard with read-only Mission Control integration",
    )
    append_governed_application_generation_record(
        session_id=session,
        kind="repository_blueprint_note",
        content="Monorepo with src/, web/, tests/, docs/",
    )
    append_governed_application_generation_record(
        session_id=session,
        kind="delivery_backlog_note",
        content="Epic: foundation, API shell, dashboard, verification integration",
    )
    append_governed_application_generation_record(
        session_id=session,
        kind="generation_decision_approve",
        content="Approve product creation plan for delivery pipeline handoff",
    )


def test_governed_application_generation_intent():
    assert is_governed_application_generation_intent("show governed application generation")
    assert is_governed_application_generation_intent("prepare delivery pipeline handoff")
    assert not is_governed_application_generation_intent("create repository now")


def test_prd_intake_record_intent():
    parsed = parse_governed_application_generation_record_intent(
        "prd intake: product=Pilot Analytics Dashboard operator metrics platform"
    )
    assert parsed is not None
    assert parsed[0] == "prd_intake_note"
    assert parsed[2].get("product_name") == "Pilot Analytics Dashboard operator metrics platform"


def test_generation_decision_record_intent():
    parsed = parse_governed_application_generation_record_intent(
        "generation decision approve: architecture and backlog reviewed"
    )
    assert parsed == ("generation_decision_approve", "architecture and backlog reviewed", {})


def test_build_application_generation():
    _seed_generation_stack("fix-250-gen")
    result = build_governed_application_generation(session_id="fix-250-gen")
    board = result.governed_application_generation
    assert board["application_generation_authority"] is APPLICATION_GENERATION_AUTHORITY_FIX_250
    assert board["repository_creation_authority"] is REPOSITORY_CREATION_AUTHORITY_FIX_250
    sections = board["sections"]
    assert sections["product_understanding_package"]
    assert sections["architecture_package"]
    assert sections["repository_blueprint"]
    assert sections["delivery_backlog"]
    assert sections["repository_creation_plan"]
    assert sections["generation_readiness_report"]
    assert sections["bounded_generation_agents"]


def test_delivery_pipeline_handoff_after_approval():
    _seed_generation_stack("fix-250-handoff")
    handoff = prepare_governed_application_generation_handoff(session_id="fix-250-handoff")
    assert handoff.ok is True
    assert handoff.delivery_pipeline_handoff["handoff_executable"] is False
    assert handoff.delivery_pipeline_handoff["feeds_existing_pipeline_only"] is True


def test_chat_route_show_application_generation():
    _seed_generation_stack("fix-250-chat")
    turn = resolve_chat_turn("show governed application generation", session_id="fix-250-chat")
    assert turn.intent == "mission_control_governed_application_generation"
    assert (turn.meta or {}).get("route_id") == GOVERNED_APPLICATION_GENERATION_ROUTE_ID


def test_governed_application_generation_api():
    _seed_generation_stack("fix-250-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/governed-application-generation",
        params={"session_id": "fix-250-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["application_generation_authority"] is False
    assert payload["repository_creation_authority"] is False
    assert payload["markdown"]

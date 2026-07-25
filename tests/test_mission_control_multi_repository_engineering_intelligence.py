# SPDX-License-Identifier: Apache-2.0
"""FIX 260 — multi-repository engineering intelligence tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_contract import (
    CROSS_REPO_AUTHORITY_FIX_260,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_ROUTE_ID,
    PORTFOLIO_AUTHORITY_FIX_260,
    PORTFOLIO_REPOSITORIES,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_intent import (
    parse_multi_repository_engineering_intelligence_intent,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_store import (
    append_multi_repository_engineering_intelligence_record,
    clear_multi_repository_engineering_intelligence_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_multi_repository_engineering_intelligence_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_multi_repository_engineering_intelligence_records_for_tests()
    get_settings.cache_clear()


def test_multi_repository_engineering_intelligence_intent():
    assert parse_multi_repository_engineering_intelligence_intent(
        "show multi repository engineering intelligence"
    ) == {"action": "view"}
    assert parse_multi_repository_engineering_intelligence_intent(
        "portfolio engineering dashboard"
    ) == {"action": "view"}
    parsed = parse_multi_repository_engineering_intelligence_intent(
        "cross repo dependency: source=pilotmain/pilot-os-ui target=pilotmain/AethOS relationship=advisory"
    )
    assert parsed is not None
    assert parsed["kind"] == "cross_repo_dependency_note"


def test_build_multi_repository_engineering_intelligence():
    result = build_multi_repository_engineering_intelligence(session_id="mc-mrei-260")
    assert result.ok is True
    board = result.multi_repository_engineering_intelligence
    assert board["portfolio_authority"] is False
    assert board["cross_repo_authority"] is False
    assert board["program_delivery_authority"] is False
    sections = board["sections"]
    assert sections["portfolio_engineering_dashboard"]
    assert sections["cross_repository_dependency_map"]
    assert sections["engineering_health_scores"]
    assert sections["program_delivery_visibility"]
    assert len(sections["engineering_health_scores"]) == len(PORTFOLIO_REPOSITORIES)


def test_operator_record_in_dependency_map():
    append_multi_repository_engineering_intelligence_record(
        kind="cross_repo_dependency_note",
        content="PilotOS UI shares UI patterns with AethOS Mission Control",
        session_id="mc-mrei-260",
        source_repository="pilotmain/pilot-os-ui",
        target_repository="pilotmain/AethOS",
        relationship="advisory",
    )
    result = build_multi_repository_engineering_intelligence(session_id="mc-mrei-260")
    deps = result.multi_repository_engineering_intelligence["sections"]["cross_repository_dependency_map"]
    assert any(d.get("operator_recorded") for d in deps)


def test_authority_flags():
    assert PORTFOLIO_AUTHORITY_FIX_260 is False
    assert CROSS_REPO_AUTHORITY_FIX_260 is False


def test_chat_route():
    turn = resolve_chat_turn("show portfolio engineering intelligence", session_id="mc-mrei-chat")
    assert turn.intent == "mission_control_multi_repository_engineering_intelligence"
    assert (turn.meta or {}).get("route_id") == MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/multi-repository-engineering-intelligence",
        params={"session_id": "mc-mrei-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["portfolio_authority"] is False
    assert body["multi_repository_engineering_intelligence"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/multi-repository-engineering-intelligence/record",
        json={
            "session_id": "mc-mrei-api",
            "kind": "portfolio_observation_note",
            "content": "Phase 2 repos remain unproven until independent pilot arcs complete",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

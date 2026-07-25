# SPDX-License-Identifier: Apache-2.0
"""FIX 261 — cross-repository product evolution intelligence tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_contract import (
    AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_ROUTE_ID,
    PORTFOLIO_REPOSITORIES,
    PRODUCT_EVOLUTION_AUTHORITY_FIX_261,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_intent import (
    parse_cross_repository_product_evolution_intelligence_intent,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_service import (
    build_cross_repository_product_evolution_intelligence,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_store import (
    append_cross_repository_product_evolution_intelligence_record,
    clear_cross_repository_product_evolution_intelligence_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_cross_repository_product_evolution_intelligence_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_cross_repository_product_evolution_intelligence_records_for_tests()
    get_settings.cache_clear()


def test_cross_repository_product_evolution_intelligence_intent():
    assert parse_cross_repository_product_evolution_intelligence_intent(
        "show product evolution intelligence"
    ) == {"action": "view"}
    parsed = parse_cross_repository_product_evolution_intelligence_intent(
        "evolution decision approve: Operator approves portfolio evolution backlog for governed delivery"
    )
    assert parsed == {
        "action": "record",
        "kind": "human_evolution_decision_approve",
        "content": "Operator approves portfolio evolution backlog for governed delivery",
    }
    note = parse_cross_repository_product_evolution_intelligence_intent(
        "feature evolution note: Add portfolio-wide observability dashboard"
    )
    assert note is not None
    assert note["kind"] == "feature_evolution_note"


def test_build_cross_repository_product_evolution_intelligence():
    result = build_cross_repository_product_evolution_intelligence(session_id="mc-crpei-261")
    assert result.ok is True
    board = result.cross_repository_product_evolution_intelligence
    assert board["product_evolution_authority"] is False
    assert board["automatic_improvement_enabled"] is False
    assert board["cross_repo_execution_enabled"] is False
    sections = board["sections"]
    assert sections["feature_evolution_report"]
    assert sections["quality_evolution_report"]
    assert sections["architecture_evolution_report"]
    assert sections["operational_evolution_report"]
    assert sections["ux_evolution_report"]
    assert sections["opportunity_graph"]
    assert sections["portfolio_evolution_backlog"]
    assert sections["evolution_priority_matrix"]
    assert sections["product_evolution_dashboard"]
    assert len(board["repositories"]) == len(PORTFOLIO_REPOSITORIES)


def test_human_evolution_decision_updates_dashboard():
    append_cross_repository_product_evolution_intelligence_record(
        kind="human_evolution_decision_approve",
        content="Operator approves top portfolio evolution opportunities for governed delivery planning",
        session_id="mc-crpei-261",
    )
    result = build_cross_repository_product_evolution_intelligence(session_id="mc-crpei-261")
    dashboard = result.cross_repository_product_evolution_intelligence["sections"]["product_evolution_dashboard"][0]
    assert result.cross_repository_product_evolution_intelligence["human_evolution_decision_approve"] is True
    assert dashboard["feeds_governed_delivery_pipeline"] is True


def test_operator_record_in_opportunities():
    append_cross_repository_product_evolution_intelligence_record(
        kind="quality_evolution_note",
        content="Reduce repeated verification failures in Atlas Trader pilot sessions",
        session_id="mc-crpei-261",
        repository="pilotmain/atlas-trader",
    )
    result = build_cross_repository_product_evolution_intelligence(session_id="mc-crpei-261")
    quality = result.cross_repository_product_evolution_intelligence["sections"]["quality_evolution_report"][0]
    assert any(r.get("operator_recorded") for r in quality.get("recommendations") or [])


def test_authority_flags():
    assert PRODUCT_EVOLUTION_AUTHORITY_FIX_261 is False
    assert AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261 is False


def test_chat_route():
    turn = resolve_chat_turn("show portfolio evolution intelligence", session_id="mc-crpei-chat")
    assert turn.intent == "mission_control_cross_repository_product_evolution_intelligence"
    assert (turn.meta or {}).get("route_id") == CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/cross-repository-product-evolution-intelligence",
        params={"session_id": "mc-crpei-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["product_evolution_authority"] is False
    assert body["cross_repository_product_evolution_intelligence"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/cross-repository-product-evolution-intelligence/record",
        json={
            "session_id": "mc-crpei-api",
            "kind": "evolution_backlog_note",
            "content": "Prioritize cross-repo monitoring improvements after human review",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

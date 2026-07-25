# SPDX-License-Identifier: Apache-2.0
"""FIX 314 — public launch readiness freeze tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_contract import (
    AUTOMATIC_LAUNCH_ENABLED_FIX_314,
    LAUNCH_FREEZE_AUTHORITY_FIX_314,
    LAUNCH_READINESS_FREEZE_DOMAINS,
    LAUNCH_RECOMMENDATION_FREEZE_VALUES,
    PUBLIC_LAUNCH_READINESS_FREEZE_ROUTE_ID,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_evaluator import (
    derive_launch_recommendation_freeze,
    summarize_trust_baselines,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_intent import (
    parse_public_launch_readiness_freeze_intent,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_service import (
    build_public_launch_readiness_freeze,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_store import (
    clear_public_launch_readiness_freeze_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_public_launch_readiness_freeze_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_public_launch_readiness_freeze_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_public_launch_readiness_freeze_intent():
    assert parse_public_launch_readiness_freeze_intent("show launch readiness freeze") == {
        "action": "view",
        "focus": "launch_readiness_freeze_dashboard",
    }
    assert parse_public_launch_readiness_freeze_intent("show launch baseline") == {
        "action": "view",
        "focus": "launch_readiness_freeze_dashboard",
    }
    assert parse_public_launch_readiness_freeze_intent("show launch evidence freeze") == {
        "action": "view",
        "focus": "launch_evidence_timeline",
    }
    parsed = parse_public_launch_readiness_freeze_intent(
        "launch freeze review approve: Human approves launch freeze review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "launch_freeze_review_decision_approve",
        "content": "Human approves launch freeze review only",
    }


def test_build_public_launch_readiness_freeze():
    result = build_public_launch_readiness_freeze(session_id="mc-plrf-314")
    assert result.ok is True
    board = result.public_launch_readiness_freeze
    assert board["launch_freeze_authority"] is False
    assert board["automatic_launch_enabled"] is False
    assert board["pilot_reexecution_performed"] is False
    sections = board["sections"]
    for key in LAUNCH_READINESS_FREEZE_DOMAINS:
        assert sections[key]


def test_trust_baselines_compose():
    rows = summarize_trust_baselines(
        fix_186={"trust_recommendation": "HOLD"},
        fix_192={"trust_recommendation": "HOLD"},
        fix_194={"trust_recommendation": "HOLD"},
        fix_196={"trust_recommendation": "HOLD"},
        fix_186_ok=True,
        fix_192_ok=True,
        fix_194_ok=True,
        fix_196_ok=True,
    )
    assert len(rows) == 4
    assert {row["product"] for row in rows} == {"AethOS", "PilotOS UI", "Atlas Trader", "Nexora"}


def test_capability_baseline_compose():
    result = build_public_launch_readiness_freeze(session_id="mc-plrf-cap")
    baseline = result.public_launch_readiness_freeze["sections"]["launch_capability_baseline"][0]
    assert baseline["evidence_sources"] == ["FIX 295", "FIX 296"]
    assert "proven_count" in baseline
    assert "unproven_count" in baseline


def test_operational_baseline_compose():
    result = build_public_launch_readiness_freeze(session_id="mc-plrf-ops")
    baseline = result.public_launch_readiness_freeze["sections"]["launch_operational_baseline"][0]
    assert baseline["evidence_sources"] == ["FIX 200", "FIX 210", "FIX 220", "FIX 230"]
    assert "platform_healthy" in baseline


def test_recommendation_derived_from_evidence():
    recommendation = derive_launch_recommendation_freeze(
        overall_launch_status="BLOCKED",
        launch_recommendation="BLOCK_LAUNCH",
        beta_recommendation="DO_NOT_LAUNCH",
        blocker_count=2,
        critical_risk_count=1,
        trust_baseline_count=2,
        platform_healthy=False,
        product_ready=False,
    )
    assert recommendation == "NOT_READY"
    assert recommendation in LAUNCH_RECOMMENDATION_FREEZE_VALUES

    result = build_public_launch_readiness_freeze(session_id="mc-plrf-rec")
    rec = result.public_launch_readiness_freeze["sections"]["launch_recommendation_freeze"][0]
    assert rec["recommendation"] in LAUNCH_RECOMMENDATION_FREEZE_VALUES
    assert rec["launch_execution_performed"] is False


def test_no_launch_authority_paths():
    result = build_public_launch_readiness_freeze(session_id="mc-plrf-no-launch")
    board = result.public_launch_readiness_freeze
    sources = board["sources"]
    dashboard = board["sections"]["launch_readiness_freeze_dashboard"][0]
    assert board["launch_freeze_authority"] is False
    assert sources["launch_execution_performed"] is False
    assert sources["pilot_reexecution_performed"] is False
    assert dashboard["launch_decision_performed"] is False


def test_regression_show_launch_readiness_freeze():
    turn = resolve_chat_turn("show launch readiness freeze", session_id="mc-plrf-regression")
    assert turn.intent == "mission_control_public_launch_readiness_freeze"
    lowered = turn.reply.lower()
    assert "freeze" in lowered or "baseline" in lowered
    assert "authority" in lowered or "humans" in lowered


def test_authority_flags():
    assert LAUNCH_FREEZE_AUTHORITY_FIX_314 is False
    assert AUTOMATIC_LAUNCH_ENABLED_FIX_314 is False


def test_chat_route():
    turn = resolve_chat_turn("show launch baseline", session_id="mc-plrf-chat")
    assert turn.intent == "mission_control_public_launch_readiness_freeze"
    assert (turn.meta or {}).get("route_id") == PUBLIC_LAUNCH_READINESS_FREEZE_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/public-launch-readiness-freeze",
        params={"session_id": "mc-plrf-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["launch_freeze_authority"] is False
    assert body["public_launch_readiness_freeze"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/public-launch-readiness-freeze",
        json={
            "session_id": "mc-plrf-api",
            "kind": "launch_freeze_note",
            "content": "Launch freeze review complete — no launch execution performed",
            "domain": "launch_readiness_freeze_dashboard",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

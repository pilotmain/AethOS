# SPDX-License-Identifier: Apache-2.0
"""FIX 315 — launch decision package tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.launch_decision_package.launch_decision_package_contract import (
    AUTOMATIC_LAUNCH_ENABLED_FIX_315,
    LAUNCH_DECISION_AUTHORITY_FIX_315,
    LAUNCH_DECISION_PACKAGE_DOMAINS,
    LAUNCH_DECISION_PACKAGE_ROUTE_ID,
    LAUNCH_RECOMMENDATION_PACKAGE_VALUES,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_evaluator import (
    bucket_risks_by_level,
    derive_launch_recommendation_package,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_intent import (
    parse_launch_decision_package_intent,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_service import (
    build_launch_decision_package,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_store import (
    append_launch_decision_package_record,
    clear_launch_decision_package_records_for_tests,
    list_launch_decision_package_records,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_store import (
    clear_public_launch_readiness_freeze_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_launch_decision_package_records_for_tests()
    clear_public_launch_readiness_freeze_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_launch_decision_package_records_for_tests()
    clear_public_launch_readiness_freeze_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_launch_decision_package_intent():
    assert parse_launch_decision_package_intent("show launch decision package") == {
        "action": "view",
        "focus": "launch_decision_dashboard",
    }
    assert parse_launch_decision_package_intent("show executive summary") == {
        "action": "view",
        "focus": "launch_executive_summary",
    }
    parsed = parse_launch_decision_package_intent(
        "launch decision approve: Human approves launch review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "launch_decision_approve",
        "content": "Human approves launch review only",
    }


def test_build_launch_decision_package():
    result = build_launch_decision_package(session_id="mc-ldp-315")
    assert result.ok is True
    board = result.launch_decision_package
    assert board["launch_decision_authority"] is False
    assert board["automatic_launch_approval_enabled"] is False
    sections = board["sections"]
    for key in LAUNCH_DECISION_PACKAGE_DOMAINS:
        assert sections[key]


def test_executive_summary_compose():
    result = build_launch_decision_package(session_id="mc-ldp-exec")
    executive = result.launch_decision_package["sections"]["launch_executive_summary"][0]
    assert executive["evidence_sources"] == ["FIX 314"]
    assert "platform_summary" in executive
    assert "recommendation_summary" in executive


def test_trust_evidence_compose():
    result = build_launch_decision_package(session_id="mc-ldp-trust")
    trust = result.launch_decision_package["sections"]["launch_trust_evidence_summary"][0]
    assert "FIX 186" in trust["evidence_sources"]
    assert "baseline_count" in trust


def test_operational_readiness_compose():
    result = build_launch_decision_package(session_id="mc-ldp-ops")
    operational = result.launch_decision_package["sections"]["launch_operational_summary"][0]
    assert "delivery_readiness" in operational
    assert "FIX 314" in operational["evidence_sources"]


def test_recommendation_derived_from_evidence():
    recommendation = derive_launch_recommendation_package(
        freeze_recommendation="NOT_READY",
        ops_recommendation="BLOCK_LAUNCH",
        beta_recommendation="DO_NOT_LAUNCH",
        blocker_count=2,
        critical_risk_count=1,
        platform_healthy=False,
    )
    assert recommendation == "DO_NOT_PROCEED"
    assert recommendation in LAUNCH_RECOMMENDATION_PACKAGE_VALUES

    result = build_launch_decision_package(session_id="mc-ldp-rec")
    rec = result.launch_decision_package["sections"]["launch_recommendation_package"][0]
    assert rec["recommendation"] in LAUNCH_RECOMMENDATION_PACKAGE_VALUES
    assert rec["launch_approval_performed"] is False


def test_decision_registry_records_reviews():
    append_launch_decision_package_record(
        kind="launch_decision_note",
        content="Executive review scheduled",
        session_id="mc-ldp-reg",
    )
    append_launch_decision_package_record(
        kind="launch_decision_hold",
        content="Hold pending beta evidence",
        session_id="mc-ldp-reg",
    )
    result = build_launch_decision_package(session_id="mc-ldp-reg")
    registry = result.launch_decision_package["sections"]["launch_decision_registry"][0]
    assert registry["record_count"] >= 2
    assert len(list_launch_decision_package_records()) >= 2


def test_risk_summary_buckets():
    buckets = bucket_risks_by_level(
        [
            {"level": "critical", "detail": "critical risk"},
            {"level": "high", "detail": "high risk"},
        ]
    )
    assert len(buckets["critical"]) == 1
    assert len(buckets["high"]) == 1


def test_no_launch_authority_paths():
    result = build_launch_decision_package(session_id="mc-ldp-no-launch")
    board = result.launch_decision_package
    sources = board["sources"]
    dashboard = board["sections"]["launch_decision_dashboard"][0]
    assert board["launch_decision_authority"] is False
    assert sources["launch_approval_performed"] is False
    assert sources["launch_execution_performed"] is False
    assert dashboard["launch_approval_performed"] is False


def test_regression_show_launch_decision_package():
    turn = resolve_chat_turn("show launch decision package", session_id="mc-ldp-regression")
    assert turn.intent == "mission_control_launch_decision_package"
    lowered = turn.reply.lower()
    assert "package" in lowered or "recommendation" in lowered
    assert "authority" in lowered or "humans" in lowered


def test_authority_flags():
    assert LAUNCH_DECISION_AUTHORITY_FIX_315 is False
    assert AUTOMATIC_LAUNCH_ENABLED_FIX_315 is False


def test_chat_route():
    turn = resolve_chat_turn("show executive summary", session_id="mc-ldp-chat")
    assert turn.intent == "mission_control_launch_decision_package"
    assert (turn.meta or {}).get("route_id") == LAUNCH_DECISION_PACKAGE_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/launch-decision-package",
        params={"session_id": "mc-ldp-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["launch_decision_authority"] is False
    assert body["launch_decision_package"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/launch-decision-package",
        json={
            "session_id": "mc-ldp-api",
            "kind": "launch_decision_note",
            "content": "Launch decision review complete — no launch approval performed",
            "domain": "launch_decision_dashboard",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

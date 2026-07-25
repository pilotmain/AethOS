# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — post-launch operations baseline tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_contract import (
    AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316,
    POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316,
    POST_LAUNCH_OPERATIONS_BASELINE_DOMAINS,
    POST_LAUNCH_OPERATIONS_BASELINE_ROUTE_ID,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_evaluator import (
    assess_customer_health,
    assess_platform_health,
    categorize_capabilities_for_baseline,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_intent import (
    parse_post_launch_operations_baseline_intent,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_service import (
    build_post_launch_operations_baseline,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_store import (
    append_post_launch_operations_baseline_record,
    clear_post_launch_operations_baseline_records_for_tests,
    list_post_launch_operations_baseline_records,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_post_launch_operations_baseline_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_post_launch_operations_baseline_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_post_launch_operations_baseline_intent():
    assert parse_post_launch_operations_baseline_intent("show post launch operations baseline") == {
        "action": "view",
        "focus": "post_launch_operations_dashboard",
    }
    assert parse_post_launch_operations_baseline_intent("show platform baseline") == {
        "action": "view",
        "focus": "platform_health_baseline",
    }
    parsed = parse_post_launch_operations_baseline_intent(
        "operations baseline review approve: Human approves operations baseline review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "operations_baseline_review_decision_approve",
        "content": "Human approves operations baseline review only",
    }


def test_build_post_launch_operations_baseline():
    result = build_post_launch_operations_baseline(session_id="mc-plob-316")
    assert result.ok is True
    board = result.post_launch_operations_baseline
    assert board["post_launch_operations_authority"] is False
    assert board["automatic_operational_execution_enabled"] is False
    sections = board["sections"]
    for key in POST_LAUNCH_OPERATIONS_BASELINE_DOMAINS:
        assert sections[key]


def test_platform_health_baseline_compose():
    result = build_post_launch_operations_baseline(session_id="mc-plob-platform")
    baseline = result.post_launch_operations_baseline["sections"]["platform_health_baseline"][0]
    assert baseline["evidence_sources"] == ["FIX 220", "FIX 313"]
    assert "deployment_health" in baseline
    assert "monitoring_health" in baseline


def test_customer_health_baseline_compose():
    result = build_post_launch_operations_baseline(session_id="mc-plob-customer")
    baseline = result.post_launch_operations_baseline["sections"]["customer_health_baseline"][0]
    assert baseline["evidence_sources"] == ["FIX 310", "FIX 312"]
    assert "healthy_count" in baseline


def test_governance_health_baseline_compose():
    result = build_post_launch_operations_baseline(session_id="mc-plob-gov")
    baseline = result.post_launch_operations_baseline["sections"]["governance_health_baseline"][0]
    assert "FIX 302" in baseline["evidence_sources"]
    assert "FIX 307" in baseline["evidence_sources"]


def test_incident_baseline_compose():
    result = build_post_launch_operations_baseline(session_id="mc-plob-incident")
    baseline = result.post_launch_operations_baseline["sections"]["incident_baseline"][0]
    assert baseline["evidence_sources"] == ["FIX 220", "FIX 230", "FIX 313"]
    assert "incident_count" in baseline


def test_platform_health_assessment():
    assert assess_platform_health(
        monitoring_ok=True,
        monitoring_classification="HEALTHY",
        platform_healthy=True,
        deployment_health=True,
    ) == "HEALTHY"
    assert assess_platform_health(
        monitoring_ok=True,
        monitoring_classification="INCIDENT",
        platform_healthy=False,
        deployment_health=False,
    ) == "DEGRADED"


def test_customer_health_assessment():
    assert assess_customer_health(
        healthy_count=5,
        at_risk_count=1,
        beta_participants=3,
        support_ready=True,
    ) == "ATTENTION"


def test_capability_baseline_compose():
    categories = categorize_capabilities_for_baseline(
        [
            {"name": "proven", "status": "PROVEN"},
            {"name": "experimental", "status": "EXPERIMENTAL"},
            {"name": "blocked", "status": "BLOCKED"},
        ]
    )
    assert len(categories["proven"]) == 1
    assert len(categories["experimental"]) == 1
    assert len(categories["blocked"]) == 1


def test_baseline_registry_records_reviews():
    append_post_launch_operations_baseline_record(
        kind="operations_baseline_note",
        content="Weekly operations baseline review scheduled",
        session_id="mc-plob-reg",
    )
    append_post_launch_operations_baseline_record(
        kind="operations_baseline_review_decision_hold",
        content="Hold pending incident review",
        session_id="mc-plob-reg",
    )
    result = build_post_launch_operations_baseline(session_id="mc-plob-reg")
    registry = result.post_launch_operations_baseline["sections"]["operations_baseline_registry"][0]
    assert registry["record_count"] >= 2
    assert len(list_post_launch_operations_baseline_records()) >= 2


def test_no_operational_authority_paths():
    result = build_post_launch_operations_baseline(session_id="mc-plob-no-exec")
    board = result.post_launch_operations_baseline
    sources = board["sources"]
    dashboard = board["sections"]["post_launch_operations_dashboard"][0]
    assert board["post_launch_operations_authority"] is False
    assert sources["operational_execution_performed"] is False
    assert sources["incident_response_performed"] is False
    assert dashboard["operational_execution_performed"] is False


def test_regression_show_post_launch_operations_baseline():
    turn = resolve_chat_turn("show post launch operations baseline", session_id="mc-plob-regression")
    assert turn.intent == "mission_control_post_launch_operations_baseline"
    lowered = turn.reply.lower()
    assert "baseline" in lowered or "platform" in lowered
    assert "authority" in lowered or "observation" in lowered or "execution" in lowered


def test_authority_flags():
    assert POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316 is False
    assert AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316 is False


def test_chat_route():
    turn = resolve_chat_turn("show operations dashboard", session_id="mc-plob-chat")
    assert turn.intent == "mission_control_post_launch_operations_baseline"
    assert (turn.meta or {}).get("route_id") == POST_LAUNCH_OPERATIONS_BASELINE_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/post-launch-operations-baseline",
        params={"session_id": "mc-plob-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["post_launch_operations_authority"] is False
    assert body["post_launch_operations_baseline"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/post-launch-operations-baseline",
        json={
            "session_id": "mc-plob-api",
            "kind": "operations_baseline_note",
            "content": "Operations baseline review complete — no operational execution performed",
            "domain": "post_launch_operations_dashboard",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

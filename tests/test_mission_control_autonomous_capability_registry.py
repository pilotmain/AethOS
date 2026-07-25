# SPDX-License-Identifier: Apache-2.0
"""FIX 295 — autonomous capability registry tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_contract import (
    AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295,
    AUTONOMOUS_CAPABILITY_REGISTRY_ROUTE_ID,
    CAPABILITY_AUTHORITY_FIX_295,
    CAPABILITY_DOMAINS,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_intent import (
    parse_autonomous_capability_registry_intent,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_store import (
    append_autonomous_capability_registry_record,
    clear_autonomous_capability_registry_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_autonomous_capability_registry_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_autonomous_capability_registry_records_for_tests()
    get_settings.cache_clear()


def test_autonomous_capability_registry_intent():
    assert parse_autonomous_capability_registry_intent("show capability registry") == {
        "action": "view",
        "focus": "registry",
    }
    assert parse_autonomous_capability_registry_intent("what can you do") == {
        "action": "view",
        "focus": "self_awareness",
    }
    parsed = parse_autonomous_capability_registry_intent(
        "capability review approve: Operator approves capability maturity assessment for Q3"
    )
    assert parsed == {
        "action": "record",
        "kind": "human_capability_review_approve",
        "content": "Operator approves capability maturity assessment for Q3",
    }
    note = parse_autonomous_capability_registry_intent(
        "capability note: capability_id=provider_github Document GitHub readonly inventory support"
    )
    assert note is not None
    assert note["kind"] == "capability_note"
    assert note["capability_id"] == "provider_github"


def test_build_autonomous_capability_registry():
    result = build_autonomous_capability_registry(session_id="mc-acr-295")
    assert result.ok is True
    board = result.autonomous_capability_registry
    assert board["capability_authority"] is False
    assert board["self_authority_granting_enabled"] is False
    assert board["automatic_capability_promotion_enabled"] is False
    assert board["certified_fix_count"] >= 10
    sections = board["sections"]
    assert sections["capability_registry"]
    assert sections["capability_evidence_registry"]
    assert sections["capability_maturity_dashboard"]
    assert sections["capability_drift_report"]
    assert sections["self_awareness_report"]
    assert sections["provider_capability_matrix"]
    assert sections["repository_trust_matrix"]
    assert sections["capability_dashboard"]
    for domain in CAPABILITY_DOMAINS:
        assert sections[f"{domain}_capability_report"]


def test_self_awareness_report_from_live_evidence():
    result = build_autonomous_capability_registry(session_id="mc-acr-295")
    report = result.autonomous_capability_registry["sections"]["self_awareness_report"][0]
    assert report["answers_from_live_evidence"] is True
    assert report["what_can_you_do"]
    assert report["what_cant_you_do"]
    assert report["supported_providers"]


def test_human_capability_review_updates_dashboard():
    append_autonomous_capability_registry_record(
        kind="human_capability_review_approve",
        content="Operator approves capability registry maturity review",
        session_id="mc-acr-295",
    )
    result = build_autonomous_capability_registry(session_id="mc-acr-295")
    dashboard = result.autonomous_capability_registry["sections"]["capability_dashboard"][0]
    assert result.autonomous_capability_registry["human_capability_review_approve"] is True
    assert dashboard["human_capability_review_approve"] is True


def test_capability_note_in_evidence_registry():
    append_autonomous_capability_registry_record(
        kind="capability_evidence_note",
        content="Pilot evidence confirms governed merge lifecycle receipts",
        session_id="mc-acr-295",
        capability_id="merge_lifecycle",
        capability_domain="delivery",
    )
    result = build_autonomous_capability_registry(session_id="mc-acr-295")
    evidence = result.autonomous_capability_registry["sections"]["capability_evidence_registry"][0]
    assert evidence["artifact_count"] >= 1


def test_authority_flags():
    assert CAPABILITY_AUTHORITY_FIX_295 is False
    assert AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295 is False


def test_chat_route():
    turn = resolve_chat_turn("show self-awareness report", session_id="mc-acr-chat")
    assert turn.intent == "mission_control_autonomous_capability_registry"
    assert (turn.meta or {}).get("route_id") == AUTONOMOUS_CAPABILITY_REGISTRY_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/autonomous-capability-registry",
        params={"session_id": "mc-acr-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["capability_authority"] is False
    assert body["autonomous_capability_registry"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/autonomous-capability-registry/record",
        json={
            "session_id": "mc-acr-api",
            "kind": "capability_note",
            "content": "Capability registry should surface FIX 295 self-awareness in chat routing",
            "capability_id": "capability_registry",
            "capability_domain": "intelligence",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

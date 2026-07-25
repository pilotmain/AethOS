# SPDX-License-Identifier: Apache-2.0
"""FIX 300 — multi-tenant platform foundation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_contract import (
    AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300,
    CROSS_TENANT_ACCESS_ENABLED_FIX_300,
    MULTI_TENANT_PLATFORM_FOUNDATION_ROUTE_ID,
    TENANT_AUTHORITY_FIX_300,
    TENANT_DOMAINS,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_intent import (
    parse_multi_tenant_platform_foundation_intent,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_store import (
    append_multi_tenant_platform_foundation_record,
    clear_multi_tenant_platform_foundation_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_multi_tenant_platform_foundation_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_multi_tenant_platform_foundation_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_multi_tenant_platform_foundation_intent():
    assert parse_multi_tenant_platform_foundation_intent("show tenant dashboard") == {"action": "view"}
    parsed = parse_multi_tenant_platform_foundation_intent(
        "tenant governance review approve: Operator approves organization onboarding for pilot customer"
    )
    assert parsed == {
        "action": "record",
        "kind": "human_tenant_decision_approve",
        "content": "Operator approves organization onboarding for pilot customer",
        "tenant_domain": "governance_isolation",
    }
    note = parse_multi_tenant_platform_foundation_intent(
        "workspace create review: org_id=org-default Create engineering workspace for portfolio delivery"
    )
    assert note is not None
    assert note["kind"] == "workspace_create_review_note"
    assert note["tenant_domain"] == "workspaces"


def test_build_multi_tenant_platform_foundation():
    result = build_multi_tenant_platform_foundation(session_id="mc-mtpf-300")
    assert result.ok is True
    board = result.multi_tenant_platform_foundation
    assert board["tenant_authority"] is False
    assert board["automatic_tenant_creation_enabled"] is False
    assert board["cross_tenant_access_enabled"] is False
    assert board["cross_tenant_trust_enabled"] is False
    sections = board["sections"]
    assert sections["organization_registry"]
    assert sections["workspace_registry"]
    assert sections["project_registry"]
    assert sections["identity_registry"]
    assert sections["role_registry"]
    assert sections["permission_registry"]
    assert sections["tenant_trust_registry"]
    assert sections["tenant_governance_boundary_registry"]
    assert sections["tenant_onboarding_registry"]
    assert sections["channel_registry"]
    assert sections["tenant_dashboard"]
    assert len(sections["tenant_dashboard"][0]["tenant_domains"]) == len(TENANT_DOMAINS)


def test_human_tenant_decision_updates_dashboard():
    append_multi_tenant_platform_foundation_record(
        kind="human_tenant_decision_approve",
        content="Operator approves tenant foundation readiness for external organization onboarding",
        session_id="mc-mtpf-300",
    )
    result = build_multi_tenant_platform_foundation(session_id="mc-mtpf-300")
    dashboard = result.multi_tenant_platform_foundation["sections"]["tenant_dashboard"][0]
    assert result.multi_tenant_platform_foundation["human_tenant_decision_approve"] is True
    assert dashboard["human_tenant_decision_approve"] is True


def test_governance_isolation_registry():
    result = build_multi_tenant_platform_foundation(session_id="mc-mtpf-300")
    boundaries = result.multi_tenant_platform_foundation["sections"]["tenant_governance_boundary_registry"][0]
    assert boundaries["boundary_count"] >= 1
    assert boundaries["boundaries"][0]["cross_tenant_access_enabled"] is False


def test_authority_flags():
    assert TENANT_AUTHORITY_FIX_300 is False
    assert AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300 is False
    assert CROSS_TENANT_ACCESS_ENABLED_FIX_300 is False


def test_chat_route():
    turn = resolve_chat_turn("show multi-tenant platform foundation", session_id="mc-mtpf-chat")
    assert turn.intent == "mission_control_multi_tenant_platform_foundation"
    assert (turn.meta or {}).get("route_id") == MULTI_TENANT_PLATFORM_FOUNDATION_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/multi-tenant-platform-foundation",
        params={"session_id": "mc-mtpf-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["tenant_authority"] is False
    assert body["multi_tenant_platform_foundation"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/multi-tenant-platform-foundation/record",
        json={
            "session_id": "mc-mtpf-api",
            "kind": "membership_review_note",
            "content": "Review operator membership for external workspace access",
            "tenant_domain": "identity",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

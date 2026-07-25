# SPDX-License-Identifier: Apache-2.0
"""FIX 304 — channel integration foundation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_contract import (
    AUTHORIZATION_BYPASS_ENABLED_FIX_304,
    AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304,
    CHANNEL_AUTHORITY_FIX_304,
    CHANNEL_INTEGRATION_FOUNDATION_ROUTE_ID,
    CHANNELS,
    CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304,
    CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_intent import (
    parse_channel_integration_foundation_intent,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
    build_channel_integration_foundation,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_store import (
    clear_channel_integration_foundation_records_for_tests,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    clear_identity_access_hardening_records_for_tests,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
    clear_provider_connection_experience_records_for_tests,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    clear_tenant_onboarding_activation_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_channel_integration_foundation_intent():
    assert parse_channel_integration_foundation_intent("show channels") == {
        "action": "view",
        "focus": "channel_dashboard",
    }
    assert parse_channel_integration_foundation_intent("show channel readiness") == {
        "action": "view",
        "focus": "channel_readiness",
    }
    parsed = parse_channel_integration_foundation_intent(
        "channel review approve: Operator confirms Telegram bot configured"
    )
    assert parsed == {
        "action": "record",
        "kind": "channel_decision_approve",
        "content": "Operator confirms Telegram bot configured",
    }


def test_build_channel_integration_foundation():
    result = build_channel_integration_foundation(session_id="mc-cif-304")
    assert result.ok is True
    board = result.channel_integration_foundation
    assert board["channel_authority"] is False
    assert board["automatic_channel_provisioning_enabled"] is False
    assert board["authorization_bypass_enabled"] is False
    sections = board["sections"]
    assert sections["channel_registry"]
    assert sections["channel_identity_report"]
    assert sections["channel_authorization_report"]
    assert sections["channel_capability_matrix"]
    assert sections["web_channel_report"]
    assert sections["telegram_channel_report"]
    assert sections["slack_channel_report"]
    assert sections["email_channel_report"]
    assert sections["voice_channel_report"]
    assert sections["channel_dashboard"]


def test_channel_registry_includes_all_channels():
    result = build_channel_integration_foundation(session_id="mc-cif-channels")
    registry = result.channel_integration_foundation["sections"]["channel_registry"][0]
    channel_names = {row["channel"] for row in registry["channels"]}
    assert channel_names == set(CHANNELS)


def test_regression_show_channels():
    turn = resolve_chat_turn("show channels", session_id="mc-cif-regression")
    assert turn.intent == "mission_control_channel_integration_foundation"
    lowered = turn.reply.lower()
    for channel in CHANNELS:
        assert channel in lowered
    assert "mission control" in lowered
    assert "authorization" in lowered
    assert "capability" in lowered
    assert "cross-tenant" not in lowered or "no channel-specific governance or cross-tenant" in lowered


def test_authority_flags():
    assert CHANNEL_AUTHORITY_FIX_304 is False
    assert AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304 is False
    assert CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304 is False
    assert CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304 is False
    assert AUTHORIZATION_BYPASS_ENABLED_FIX_304 is False


def test_chat_route():
    turn = resolve_chat_turn("show channel authorization", session_id="mc-cif-chat")
    assert turn.intent == "mission_control_channel_integration_foundation"
    assert (turn.meta or {}).get("route_id") == CHANNEL_INTEGRATION_FOUNDATION_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/channel-integration-foundation",
        params={"session_id": "mc-cif-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["channel_authority"] is False
    assert body["channel_integration_foundation"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/channel-integration-foundation/record",
        json={
            "session_id": "mc-cif-api",
            "kind": "channel_note",
            "content": "Telegram bot token configured in Settings — not in chat",
            "channel": "telegram",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

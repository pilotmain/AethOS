# SPDX-License-Identifier: Apache-2.0
"""FIX 303 — provider connection experience tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    clear_identity_access_hardening_records_for_tests,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
    AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303,
    PHASE_1_PROVIDERS,
    PHASE_2_PROVIDERS,
    PROVIDER_CONNECTION_AUTHORITY_FIX_303,
    PROVIDER_CONNECTION_EXPERIENCE_ROUTE_ID,
    SECRET_COLLECTION_ENABLED_FIX_303,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_evaluator import (
    build_provider_connection_report,
    evaluate_provider_readiness,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_intent import (
    parse_provider_connection_experience_intent,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
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
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_provider_connection_experience_intent():
    assert parse_provider_connection_experience_intent("show provider connections") == {
        "action": "view",
        "focus": "provider_connection_dashboard",
    }
    assert parse_provider_connection_experience_intent("show provider readiness") == {
        "action": "view",
        "focus": "provider_connection_readiness_report",
    }
    parsed = parse_provider_connection_experience_intent(
        "provider connection review approve: Operator confirms GitHub token configured in Settings"
    )
    assert parsed == {
        "action": "record",
        "kind": "provider_connection_decision_approve",
        "content": "Operator confirms GitHub token configured in Settings",
    }


def test_build_provider_connection_experience():
    result = build_provider_connection_experience(session_id="mc-pce-303")
    assert result.ok is True
    board = result.provider_connection_experience
    assert board["provider_connection_authority"] is False
    assert board["automatic_provider_connection_enabled"] is False
    assert board["secret_collection_enabled"] is False
    sections = board["sections"]
    assert sections["provider_connection_dashboard"]
    assert sections["github_connection_report"]
    assert sections["railway_connection_report"]
    assert sections["vercel_connection_report"]
    assert sections["provider_capability_unlock_matrix"]
    assert sections["provider_connection_readiness_report"]
    assert sections["provider_trust_explanation"]


def test_phase_2_providers_planned_without_connection_flow():
    result = build_provider_connection_experience(session_id="mc-pce-phase2")
    readiness = result.provider_connection_experience["sections"]["provider_connection_readiness_report"][0]
    planned = {row["provider"]: row for row in readiness["phase_2_planned"]}
    for provider in PHASE_2_PROVIDERS:
        assert planned[provider]["status"] == "PLANNED"
        assert planned[provider]["connection_flow_available"] is False


def test_github_connection_report_includes_unlocks():
    report = build_provider_connection_report(provider="GitHub")
    assert report["capability_unlocks"]
    assert "Repository intelligence" in report["capability_unlocks"]
    assert report["secret_collection_in_chat_forbidden"] is True


def test_evaluate_provider_readiness_phase_1():
    row = evaluate_provider_readiness(provider="GitHub")
    assert row["phase"] == "phase_1"
    assert row["connection_flow_available"] is True
    assert "credentials_present" in row


def test_regression_show_provider_connections():
    turn = resolve_chat_turn("show provider connections", session_id="mc-pce-regression")
    assert turn.intent == "mission_control_provider_connection_experience"
    lowered = turn.reply.lower()
    assert "github" in lowered
    assert "railway" in lowered
    assert "vercel" in lowered
    assert "capability unlock" in lowered or "unlocks" in lowered
    assert "never paste secrets" in lowered or "never automatic" in lowered
    for provider in PHASE_1_PROVIDERS:
        assert provider.lower() in lowered


def test_authority_flags():
    assert PROVIDER_CONNECTION_AUTHORITY_FIX_303 is False
    assert AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303 is False
    assert SECRET_COLLECTION_ENABLED_FIX_303 is False


def test_chat_route():
    turn = resolve_chat_turn("show provider readiness", session_id="mc-pce-chat")
    assert turn.intent == "mission_control_provider_connection_experience"
    assert (turn.meta or {}).get("route_id") == PROVIDER_CONNECTION_EXPERIENCE_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/provider-connection-experience",
        params={"session_id": "mc-pce-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["provider_connection_authority"] is False
    assert body["provider_connection_experience"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/provider-connection-experience/record",
        json={
            "session_id": "mc-pce-api",
            "kind": "provider_connection_note",
            "content": "Railway token configured in Credential Center — not in chat",
            "provider": "Railway",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

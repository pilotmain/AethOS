# SPDX-License-Identifier: Apache-2.0
"""FIX 301 — tenant onboarding and activation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
    AUTOMATIC_PROVISIONING_ENABLED_FIX_301,
    ONBOARDING_AUTHORITY_FIX_301,
    ONBOARDING_STEPS,
    SECRET_COLLECTION_ENABLED_FIX_301,
    TENANT_ONBOARDING_ACTIVATION_ROUTE_ID,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_intent import (
    is_tenant_onboarding_activation_question,
    parse_tenant_onboarding_activation_intent,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
    build_tenant_onboarding_activation,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    append_tenant_onboarding_activation_record,
    clear_tenant_onboarding_activation_records_for_tests,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_store import (
    clear_multi_tenant_platform_foundation_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_tenant_onboarding_activation_records_for_tests()
    clear_multi_tenant_platform_foundation_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_tenant_onboarding_activation_records_for_tests()
    clear_multi_tenant_platform_foundation_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_onboarding_intent():
    assert parse_tenant_onboarding_activation_intent("show tenant onboarding") == {"action": "view"}
    assert parse_tenant_onboarding_activation_intent("start tenant onboarding") == {"action": "view"}
    assert is_tenant_onboarding_activation_question("How do I start using AethOS?")
    parsed = parse_tenant_onboarding_activation_intent(
        "organization setup: name=Pilot Org primary_operator=ray use_case=pilot governance=strict"
    )
    assert parsed is not None
    assert parsed["kind"] == "organization_setup_review_note"
    assert parsed["onboarding_step"] == "organization_setup"


def test_build_tenant_onboarding_activation():
    result = build_tenant_onboarding_activation(session_id="mc-toa-301")
    assert result.ok is True
    board = result.tenant_onboarding_activation
    assert board["onboarding_authority"] is False
    assert board["automatic_provisioning_enabled"] is False
    assert board["secret_collection_enabled"] is False
    sections = board["sections"]
    assert sections["tenant_onboarding_dashboard"]
    assert sections["organization_setup_review"]
    assert sections["workspace_setup_review"]
    assert sections["project_registration_review"]
    assert sections["provider_connection_checklist"]
    assert sections["capability_discovery_report"]
    assert sections["trust_explanation_report"]
    assert sections["first_mission_control_activation_packet"]
    assert sections["onboarding_progress_registry"]
    assert len(board["onboarding_steps"]) == len(ONBOARDING_STEPS)


def test_onboarding_progress_updates_with_review_notes():
    sid = "mc-toa-progress"
    append_tenant_onboarding_activation_record(
        kind="organization_setup_review_note",
        content="Organization Pilot Org ready for human review",
        session_id=sid,
        onboarding_step="organization_setup",
    )
    append_tenant_onboarding_activation_record(
        kind="workspace_setup_review_note",
        content="Engineering workspace for portfolio delivery",
        session_id=sid,
        onboarding_step="workspace_setup",
    )
    result = build_tenant_onboarding_activation(session_id=sid)
    progress = result.tenant_onboarding_activation["sections"]["onboarding_progress_registry"][0]
    statuses = {row["step_id"]: row["status"] for row in progress["steps"]}
    assert statuses["organization_setup"] == "review_recorded"
    assert statuses["workspace_setup"] == "review_recorded"
    assert statuses["capability_discovery"] == "ready"


def test_regression_how_do_i_start_using_aethos():
    turn = resolve_chat_turn("How do I start using AethOS?", session_id="mc-toa-regression")
    assert turn.intent == "mission_control_tenant_onboarding_activation"
    lowered = turn.reply.lower()
    for phrase in (
        "organization setup",
        "workspace setup",
        "project registration",
        "provider connection",
        "capability discovery",
        "trust explanation",
        "first mission control",
        "governed workflow",
    ):
        assert phrase in lowered
    assert "automatic provisioning" not in lowered or "no automatic provisioning" in lowered
    assert "paste secrets" in lowered or "never paste secrets" in lowered


def test_authority_flags():
    assert ONBOARDING_AUTHORITY_FIX_301 is False
    assert AUTOMATIC_PROVISIONING_ENABLED_FIX_301 is False
    assert SECRET_COLLECTION_ENABLED_FIX_301 is False


def test_chat_route():
    turn = resolve_chat_turn("show tenant onboarding", session_id="mc-toa-chat")
    assert turn.intent == "mission_control_tenant_onboarding_activation"
    assert (turn.meta or {}).get("route_id") == TENANT_ONBOARDING_ACTIVATION_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/tenant-onboarding-activation",
        params={"session_id": "mc-toa-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["onboarding_authority"] is False
    assert body["tenant_onboarding_activation"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/tenant-onboarding-activation/record",
        json={
            "session_id": "mc-toa-api",
            "kind": "provider_connection_note",
            "content": "GitHub token configured in Settings Connections — not in chat",
            "onboarding_step": "provider_connection",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

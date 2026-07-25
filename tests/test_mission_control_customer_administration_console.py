# SPDX-License-Identifier: Apache-2.0
"""FIX 306 — customer administration console tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_store import (
    clear_billing_entitlements_foundation_records_for_tests,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_store import (
    clear_channel_integration_foundation_records_for_tests,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_contract import (
    ADMINISTRATION_AUTHORITY_FIX_306,
    AUTOMATIC_USER_CREATION_ENABLED_FIX_306,
    CUSTOMER_ADMINISTRATION_CONSOLE_ROUTE_ID,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_evaluator import (
    admin_surface_access,
    evaluate_administration_access,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_intent import (
    parse_customer_administration_console_intent,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_service import (
    build_customer_administration_console,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_store import (
    clear_customer_administration_console_records_for_tests,
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
from aethos_core.orgs.members import assign_role
from aethos_core.orgs.organizations import clear_orgs_for_tests, get_current_organization


@pytest.fixture(autouse=True)
def _clean():
    clear_customer_administration_console_records_for_tests()
    clear_billing_entitlements_foundation_records_for_tests()
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_customer_administration_console_records_for_tests()
    clear_billing_entitlements_foundation_records_for_tests()
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_customer_administration_console_intent():
    assert parse_customer_administration_console_intent("show administration console") == {
        "action": "view",
        "focus": "customer_administration_dashboard",
    }
    assert parse_customer_administration_console_intent("show organization administration") == {
        "action": "view",
        "focus": "organization_administration_report",
    }
    parsed = parse_customer_administration_console_intent(
        "administration review approve: Operator confirms org administration review complete"
    )
    assert parsed == {
        "action": "record",
        "kind": "administration_decision_approve",
        "content": "Operator confirms org administration review complete",
    }


def test_build_customer_administration_console():
    result = build_customer_administration_console(session_id="mc-cac-306")
    assert result.ok is True
    board = result.customer_administration_console
    assert board["administration_authority"] is False
    assert board["automatic_user_creation_enabled"] is False
    assert board["billing_mutation_authority"] is False
    sections = board["sections"]
    for key in (
        "organization_administration_report",
        "user_administration_report",
        "role_administration_report",
        "workspace_administration_report",
        "project_administration_report",
        "provider_administration_report",
        "channel_administration_report",
        "billing_administration_report",
        "governance_administration_report",
        "customer_administration_dashboard",
    ):
        assert sections[key]


def test_admin_dashboard_composes_all_domains():
    result = build_customer_administration_console(session_id="mc-cac-domains")
    dashboard = result.customer_administration_console["sections"]["customer_administration_dashboard"][0]
    assert dashboard["organization_health"]
    assert dashboard["provider_health"]
    assert dashboard["channel_health"]
    assert dashboard["billing_health"]
    assert dashboard["governance_health"]


def test_viewer_cannot_access_admin_only_views():
    org_id = get_current_organization()["org_id"]
    assign_role(user_id="viewer-user", role="viewer", org_id=org_id)
    access = evaluate_administration_access(role="viewer", requester_org_id=org_id)
    assert access["allowed"] is False
    surfaces = admin_surface_access(role="viewer", requester_org_id=org_id)
    assert surfaces["user_administration_report"] is False
    assert surfaces["billing_administration_report"] is False
    assert surfaces["governance_administration_report"] is False


def test_cross_tenant_administration_blocked():
    org_id = get_current_organization()["org_id"]
    access = evaluate_administration_access(role="admin", requester_org_id=org_id, target_org_id="org-other")
    assert access["allowed"] is False
    assert access["cross_tenant_administration_enabled"] is False


def test_billing_and_governance_compose_in_console():
    result = build_customer_administration_console(session_id="mc-cac-compose")
    sections = result.customer_administration_console["sections"]
    billing = sections["billing_administration_report"][0]
    governance = sections["governance_administration_report"][0]
    providers = sections["provider_administration_report"][0]
    channels = sections["channel_administration_report"][0]
    assert billing["composed_from_fix_305"] is True
    assert billing["plan"]
    assert governance["governance_actions"] is not None
    assert providers["composed_from_fix_303"] is True
    assert channels["composed_from_fix_304"] is True


def test_regression_show_administration_console():
    turn = resolve_chat_turn("show administration console", session_id="mc-cac-regression")
    assert turn.intent == "mission_control_customer_administration_console"
    lowered = turn.reply.lower()
    assert "organization" in lowered
    assert "provider" in lowered
    assert "channel" in lowered
    assert "billing" in lowered
    assert "governance" in lowered
    assert "automatic" in lowered or "no automatic" in lowered


def test_authority_flags():
    assert ADMINISTRATION_AUTHORITY_FIX_306 is False
    assert AUTOMATIC_USER_CREATION_ENABLED_FIX_306 is False


def test_chat_route():
    turn = resolve_chat_turn("show governance administration", session_id="mc-cac-chat")
    assert turn.intent == "mission_control_customer_administration_console"
    assert (turn.meta or {}).get("route_id") == CUSTOMER_ADMINISTRATION_CONSOLE_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/customer-administration-console",
        params={"session_id": "mc-cac-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["administration_authority"] is False
    assert body["customer_administration_console"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/customer-administration-console/record",
        json={
            "session_id": "mc-cac-api",
            "kind": "administration_note",
            "content": "Org administration review complete — no automatic user creation",
            "domain": "organization_administration",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

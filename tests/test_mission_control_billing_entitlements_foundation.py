# SPDX-License-Identifier: Apache-2.0
"""FIX 305 — billing & entitlements foundation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_contract import (
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305,
    BILLING_AUTHORITY_FIX_305,
    BILLING_ENTITLEMENTS_FOUNDATION_ROUTE_ID,
    PAYMENT_PROCESSING_ENABLED_FIX_305,
    PLANS,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_evaluator import (
    enterprise_only_capabilities,
    free_blocked_from_enterprise_entitlements,
    is_capability_entitled,
    normalize_commercial_plan,
    usage_within_limits,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_intent import (
    parse_billing_entitlements_foundation_intent,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_store import (
    clear_billing_entitlements_foundation_records_for_tests,
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
    clear_billing_entitlements_foundation_records_for_tests()
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_billing_entitlements_foundation_records_for_tests()
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_billing_entitlements_foundation_intent():
    assert parse_billing_entitlements_foundation_intent("show billing") == {
        "action": "view",
        "focus": "billing_dashboard",
    }
    assert parse_billing_entitlements_foundation_intent("show entitlements") == {
        "action": "view",
        "focus": "entitlement_registry",
    }
    parsed = parse_billing_entitlements_foundation_intent(
        "billing review approve: Operator confirms STARTER plan review complete"
    )
    assert parsed == {
        "action": "record",
        "kind": "billing_decision_approve",
        "content": "Operator confirms STARTER plan review complete",
    }


def test_build_billing_entitlements_foundation():
    result = build_billing_entitlements_foundation(session_id="mc-bef-305")
    assert result.ok is True
    board = result.billing_entitlements_foundation
    assert board["billing_authority"] is False
    assert board["payment_processing_enabled"] is False
    assert board["automatic_plan_upgrade_enabled"] is False
    sections = board["sections"]
    assert sections["plan_registry"]
    assert sections["subscription_registry"]
    assert sections["entitlement_registry"]
    assert sections["usage_registry"]
    assert sections["capability_entitlement_matrix"]
    assert sections["channel_entitlement_matrix"]
    assert sections["provider_entitlement_matrix"]
    assert sections["usage_limit_report"]
    assert sections["billing_readiness_report"]
    assert sections["billing_dashboard"]


def test_plan_registry_includes_all_plans():
    result = build_billing_entitlements_foundation(session_id="mc-bef-plans")
    registry = result.billing_entitlements_foundation["sections"]["plan_registry"][0]
    plan_names = {row["plan"] for row in registry["plans"]}
    assert plan_names == set(PLANS)


def test_free_blocked_from_enterprise_entitlements():
    blocked = free_blocked_from_enterprise_entitlements(plan="FREE")
    for capability in enterprise_only_capabilities():
        assert capability in blocked
        assert is_capability_entitled(plan="FREE", capability=capability) is False
        assert is_capability_entitled(plan="ENTERPRISE", capability=capability) is True


def test_usage_limits_compose_correctly():
    report = usage_within_limits(
        plan="FREE",
        usage={
            "organizations": 1,
            "workspaces": 1,
            "projects": 1,
            "repositories": 1,
            "executions": 5,
        },
    )
    assert report["within_all_limits"] is True
    over = usage_within_limits(
        plan="FREE",
        usage={
            "organizations": 2,
            "workspaces": 1,
            "projects": 1,
            "repositories": 1,
            "executions": 5,
        },
    )
    assert over["within_all_limits"] is False


def test_default_org_maps_to_starter():
    assert normalize_commercial_plan("team") == "STARTER"


def test_regression_show_billing():
    turn = resolve_chat_turn("show billing", session_id="mc-bef-regression")
    assert turn.intent == "mission_control_billing_entitlements_foundation"
    lowered = turn.reply.lower()
    assert "plan" in lowered
    assert "entitlement" in lowered
    assert "payment processing" in lowered or "no payment" in lowered
    assert "automatic plan" in lowered or "no automatic" in lowered
    for plan in ("free", "starter", "pro", "business", "enterprise"):
        assert plan in lowered or "capability entitlement matrix" in lowered


def test_authority_flags():
    assert BILLING_AUTHORITY_FIX_305 is False
    assert PAYMENT_PROCESSING_ENABLED_FIX_305 is False
    assert AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305 is False


def test_chat_route():
    turn = resolve_chat_turn("show subscription status", session_id="mc-bef-chat")
    assert turn.intent == "mission_control_billing_entitlements_foundation"
    assert (turn.meta or {}).get("route_id") == BILLING_ENTITLEMENTS_FOUNDATION_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/billing-entitlements-foundation",
        params={"session_id": "mc-bef-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["billing_authority"] is False
    assert body["payment_processing_enabled"] is False
    assert body["billing_entitlements_foundation"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/billing-entitlements-foundation/record",
        json={
            "session_id": "mc-bef-api",
            "kind": "billing_note",
            "content": "Plan review complete — no payment collected in chat",
            "plan": "STARTER",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

# SPDX-License-Identifier: Apache-2.0
"""FIX 308 — payment integration readiness tests."""

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
from aethos_core.mission_control.customer_administration_console.customer_administration_console_store import (
    clear_customer_administration_console_records_for_tests,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_store import (
    clear_customer_usage_audit_portal_records_for_tests,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    clear_identity_access_hardening_records_for_tests,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_contract import (
    CREDIT_CARD_STORAGE_ENABLED_FIX_308,
    PAYMENT_INTEGRATION_READINESS_ROUTE_ID,
    PAYMENT_PROCESSING_ENABLED_FIX_308,
    PAYMENT_PROVIDERS,
    SUBSCRIPTION_LIFECYCLE_STATES,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_evaluator import (
    payment_provider_readiness_rows,
    subscription_lifecycle_rows,
    usage_monetization_rows,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_intent import (
    parse_payment_integration_readiness_intent,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
    build_payment_integration_readiness,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_store import (
    clear_payment_integration_readiness_records_for_tests,
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
    clear_payment_integration_readiness_records_for_tests()
    clear_customer_usage_audit_portal_records_for_tests()
    clear_customer_administration_console_records_for_tests()
    clear_billing_entitlements_foundation_records_for_tests()
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_payment_integration_readiness_records_for_tests()
    clear_customer_usage_audit_portal_records_for_tests()
    clear_customer_administration_console_records_for_tests()
    clear_billing_entitlements_foundation_records_for_tests()
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_payment_integration_readiness_intent():
    assert parse_payment_integration_readiness_intent("show payment readiness") == {
        "action": "view",
        "focus": "payment_readiness_dashboard",
    }
    assert parse_payment_integration_readiness_intent("show upgrade paths") == {
        "action": "view",
        "focus": "upgrade_path_registry",
    }
    parsed = parse_payment_integration_readiness_intent(
        "payment readiness review approve: Operator confirms Stripe readiness review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "payment_readiness_decision_approve",
        "content": "Operator confirms Stripe readiness review only",
    }


def test_build_payment_integration_readiness():
    result = build_payment_integration_readiness(session_id="mc-pir-308")
    assert result.ok is True
    board = result.payment_integration_readiness
    assert board["payment_processing_enabled"] is False
    assert board["credit_card_storage_enabled"] is False
    assert board["subscription_mutation_authority"] is False
    sections = board["sections"]
    for key in (
        "customer_billing_identity_registry",
        "payment_provider_registry",
        "subscription_lifecycle_registry",
        "billing_event_registry",
        "invoice_readiness_registry",
        "usage_monetization_registry",
        "commercial_analytics_dashboard",
        "upgrade_path_registry",
        "payment_readiness_dashboard",
        "commercial_governance_report",
    ):
        assert sections[key]


def test_subscription_lifecycle_states_compose():
    rows = subscription_lifecycle_rows(commercial_plan="FREE", trial_status="eligible")
    states = {row["state"] for row in rows}
    assert states == set(SUBSCRIPTION_LIFECYCLE_STATES)
    assert sum(1 for row in rows if row["current_for_tenant"]) == 1


def test_upgrade_paths_compose():
    result = build_payment_integration_readiness(session_id="mc-pir-upgrades")
    upgrades = result.payment_integration_readiness["sections"]["upgrade_path_registry"][0]
    assert upgrades["current_plan"]
    assert isinstance(upgrades["eligible_paths"], list)


def test_usage_monetization_registry_compose():
    rows = usage_monetization_rows(
        plan="STARTER",
        usage={
            "organizations": 1,
            "workspaces": 1,
            "projects": 1,
            "repositories": 1,
            "executions": 0,
        },
    )
    assert rows
    assert all(row["future_billable"] is True for row in rows)


def test_payment_providers_readiness_only():
    providers = payment_provider_readiness_rows()
    assert len(providers) == len(PAYMENT_PROVIDERS)
    for row in providers:
        assert row["integration_status"] == "readiness_only"
        assert row["configured"] is False
        assert row["payment_processing_enabled"] is False
        assert row["credit_card_storage_enabled"] is False


def test_no_payment_processing_paths():
    result = build_payment_integration_readiness(session_id="mc-pir-no-payment")
    sources = result.payment_integration_readiness["sources"]
    assert sources["payment_collection_performed"] is False
    assert sources["credit_card_storage_performed"] is False
    assert result.payment_integration_readiness["payment_processing_enabled"] is False


def test_regression_show_payment_readiness():
    turn = resolve_chat_turn("show payment readiness", session_id="mc-pir-regression")
    assert turn.intent == "mission_control_payment_integration_readiness"
    lowered = turn.reply.lower()
    assert "stripe" in lowered or "payment provider" in lowered
    assert "subscription" in lowered
    assert "payment processing" in lowered or "no payment" in lowered
    assert "credit card" in lowered or "card storage" in lowered


def test_authority_flags():
    assert PAYMENT_PROCESSING_ENABLED_FIX_308 is False
    assert CREDIT_CARD_STORAGE_ENABLED_FIX_308 is False


def test_chat_route():
    turn = resolve_chat_turn("show billing events", session_id="mc-pir-chat")
    assert turn.intent == "mission_control_payment_integration_readiness"
    assert (turn.meta or {}).get("route_id") == PAYMENT_INTEGRATION_READINESS_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/payment-integration-readiness",
        params={"session_id": "mc-pir-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["payment_processing_enabled"] is False
    assert body["payment_integration_readiness"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/payment-integration-readiness/record",
        json={
            "session_id": "mc-pir-api",
            "kind": "payment_readiness_note",
            "content": "Stripe readiness reviewed — no payment processing enabled",
            "provider": "Stripe",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

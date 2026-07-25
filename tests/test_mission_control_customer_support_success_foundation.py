# SPDX-License-Identifier: Apache-2.0
"""FIX 310 — customer support & success foundation tests."""

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
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_contract import (
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310,
    CUSTOMER_HEALTH_STATUSES,
    CUSTOMER_SUPPORT_AUTHORITY_FIX_310,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_ROUTE_ID,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_evaluator import (
    score_customer_health,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_intent import (
    parse_customer_support_success_foundation_intent,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
    build_customer_support_success_foundation,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_store import (
    clear_customer_support_success_foundation_records_for_tests,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_store import (
    clear_customer_usage_audit_portal_records_for_tests,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    clear_identity_access_hardening_records_for_tests,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_store import (
    clear_payment_integration_readiness_records_for_tests,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
    clear_provider_connection_experience_records_for_tests,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_store import (
    clear_saas_launch_readiness_assessment_records_for_tests,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    clear_tenant_onboarding_activation_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_customer_support_success_foundation_records_for_tests()
    clear_saas_launch_readiness_assessment_records_for_tests()
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
    clear_customer_support_success_foundation_records_for_tests()
    clear_saas_launch_readiness_assessment_records_for_tests()
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


def test_customer_support_success_foundation_intent():
    assert parse_customer_support_success_foundation_intent("show customer support") == {
        "action": "view",
        "focus": "customer_support_success_dashboard",
    }
    assert parse_customer_support_success_foundation_intent("show customer health") == {
        "action": "view",
        "focus": "customer_health_registry",
    }
    parsed = parse_customer_support_success_foundation_intent(
        "support review approve: Human approves support review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "support_review_decision_approve",
        "content": "Human approves support review only",
    }


def test_build_customer_support_success_foundation():
    result = build_customer_support_success_foundation(session_id="mc-cssf-310")
    assert result.ok is True
    board = result.customer_support_success_foundation
    assert board["customer_support_authority"] is False
    assert board["automatic_customer_contact_enabled"] is False
    sections = board["sections"]
    for key in (
        "customer_health_registry",
        "customer_success_dashboard",
        "support_request_registry",
        "customer_adoption_report",
        "customer_trust_report",
        "customer_risk_registry",
        "customer_escalation_registry",
        "success_opportunity_registry",
        "support_analytics_dashboard",
        "customer_support_success_dashboard",
    ):
        assert sections[key]


def test_all_support_domains_compose():
    result = build_customer_support_success_foundation(session_id="mc-cssf-domains")
    dashboard = result.customer_support_success_foundation["sections"]["customer_support_success_dashboard"][0]
    assert dashboard["evidence_coverage"]["fix_300_309_total"] == 10


def test_customer_health_scoring():
    status = score_customer_health(
        onboarding_ready=True,
        provider_ready=True,
        channel_ready=True,
        billing_ready=True,
        workspace_count=2,
        member_count=3,
        plan="pro",
    )
    assert status in CUSTOMER_HEALTH_STATUSES
    assert status == "HIGH_VALUE"


def test_trust_and_adoption_included():
    result = build_customer_support_success_foundation(session_id="mc-cssf-trust")
    adoption = result.customer_support_success_foundation["sections"]["customer_adoption_report"][0]
    trust = result.customer_support_success_foundation["sections"]["customer_trust_report"][0]
    assert adoption.get("report_id") == "customer-adoption-report"
    assert any(check["check_id"] == "onboarding" for check in adoption["checks"])
    assert "FIX 295" in trust["evidence_sources"]
    assert "FIX 309" in trust["evidence_sources"]


def test_no_customer_contact_path():
    result = build_customer_support_success_foundation(session_id="mc-cssf-no-contact")
    sources = result.customer_support_success_foundation["sources"]
    dashboard = result.customer_support_success_foundation["sections"]["customer_support_success_dashboard"][0]
    assert sources["customer_contact_performed"] is False
    assert sources["ticket_execution_performed"] is False
    assert dashboard["customer_contact_performed"] is False
    assert result.customer_support_success_foundation["customer_support_authority"] is False


def test_regression_show_customer_support():
    turn = resolve_chat_turn("show customer support", session_id="mc-cssf-regression")
    assert turn.intent == "mission_control_customer_support_success_foundation"
    lowered = turn.reply.lower()
    assert "healthy" in lowered or "at-risk" in lowered or "at risk" in lowered
    assert "support" in lowered or "visibility" in lowered
    assert "authority" in lowered or "humans" in lowered


def test_authority_flags():
    assert CUSTOMER_SUPPORT_AUTHORITY_FIX_310 is False
    assert AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310 is False


def test_chat_route():
    turn = resolve_chat_turn("show customer escalations", session_id="mc-cssf-chat")
    assert turn.intent == "mission_control_customer_support_success_foundation"
    assert (turn.meta or {}).get("route_id") == CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/customer-support-success-foundation",
        params={"session_id": "mc-cssf-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["customer_support_authority"] is False
    assert body["customer_support_success_foundation"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/customer-support-success-foundation",
        json={
            "session_id": "mc-cssf-api",
            "kind": "support_note",
            "content": "Review at-risk customer onboarding — no outreach performed",
            "domain": "customer_support_success_dashboard",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

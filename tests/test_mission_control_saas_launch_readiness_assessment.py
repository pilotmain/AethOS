# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — SaaS launch readiness assessment tests."""

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
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_store import (
    clear_payment_integration_readiness_records_for_tests,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
    clear_provider_connection_experience_records_for_tests,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_contract import (
    AUTOMATIC_LAUNCH_ENABLED_FIX_309,
    DOMAIN_SCORES,
    LAUNCH_AUTHORITY_FIX_309,
    OVERALL_LAUNCH_STATUSES,
    SAAS_LAUNCH_READINESS_ASSESSMENT_ROUTE_ID,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_evaluator import (
    derive_overall_status,
    score_domain,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_intent import (
    parse_saas_launch_readiness_assessment_intent,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
    build_saas_launch_readiness_assessment,
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


def test_saas_launch_readiness_assessment_intent():
    assert parse_saas_launch_readiness_assessment_intent("show launch readiness") == {
        "action": "view",
        "focus": "launch_readiness_dashboard",
    }
    assert parse_saas_launch_readiness_assessment_intent("show launch blockers") == {
        "action": "view",
        "focus": "launch_risk_registry",
    }
    parsed = parse_saas_launch_readiness_assessment_intent(
        "launch readiness review approve: Human approves limited beta readiness review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "launch_readiness_decision_approve",
        "content": "Human approves limited beta readiness review only",
    }


def test_build_saas_launch_readiness_assessment():
    result = build_saas_launch_readiness_assessment(session_id="mc-slra-309")
    assert result.ok is True
    board = result.saas_launch_readiness_assessment
    assert board["launch_authority"] is False
    assert board["automatic_launch_enabled"] is False
    assert board["customer_provisioning_authority"] is False
    sections = board["sections"]
    for key in (
        "product_readiness_report",
        "platform_readiness_report",
        "security_readiness_report",
        "governance_readiness_report",
        "operational_readiness_report",
        "commercial_readiness_report",
        "customer_readiness_report",
        "support_readiness_report",
        "launch_risk_registry",
        "launch_readiness_dashboard",
    ):
        assert sections[key]


def test_all_readiness_domains_compose():
    result = build_saas_launch_readiness_assessment(session_id="mc-slra-domains")
    dashboard = result.saas_launch_readiness_assessment["sections"]["launch_readiness_dashboard"][0]
    scores = dashboard["domain_scores"]
    assert len(scores) == 8
    assert all(score in DOMAIN_SCORES for score in scores.values())


def test_risks_aggregate_correctly():
    result = build_saas_launch_readiness_assessment(session_id="mc-slra-risks")
    registry = result.saas_launch_readiness_assessment["sections"]["launch_risk_registry"][0]
    assert registry["risk_count"] >= 0
    assert "critical" in registry
    assert "high" in registry


def test_launch_status_derived_from_evidence():
    status = derive_overall_status(
        domain_scores={"product_readiness": "NOT_READY", "platform_readiness": "READY"},
        risks=[{"level": "critical", "detail": "blocker"}],
    )
    assert status == "BLOCKED"
    assert status in OVERALL_LAUNCH_STATUSES


def test_commercial_and_provider_readiness_included():
    result = build_saas_launch_readiness_assessment(session_id="mc-slra-commercial")
    commercial = result.saas_launch_readiness_assessment["sections"]["commercial_readiness_report"][0]
    platform = result.saas_launch_readiness_assessment["sections"]["platform_readiness_report"][0]
    assert commercial["domain"] == "commercial_readiness"
    assert platform["domain"] == "platform_readiness"
    assert any(check["check_id"] == "payment_readiness" for check in commercial["checks"])
    assert any(check["check_id"] == "providers" for check in platform["checks"])


def test_no_launch_declaration_path():
    result = build_saas_launch_readiness_assessment(session_id="mc-slra-no-launch")
    sources = result.saas_launch_readiness_assessment["sources"]
    dashboard = result.saas_launch_readiness_assessment["sections"]["launch_readiness_dashboard"][0]
    assert sources["launch_declaration_performed"] is False
    assert dashboard["launch_declaration_performed"] is False
    assert result.saas_launch_readiness_assessment["launch_authority"] is False


def test_score_domain_with_blockers():
    assert score_domain(signals_ready=4, signals_total=4, blockers=["missing"]) == "NOT_READY"


def test_regression_show_launch_readiness():
    turn = resolve_chat_turn("show launch readiness", session_id="mc-slra-regression")
    assert turn.intent == "mission_control_saas_launch_readiness_assessment"
    lowered = turn.reply.lower()
    assert "overall" in lowered or "launch status" in lowered
    assert "launch authority" in lowered or "humans decide" in lowered
    assert "launch declaration" in lowered or "no launch" in lowered


def test_authority_flags():
    assert LAUNCH_AUTHORITY_FIX_309 is False
    assert AUTOMATIC_LAUNCH_ENABLED_FIX_309 is False


def test_chat_route():
    turn = resolve_chat_turn("show launch risks", session_id="mc-slra-chat")
    assert turn.intent == "mission_control_saas_launch_readiness_assessment"
    assert (turn.meta or {}).get("route_id") == SAAS_LAUNCH_READINESS_ASSESSMENT_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/saas-launch-readiness-assessment",
        params={"session_id": "mc-slra-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["launch_authority"] is False
    assert body["saas_launch_readiness_assessment"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/saas-launch-readiness-assessment/record",
        json={
            "session_id": "mc-slra-api",
            "kind": "launch_readiness_note",
            "content": "Limited beta review complete — no launch declaration performed",
            "domain": "launch_readiness_dashboard",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

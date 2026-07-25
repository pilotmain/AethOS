# SPDX-License-Identifier: Apache-2.0
"""FIX 307 — customer usage & audit portal tests."""

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
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_contract import (
    AUDIT_AUTHORITY_FIX_307,
    AUDIT_MUTATION_ENABLED_FIX_307,
    CUSTOMER_USAGE_AUDIT_PORTAL_ROUTE_ID,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_evaluator import (
    evaluate_audit_portal_access,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_intent import (
    parse_customer_usage_audit_portal_intent,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_service import (
    build_customer_usage_audit_portal,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_store import (
    append_customer_usage_audit_portal_record,
    clear_customer_usage_audit_portal_records_for_tests,
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
from aethos_core.orgs.audit_attribution import clear_attributions_for_tests, record_attribution
from aethos_core.orgs.organizations import clear_orgs_for_tests, get_current_organization


@pytest.fixture(autouse=True)
def _clean():
    clear_customer_usage_audit_portal_records_for_tests()
    clear_customer_administration_console_records_for_tests()
    clear_billing_entitlements_foundation_records_for_tests()
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_attributions_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_customer_usage_audit_portal_records_for_tests()
    clear_customer_administration_console_records_for_tests()
    clear_billing_entitlements_foundation_records_for_tests()
    clear_channel_integration_foundation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_identity_access_hardening_records_for_tests()
    clear_attributions_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_customer_usage_audit_portal_intent():
    assert parse_customer_usage_audit_portal_intent("show audit portal") == {
        "action": "view",
        "focus": "customer_audit_dashboard",
    }
    assert parse_customer_usage_audit_portal_intent("show activity timeline") == {
        "action": "view",
        "focus": "activity_timeline",
    }
    parsed = parse_customer_usage_audit_portal_intent(
        "audit review approve: Operator confirms audit portal review complete"
    )
    assert parsed == {
        "action": "record",
        "kind": "audit_decision_approve",
        "content": "Operator confirms audit portal review complete",
    }


def test_build_customer_usage_audit_portal():
    result = build_customer_usage_audit_portal(session_id="mc-cuap-307")
    assert result.ok is True
    board = result.customer_usage_audit_portal
    assert board["audit_authority"] is False
    assert board["audit_mutation_enabled"] is False
    assert board["evidence_mutation_enabled"] is False
    sections = board["sections"]
    for key in (
        "activity_timeline",
        "governance_timeline",
        "usage_timeline",
        "audit_registry",
        "repository_activity_report",
        "user_activity_report",
        "provider_activity_report",
        "billing_usage_history_report",
        "evidence_explorer",
        "customer_audit_dashboard",
    ):
        assert sections[key]


def test_activity_and_governance_timelines_compose():
    org_id = get_current_organization()["org_id"]
    record_attribution(
        actor_id="operator",
        actor_role="admin",
        action="approval_recording",
        resource_type="approval",
        resource_id="apr-1",
        org_id=org_id,
        approved=True,
    )
    append_customer_usage_audit_portal_record(
        kind="audit_note",
        content="Timeline test note",
        session_id="mc-cuap-timeline",
    )
    result = build_customer_usage_audit_portal(session_id="mc-cuap-timeline")
    sections = result.customer_usage_audit_portal["sections"]
    assert sections["activity_timeline"][0]["entry_count"] >= 1
    assert sections["audit_registry"][0]["entry_count"] >= 1


def test_evidence_explorer_surfaces_trust_artifacts():
    result = build_customer_usage_audit_portal(session_id="mc-cuap-evidence")
    explorer = result.customer_usage_audit_portal["sections"]["evidence_explorer"][0]
    assert "trust_freezes" in explorer
    assert "governance_evidence" in explorer
    assert explorer["evidence_mutation_enabled"] is False


def test_cross_tenant_audit_access_blocked():
    org_id = get_current_organization()["org_id"]
    access = evaluate_audit_portal_access(role="admin", requester_org_id=org_id, target_org_id="org-other")
    assert access["allowed"] is False
    assert access["cross_tenant_audit_access_enabled"] is False


def test_audit_records_immutable():
    record = append_customer_usage_audit_portal_record(
        kind="audit_note",
        content="Immutable audit note",
        session_id="mc-cuap-immutable",
    )
    assert record["immutable"] is True
    result = build_customer_usage_audit_portal(session_id="mc-cuap-immutable")
    assert result.customer_usage_audit_portal["audit_mutation_enabled"] is False


def test_billing_history_composes():
    result = build_customer_usage_audit_portal(session_id="mc-cuap-billing")
    billing = result.customer_usage_audit_portal["sections"]["billing_usage_history_report"][0]
    assert billing["composed_from_fix_305"] is True
    assert billing["plan"]


def test_customer_dashboard_composes_all_domains():
    result = build_customer_usage_audit_portal(session_id="mc-cuap-dashboard")
    dashboard = result.customer_usage_audit_portal["sections"]["customer_audit_dashboard"][0]
    assert "activity_entry_count" in dashboard
    assert "governance_entry_count" in dashboard
    assert "usage_entry_count" in dashboard
    assert dashboard["audit_health"]


def test_regression_show_audit_portal():
    turn = resolve_chat_turn("show audit portal", session_id="mc-cuap-regression")
    assert turn.intent == "mission_control_customer_usage_audit_portal"
    lowered = turn.reply.lower()
    assert "activity" in lowered
    assert "governance" in lowered
    assert "audit" in lowered
    assert "immutable" in lowered or "mutation" in lowered


def test_authority_flags():
    assert AUDIT_AUTHORITY_FIX_307 is False
    assert AUDIT_MUTATION_ENABLED_FIX_307 is False


def test_chat_route():
    turn = resolve_chat_turn("show evidence explorer", session_id="mc-cuap-chat")
    assert turn.intent == "mission_control_customer_usage_audit_portal"
    assert (turn.meta or {}).get("route_id") == CUSTOMER_USAGE_AUDIT_PORTAL_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/customer-usage-audit-portal",
        params={"session_id": "mc-cuap-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["audit_authority"] is False
    assert body["customer_usage_audit_portal"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/customer-usage-audit-portal/record",
        json={
            "session_id": "mc-cuap-api",
            "kind": "audit_note",
            "content": "Audit review complete — no record mutation",
            "domain": "activity_timeline",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True

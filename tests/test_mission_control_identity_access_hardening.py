# SPDX-License-Identifier: Apache-2.0
"""FIX 302 — identity and access hardening tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
    AUTHORIZATION_AUTHORITY_FIX_302,
    AUTHORIZATION_DOMAINS,
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302,
    IDENTITY_ACCESS_HARDENING_ROUTE_ID,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_evaluator import (
    evaluate_access_request,
    evaluate_tenant_boundary,
    role_has_tenant_permission,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_intent import (
    parse_identity_access_hardening_intent,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
    build_identity_access_hardening,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    clear_identity_access_hardening_records_for_tests,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_store import (
    clear_multi_tenant_platform_foundation_records_for_tests,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    clear_tenant_onboarding_activation_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests, create_organization, get_current_organization
from aethos_core.orgs.members import assign_role


@pytest.fixture(autouse=True)
def _clean():
    clear_identity_access_hardening_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_multi_tenant_platform_foundation_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_identity_access_hardening_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_multi_tenant_platform_foundation_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_identity_access_hardening_intent():
    assert parse_identity_access_hardening_intent("show authorization report") == {
        "action": "view",
        "focus": "authorization_dashboard",
    }
    assert parse_identity_access_hardening_intent("show permission evaluation") == {
        "action": "view",
        "focus": "permission_evaluation",
    }
    parsed = parse_identity_access_hardening_intent(
        "authorization review approve: Operator approves identity access review for pilot tenant"
    )
    assert parsed == {
        "action": "record",
        "kind": "authorization_decision_approve",
        "content": "Operator approves identity access review for pilot tenant",
    }


def test_build_identity_access_hardening():
    result = build_identity_access_hardening(session_id="mc-iah-302")
    assert result.ok is True
    board = result.identity_access_hardening
    assert board["authorization_authority"] is False
    assert board["automatic_permission_granting_enabled"] is False
    assert board["authorization_bypass_enabled"] is False
    sections = board["sections"]
    assert sections["authorization_dashboard"]
    assert sections["identity_resolution_report"]
    assert sections["permission_evaluation_report"]
    assert sections["tenant_boundary_audit"]
    assert sections["mission_control_authorization_report"]
    assert sections["repository_access_report"]
    assert sections["governance_action_report"]
    assert sections["authorization_audit_registry"]
    assert sections["least_privilege_report"]
    assert sections["channel_authorization_report"]
    assert sections["session_trust_report"]
    assert len(board["authorization_domains"]) == len(AUTHORIZATION_DOMAINS)


def test_regression_observer_cannot_approve():
    assert role_has_tenant_permission(role="viewer", permission="view") is True
    assert role_has_tenant_permission(role="viewer", permission="approve") is False


def test_regression_reviewer_cannot_administer():
    assert role_has_tenant_permission(role="reviewer", permission="review") is True
    assert role_has_tenant_permission(role="reviewer", permission="administer") is False


def test_regression_operator_cannot_govern():
    assert role_has_tenant_permission(role="operator", permission="operate") is True
    assert role_has_tenant_permission(role="operator", permission="govern") is False


def test_regression_admin_cannot_cross_tenant_boundary():
    current = get_current_organization()
    other = create_organization(name="Other Org")
    boundary = evaluate_tenant_boundary(
        requester_org_id=str(current.get("org_id")),
        target_org_id=str(other.get("org_id")),
    )
    assert boundary["allowed"] is False
    assert boundary["cross_tenant_access_enabled"] is False


def test_regression_cross_tenant_trust_reads_blocked():
    current = get_current_organization()
    other = create_organization(name="Trust Isolated Org")
    result = evaluate_access_request(
        role="admin",
        permission="view",
        requester_org_id=str(current.get("org_id")),
        target_org_id=str(other.get("org_id")),
    )
    assert result["allowed"] is False
    assert result["tenant_boundary_passed"] is False


def test_regression_mission_control_protected():
    result = build_identity_access_hardening(session_id="mc-iah-protected")
    report = result.identity_access_hardening["sections"]["mission_control_authorization_report"][0]
    assert report["mission_control_protected"] is True
    assert len(report["protected_surfaces"]) >= 4


def test_regression_governance_actions_permission_checked():
    result = build_identity_access_hardening(session_id="mc-iah-governance")
    report = result.identity_access_hardening["sections"]["governance_action_report"][0]
    assert report["governance_actions_permission_checked"] is True
    merge = next(row for row in report["actions"] if row["action"] == "merge_decision")
    assert merge["permission_checked"] is True
    assert merge["required_permission"] == "approve"


def test_regression_operator_role_assignment_enforcement():
    current = get_current_organization()
    assign_role(user_id="operator-user", role="operator", org_id=current.get("org_id"))
    govern = evaluate_access_request(
        role="operator",
        permission="govern",
        requester_org_id=str(current.get("org_id")),
    )
    assert govern["allowed"] is False


def test_authority_flags():
    assert AUTHORIZATION_AUTHORITY_FIX_302 is False
    assert AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302 is False


def test_chat_route():
    turn = resolve_chat_turn("show authorization report", session_id="mc-iah-chat")
    assert turn.intent == "mission_control_identity_access_hardening"
    assert (turn.meta or {}).get("route_id") == IDENTITY_ACCESS_HARDENING_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/identity-access-hardening",
        params={"session_id": "mc-iah-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["authorization_authority"] is False
    assert body["identity_access_hardening"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/identity-access-hardening/record",
        json={
            "session_id": "mc-iah-api",
            "kind": "authorization_note",
            "content": "Review operator membership before granting reviewer role",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True
